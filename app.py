import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

# 1. Konfigurácia stránky
st.set_page_config(
    page_title="Bezlepkový Skener", 
    page_icon="🌾",
    layout="centered"
)

# 2. Vylepšené CSS pre mobil (Pixel 8a)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .block-container { padding: 1rem 0.5rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #f0f2f6; padding: 5px; border-radius: 15px; width: 100%; }
    .stTabs [data-baseweb="tab"] { height: 3.5rem; flex-grow: 1; border-radius: 10px !important; background-color: transparent; border: none !important; }
    .stTabs [aria-selected="true"] { background-color: #ffffff !important; box-shadow: 0px 2px 5px rgba(0,0,0,0.1); font-weight: bold; }
    [data-testid="stCameraInput"] { border: 3px solid #007bff; border-radius: 20px; overflow: hidden; }
    div.stButton > button { width: 100%; border-radius: 15px !important; background-color: #007bff !important; color: white !important; font-weight: 600; height: 3.5rem; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# 3. MAPA ALERGÉNOV A TAGOV
ALERGENY_MAPA = {
    "Lepok": ["lepok", "pšenič", "jačmeň", "raž", "ovos", "slad", "pohánka", "špald", "gluten", "wheat", "barley", "rye", "oat"],
    "Kôrovce": ["kôrovce", "krevety", "homár", "rak", "krab", "crustaceans", "shrimp", "prawns"],
    "Vajcia": ["vajcia", "vaječ", "žĺtok", "bielok", "egg", "albumin"],
    "Ryby": ["ryby", "rybac", "fish", "tuniak", "losos", "treska"],
    "Arašidy": ["arašidy", "arašid", "arašidov", "peanuts"],
    "Sója": ["sója", "sójov", "lecitín", "soy", "soya"],
    "Mlieko": ["mlieko", "mlieč", "laktóz", "srvátka", "tvaroh", "smotana", "maslo", "milk", "lactose", "whey"],
    "Orechy": ["orechy", "mandle", "lieskov", "vlašs", "kešu", "pekan", "para", "pistáci", "makadam", "nuts", "almonds", "hazelnut", "cashew"],
    "Zeler": ["zeler", "celery"],
    "Horčica": ["horčica", "mustard"],
    "Sézam": ["sézam", "sesame"],
    "SO2": ["oxid siričitý", "siričitan", "so2", "sulphites", "sulfites"],
    "Vlčí bôb": ["vlčí bôb", "lupina", "lupin"],
    "Mäkkýše": ["mäkkýše", "ustrice", "mušle", "chobotnic", "molluscs", "mussels"]
}

# Mapovanie OFF tagov na slovenské názvy
OFF_TAGS_MAPPING = {
    "gluten": "Lepok", "milk": "Mlieko", "eggs": "Vajcia", "nuts": "Orechy",
    "peanuts": "Arašidy", "soybeans": "Sója", "fish": "Ryby", "crustaceans": "Kôrovce",
    "celery": "Zeler", "mustard": "Horčica", "sesame-seeds": "Sézam", 
    "sulphur-dioxide-and-sulphites": "SO2", "lupin": "Vlčí bôb", "molluscs": "Mäkkýše"
}

# 4. POMOCNÉ FUNKCIE
def analyzuj_vsetko(product_data):
    najdene = set()
    stopy = set()

    # VRSTVA 1: Štruktúrované tagy (najpresnejšie)
    for tag in product_data.get('allergens_tags', []):
        name = tag.replace('en:', '').lower()
        if name in OFF_TAGS_MAPPING: najdene.add(OFF_TAGS_MAPPING[name])

    for tag in product_data.get('traces_tags', []):
        name = tag.replace('en:', '').lower()
        if name in OFF_TAGS_MAPPING: stopy.add(OFF_TAGS_MAPPING[name])

    # VRSTVA 2: Textová analýza (SK, CS, EN)
    texty = " ".join([
        product_data.get("ingredients_text_sk", ""),
        product_data.get("ingredients_text_cs", ""),
        product_data.get("ingredients_text_en", ""),
        product_data.get("ingredients_text", "")
    ]).lower()

    text_stopy = (product_data.get("traces", "")).lower()

    for alergen, kluce in ALERGENY_MAPA.items():
        if any(k in texty for k in kluce):
            najdene.add(alergen)
        elif any(k in text_stopy for k in kluce):
            stopy.add(alergen)

    # Čistenie: Ak je v hlavnom, nemôže byť len v stopách
    stopy = stopy - najdene
    return list(najdene), list(stopy)

def load_local_db():
    path = "data/kategorizacia.json"
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
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
        detected_barcodes = decode(img.convert('L')) or decode(img)
        if detected_barcodes:
            ean = detected_barcodes[0].data.decode('utf-8').strip()
        else:
            st.error("Kód nečitateľný.")

with tab2:
    manual_ean = st.text_input("Zadajte EAN kód:")
    if manual_ean: ean = manual_ean.strip()

# --- SPRACOVANIE VÝSLEDKOV ---
if ean:
    st.divider()
    prod_info = None
    source = None

    if ean in local_db:
        lp = local_db[ean]
        prod_info = {"name": lp['name'], "brand": lp['producer'], "desc": "Overené MZ SR", "img": None}
        source = "local"
    else:
        try:
            res = requests.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json", timeout=10).json()
            if res.get("status") == 1:
                p = res.get("product", {})
                prod_info = {
                    "name": p.get('product_name') or "Neznámy produkt",
                    "brand": p.get('brands', 'Neznáma značka').split(',')[0],
                    "desc": p.get('categories', 'Potraviny').split(',')[0],
                    "img": p.get('image_url'),
                    "raw": p
                }
                source = "off"
        except: st.error("Chyba databázy.")

    if prod_info:
        c1, c2 = st.columns([1, 2])
        with c1:
            if prod_info["img"]: st.image(prod_info["img"], use_container_width=True)
            else: st.markdown("🖼️\n**Bez fotky**")
        with c2:
            st.markdown(f"### **{prod_info['name']}**")
            st.write(f"**{prod_info['brand']}**")
            st.caption(prod_info['desc'])

        st.markdown("---")

        najdene, stopy = [], []
        if source == "local":
            st.success("🟢 **OVERENÝ BEZLEPKOVÝ PRODUKT**")
        else:
            najdene, stopy = analyzuj_vsetko(prod_info["raw"])
            is_gf = any('gluten-free' in l for l in prod_info["raw"].get('labels_tags', []))

            if najdene:
                st.error(f"🔴 **OBSAHUJE ALERGÉNY:** {', '.join(najdene)}")
            elif stopy:
                st.warning(f"🟡 **MOŽNÉ STOPY:** {', '.join(stopy)}")
            else:
                st.success("🟢 **VYZERÁ TO BEZPEČNE**")
            if is_gf: st.info("🛡️ Produkt má certifikát 'Gluten-free'")

        with st.expander("🔍 Kompletná analýza 14 alergénov"):
            for al in ALERGENY_MAPA.keys():
                icon = "❌" if al in najdene else ("⚠️" if al in stopy else "✅")
                st.write(f"{icon} **{al}**")
            
            if source == "off":
                adds = prod_info["raw"].get('additives_tags', [])
                if adds: st.write(f"**Aditíva (E-čka):** {', '.join([a.replace('en:', '').upper() for a in adds])}")

        st.link_button(f"🚩 Overiť bezpečnosť {prod_info['brand']}", f"https://webgate.ec.europa.eu/rasff-window/screen/search?searchQueries={prod_info['brand']}")
    else:
        st.warning("Produkt sa nenašiel.")

st.divider()
st.caption("Dáta: MZ SR & Open Food Facts")
