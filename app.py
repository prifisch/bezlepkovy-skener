import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

# 1. Konfigurácia stránky pre mobil (Optimalizované pre Pixel 8a)
st.set_page_config(
    page_title="Bezlepkový Skener", 
    page_icon="🌾",
    layout="centered"
)

# 2. Vylepšené CSS pre moderný mobilný vzhľad
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .block-container { padding: 1rem 0.5rem !important; }

    /* Štýlovanie kariet (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; background-color: #f0f2f6; padding: 5px; border-radius: 15px; width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3.5rem; flex-grow: 1; border-radius: 10px !important;
        background-color: transparent; border: none !important; text-align: center;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important; box-shadow: 0px 2px 5px rgba(0,0,0,0.1); font-weight: bold;
    }

    /* Vizuálny rámik pre kameru */
    [data-testid="stCameraInput"] {
        border: 3px solid #007bff; border-radius: 20px; overflow: hidden;
    }

    /* Tlačidlá */
    div.stButton > button {
        width: 100%; border-radius: 15px !important; background-color: #007bff !important;
        color: white !important; font-weight: 600; height: 3.5rem;
    }
    
    /* Štýlovanie výslednej karty produktu */
    .prod-card {
        background-color: white;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 3. Pomocné funkcie
def clean_tags(text):
    if not text: return "Neuvedené"
    preklady = {
        "en:gluten": "Lepok", "en:wheat": "Pšenica", "en:milk": "Mlieko",
        "en:eggs": "Vajcia", "en:nuts": "Orechy", "en:soybeans": "Sója",
        "en:lupin": "Lupina", "en:peanuts": "Arašidy", "en:none": "Žiadne"
    }
    vystup = text
    for kod, nazov in preklady.items():
        vystup = vystup.replace(kod, nazov)
    return vystup.replace("en:", "")

def load_local_db():
    path = "data/kategorizacia.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

local_db = load_local_db()

# --- LOGIKA APLIKÁCIE ---
st.title("🌾 Bezlepkový Skener")

ean = None
tab1, tab2 = st.tabs(["🔍 SKENOVAŤ", "⌨️ RUČNE"])

with tab1:
    st.info("📸 **Namierte na kód**")
    img_file = st.camera_input("Skenovanie", label_visibility="collapsed")
    if img_file:
        img = Image.open(img_file)
        img_gray = img.convert('L')
        detected_barcodes = decode(img_gray) or decode(img)
        if detected_barcodes:
            ean = detected_barcodes[0].data.decode('utf-8').strip()
        else:
            st.error("Kód nečitateľný. Skúste iný uhol.")

with tab2:
    manual_ean = st.text_input("Zadajte EAN kód:")
    if manual_ean: ean = manual_ean.strip()

# --- SPRACOVANIE A ZOBRAZENIE VÝSLEDKOV ---
if ean:
    st.divider()
    
    prod_info = None
    source = None

    # 1. Hľadanie dát (Lokálna DB -> Open Food Facts)
    if ean in local_db:
        local_prod = local_db[ean]
        prod_info = {
            "name": local_prod['name'],
            "brand": local_prod['producer'],
            "desc": local_prod.get('note', 'Overený bezlepkový produkt (MZ SR)'),
            "img": None
        }
        source = "local"
    else:
        headers = {"User-Agent": "BezlepkovySkenerSK - Pixel8a-View"}
        try:
            response = requests.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json", headers=headers, timeout=10)
            if response.status_code == 200:
                res = response.json()
                if res.get("status") == 1:
                    p = res.get("product", {})
                    prod_info = {
                        "name": p.get('product_name') or p.get('product_name_en') or "Neznámy produkt",
                        "brand": p.get('brands', 'Neznáma značka').split(',')[0],
                        "desc": f"Kategória: {p.get('categories', 'Potraviny').split(',')[0]}",
                        "img": p.get('image_url'),
                        "raw": p
                    }
                    source = "off"
        except: pass

    # 2. Vizualizácia výsledku (Nové rozloženie)
    if prod_info:
        # Horná sekcia: Thumbnail vľavo, Text vpravo
        col_img, col_txt = st.columns([1, 2])
        
        with col_img:
            if prod_info["img"]:
                st.image(prod_info["img"], use_container_width=True)
            else:
                st.markdown("🖼️\n**Bez fotky**")
        
        with col_txt:
            st.markdown(f"### **{prod_info['name']}**")
            st.write(f"**{prod_info['brand']}**")
            st.caption(prod_info['desc'])

        st.markdown("---")

        # STREDNÁ SEKCIA: Semafor (Výsledná hláška)
        if source == "local":
            st.success("🟢 **OVERENÝ BEZLEPKOVÝ PRODUKT**")
            st.balloons()
        else:
            p = prod_info["raw"]
            ingr = (p.get("ingredients_text_sk") or p.get("ingredients_text") or "").lower()
            labels = p.get('labels_tags', [])
            zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "wheat", "barley", "rye", "oat", "spelt"]
            
            found = [s for s in zakazane if s in ingr]
            is_certified = any('gluten-free' in l or 'crossed-grain' in l for l in labels)

            if found:
                st.error(f"🔴 **OBSAHUJE LEPOK**\n(Zistené: {', '.join(set(found))})")
            elif is_certified:
                st.success("🟢 **CERTIFIKOVANÝ BEZLEPKOVÝ PRODUKT**")
            else:
                st.warning("🟡 **NEOVERENÉ / MOŽNÉ STOPY**\nSkontrolujte obal výrobku.")

        # DOLNÁ SEKCIA: Detailné informácie (Expander)
        with st.expander("🔍 Detailné informácie o zložení"):
            if source == "off":
                p = prod_info["raw"]
                st.write(f"**Alergény:** {clean_tags(p.get('allergens', 'Neuvedené'))}")
                st.write(f"**Stopy:** {clean_tags(p.get('traces', 'Neuvedené'))}")
                
                # Pridanie aditív (E-čka)
                additives = p.get('additives_tags', [])
                if additives:
                    clean_additives = [a.replace('en:', '').upper() for a in additives]
                    st.write(f"**Aditíva (E-čka):** {', '.join(clean_additives)}")
                else:
                    st.write("**Aditíva:** Neuvádzajú sa žiadne aditíva.")
            else:
                st.write("Produkt je registrovaný v oficiálnom zozname kategorizovaných dietetických potravín SR.")

        # RASFF Tlačidlo (Bezpečnostná kontrola)
        if prod_info["brand"]:
            rasff_url = f"https://webgate.ec.europa.eu/rasff-window/screen/search?searchQueries={prod_info['brand']}"
            st.link_button(f"🚩 Overiť bezpečnosť značky {prod_info['brand']}", rasff_url)

    else:
        st.warning("Produkt sa nenašiel v dostupných databázach.")

st.divider()
st.caption("Dáta: MZ SR & [Open Food Facts](https://world.openfoodfacts.org)")
