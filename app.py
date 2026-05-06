import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

st.set_page_config(page_title="Bezlepkový Skener", page_icon="🌾")
st.title("🌾 Inteligentný Skener")

def load_local_db():
    path = "data/kategorizacia.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

local_db = load_local_db()

# --- LOGIKA SKENOVANIA ---
ean = None
img_file = st.camera_input("Odfoťte čiarový kód")

if img_file:
    # Prevod fotky na formát, ktorému rozumie čítačka
    img = Image.open(img_file)
    detected_barcodes = decode(img)
    
    if detected_barcodes:
        ean = detected_barcodes[0].data.decode('utf-8')
        st.success(f"Naskenovaný kód: {ean}")
    else:
        st.error("Nepodarilo sa rozpoznať kód. Skúste kód priblížiť a zaostriť.")

# Alternatívny ručný vstup
manual_ean = st.text_input("Alebo zadajte kód ručne:")
if manual_ean:
    ean = manual_ean

# --- VYHĽADÁVANIE ---
if ean:
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.write(f"**Výrobca:** {product['producer']}")
        st.info(f"ℹ️ {product['note']}")
    else:
        with st.spinner('Hľadám v globálnej databáze...'):
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            try:
                res = requests.get(url).json()
                if res.get("status") == 1:
                    prod = res["product"]
                    st.warning(f"### 📦 {prod.get('product_name', 'Neznámy')}")
                    st.write("Produkt nie je v zozname na predpis. Skontrolujte zloženie nižšie:")
                    st.write(prod.get("ingredients_text_sk") or "Zloženie nie je v SK")
                else:
                    st.error("Produkt sa nenašiel.")
            except:
                st.error("Chyba spojenia.")
