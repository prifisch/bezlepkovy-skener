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
    layout="centered" # Na mobile je lepšie centrované, CSS sa postará o šírku
)

# 2. Vlastné CSS pre Pixel 8a a mobilné zariadenia
st.markdown("""
    <style>
    /* Odstránenie horného paddingu a okrajov */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    /* Zväčšenie tlačidiel pre palce */
    .stButton > button {
        width: 100%;
        height: 3.5rem;
        border-radius: 12px;
        font-size: 1.1rem !important;
        font-weight: bold;
    }
    
    /* Úprava kariet (Tabs) pre mobil */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        width: 100%;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        flex-grow: 1;
        border-radius: 8px 8px 0px 0px;
        text-align: center;
    }

    /* Vylepšenie zobrazenia obrázkov */
    img {
        border-radius: 15px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }

    /* Zväčšenie textu v info boxoch */
    .stAlert {
        font-size: 1rem !important;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌾 Inteligentný Skener")

# --- ZVYŠOK KÓDU (Funkcie) ---

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

ean = None
tab1, tab2 = st.tabs(["📸 Skenovať", "⌨️ Ručne"])

with tab1:
    # Zmenšený text pre inštrukciu, aby nezaberala miesto
    img_file = st.camera_input("Namierte na kód")
    if img_file:
        img = Image.open(img_file)
        img_gray = img.convert('L')
        detected_barcodes = decode(img_gray) or decode(img)
            
        if detected_barcodes:
            ean = detected_barcodes[0].data.decode('utf-8').strip()
        else:
            st.error("Kód nečitateľný. Skúste iný uhol.")

with tab2:
    manual_ean = st.text_input("EAN kód:")
    if manual_ean: ean = manual_ean.strip()

if ean:
    st.divider()
    
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.info(f"**Výrobca:** {product['producer']}\n\n**Status:** {product['note']}")
    
    else:
        with st.spinner('Hľadám...'):
            headers = {"User-Agent": "BezlepkovySkenerSK - MobileView"}
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    res = response.json()
                    if res.get("status") == 1:
                        prod = res.get("product", {})
                        
                        # Mobilné rozloženie: Obrázok hore, pod ním info
                        img_url = prod.get('image_url')
                        if img_url:
                            st.image(img_url, use_container_width=True)
                        
                        name = prod.get('product_name') or prod.get('product_name_en') or "Neznámy produkt"
                        st.subheader(name)
                        
                        # Zobrazenie certifikátov
                        labels = prod.get('labels_tags', [])
                        if any('gluten-free' in l or 'crossed-grain' in l for l in labels):
                            st.success("🛡️ **Oficiálne bezlepkový certifikát**")

                        # Analýza zloženia
                        ingr_raw = prod.get("ingredients_text_sk") or prod.get("ingredients_text") or ""
                        zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "wheat", "barley", "rye", "oat", "spelt"]
                        
                        found = [s for s in zakazane if s in ingr_raw.lower()]

                        if found:
                            st.error(f"### ❌ OBSAHUJE LEPOK\n({', '.join(set(found))})")
                        else:
                            st.success("### ✅ VYZERÁ TO BEZPEČNE")

                        # RASFF Tlačidlo - široké pre mobil
                        brand = prod.get('brands', 'Produkt').split(',')[0]
                        rasff_url = f"https://webgate.ec.europa.eu/rasff-window/screen/search?searchQueries={brand}&notifStatus=PUBLISHED"
                        st.link_button(f"🚩 Overiť bezpečnosť {brand}", rasff_url)

                        with st.expander("🔍 Podrobnosti o zložení"):
                            st.write(f"**Alergény:** {clean_tags(prod.get('allergens', 'Neuvedené'))}")
                            st.write(f"**Stopy:** {clean_tags(prod.get('traces', 'Neuvedené'))}")
                    else:
                        st.error("Produkt sa nenašiel.")
            except Exception as e:
                st.error(f"Chyba siete.")

st.divider()
st.caption("Dáta: MZ SR & Open Food Facts")
