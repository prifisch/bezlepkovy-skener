import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

# 1. Konfigurácia stránky pre mobil
st.set_page_config(
    page_title="Bezlepkový Skener", 
    page_icon="🌾",
    layout="centered"
)

# 2. Vylepšené CSS pre Pixel 8a (UX a dizajn)
st.markdown("""
    <style>
    /* Hlavný kontajner a pozadie */
    .stApp {
        background-color: #f8f9fa;
    }
    .block-container {
        padding: 1rem 0.5rem !important;
    }

    /* Štýlovanie kariet (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f0f2f6;
        padding: 5px;
        border-radius: 15px;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3.5rem;
        flex-grow: 1;
        border-radius: 10px !important;
        background-color: transparent;
        transition: all 0.3s;
        border: none !important;
        text-align: center;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        font-weight: bold;
    }

    /* Vizuálny rámik pre kameru */
    [data-testid="stCameraInput"] {
        border: 3px solid #007bff;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0px 0px 15px rgba(0,123,255,0.2);
    }

    /* Karty pre výsledky a tlačidlá */
    .stAlert {
        border-radius: 15px;
        font-size: 1rem !important;
    }
    
    div.stButton > button {
        width: 100%;
        border-radius: 15px !important;
        background-color: #007bff !important;
        color: white !important;
        border: none;
        padding: 0.8rem;
        font-weight: 600;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        height: 3.5rem;
    }
    
    div.stButton > button:active {
        transform: scale(0.98);
    }

    /* Skrytie zbytočných Streamlit prvkov */
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
    st.info("📸 **Namierte na kód** (ak vidíte seba, prepnite kameru ikonou 🔄)")
    img_file = st.camera_input("Skenovanie", label_visibility="collapsed")
    if img_file:
        img = Image.open(img_file)
        # Dvojfázové skenovanie (čiernobiele + farebné)
        img_gray = img.convert('L')
        detected_barcodes = decode(img_gray) or decode(img)
            
        if detected_barcodes:
            ean = detected_barcodes[0].data.decode('utf-8').strip()
        else:
            st.error("Kód nečitateľný. Skúste iný uhol alebo lepšie svetlo.")

with tab2:
    manual_ean = st.text_input("Zadajte EAN kód ručne:")
    if manual_ean: 
        ean = manual_ean.strip()

# --- SPRACOVANIE VÝSLEDKOV ---
if ean:
    st.divider()
    
    # 1. KONTROLA V LOKÁLNOM ZOZNAME (Kategorizácia)
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.info(f"**Výrobca:** {product['producer']}\n\n**Status:** {product['note']}")
    
    # 2. KONTROLA V GLOBÁLNEJ DATABÁZE
    else:
        with st.spinner('Hľadám v databáze...'):
            headers = {"User-Agent": "BezlepkovySkenerSK - Pixel8a-View"}
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    res = response.json()
                    if res.get("status") == 1:
                        prod = res.get("product", {})
                        
                        # Obrázok produktu
                        img_url = prod.get('image_url')
                        if img_url:
                            st.image(img_url, use_container_width=True)
                        
                        name = prod.get('product_name') or prod.get('product_name_en') or "Neznámy produkt"
                        st.subheader(name)
                        
                        # Certifikáty
                        labels = prod.get('labels_tags', [])
                        if any('gluten-free' in l or 'crossed-grain' in l for l in labels):
                            st.success("🛡️ **Oficiálne bezlepkový certifikát**")

                        # Analýza zloženia
                        ingr_raw = prod.get("ingredients_text_sk") or prod.get("ingredients_text_cs") or prod.get("ingredients_text") or ""
                        zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "wheat", "barley", "rye", "oat", "spelt"]
                        
                        found = [s for s in zakazane if s in ingr_raw.lower()]

                        if found:
                            st.error(f"### ❌ OBSAHUJE LEPOK\nZistené: {', '.join(set(found))}")
                        else:
                            st.success("### ✅ VYZERÁ TO BEZPEČNE")

                        # RASFF Tlačidlo
                        brand = prod.get('brands', 'Produkt').split(',')[0]
                        rasff_url = f"https://webgate.ec.europa.eu/rasff-window/screen/search?searchQueries={brand}&notifStatus=PUBLISHED"
                        st.link_button(f"🚩 Overiť bezpečnosť značky {brand}", rasff_url)

                        with st.expander("🔍 Podrobné zloženie a alergény"):
                            st.write(f"**Alergény:** {clean_tags(prod.get('allergens', 'Neuvedené'))}")
                            st.write(f"**Stopy:** {clean_tags(prod.get('traces', 'Neuvedené'))}")
                            if labels:
                                st.write(f"**Štítky:** {', '.join(labels).replace('en:', '')}")
                    else:
                        st.warning("Produkt sa v globálnej databáze nenašiel.")
                else:
                    st.error("Chyba spojenia so serverom.")
            except Exception as e:
                st.error("Vyskytla sa chyba pri hľadaní.")

st.divider()
st.caption("Zdroje dát: Zoznam kategorizovaných potravín MZ SR & [Open Food Facts](https://world.openfoodfacts.org)")
