import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

st.set_page_config(page_title="Bezlepkový Skener", page_icon="🌾")
st.title("🌾 Inteligentný Skener")

# 1. Načítanie lokálnej databázy (kategorizacia.json)
def load_local_db():
    path = "data/kategorizacia.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

local_db = load_local_db()

# --- LOGIKA ZÍSKANIA EAN KÓDU ---
ean = None

# Rozdelenie na karty pre lepšie ovládanie
tab1, tab2 = st.tabs(["📸 Skenovať", "⌨️ Zadať kód"])

with tab1:
    img_file = st.camera_input("Odfoťte čiarový kód")
    if img_file:
        img = Image.open(img_file)
        detected_barcodes = decode(img)
        if detected_barcodes:
            ean = detected_barcodes[0].data.decode('utf-8').strip()
            st.success(f"Naskenovaný kód: {ean}")
        else:
            st.error("Kód na fotke sa nepodarilo prečítať. Skúste kód vycentrovať a zaostriť.")

with tab2:
    manual_ean = st.text_input("Alebo zadajte kód ručne:")
    if manual_ean:
        ean = manual_ean.strip()

# --- HLAVNÁ LOGIKA VYHĽADÁVANIA ---
# Spustí sa len ak máme EAN (z fotky alebo ručne)
if ean:
    st.divider()
    
    # KROK A: Kontrola v tvojej vlastnej databáze
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.write(f"**Výrobca:** {product['producer']}")
        st.info(f"ℹ️ **Status:** {product['note']}")
    
    # KROK B: Ak nie je u teba, hľadaj na internete (Open Food Facts)
    else:
        with st.spinner('Hľadám v globálnej databáze...'):
            # User-Agent je dôležitý pre chybu 403
            headers = {
                "User-Agent": "BezlepkovySkenerSK - WebApp - Version 1.0 (Kontakt: tvoj@email.com)"
            }
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    res_data = response.json()
                    
                    if res_data.get("status") == 1:
                        prod = res_data.get("product", {})
                        name = prod.get('product_name') or prod.get('product_name_en') or "Neznámy produkt"
                        
                        st.warning(f"### 📦 {name}")
                        st.write("Produkt nie je v oficiálnom zozname (kategorizácii), ale našiel sa v Open Food Facts.")
                        
                        # Získanie zloženia v dostupných jazykoch
                        ingr = prod.get("ingredients_text_sk") or \
                               prod.get("ingredients_text_cs") or \
                               prod.get("ingredients_text_en") or "Zloženie nie je k dispozícii."
                        
                        with st.expander("Zobraziť zloženie"):
                            st.write(ingr)
                            
                        # Jednoduchá kontrola kľúčových slov na lepok
                        zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad"]
                        naugat = [slovo for slovo in zakazane if slovo in ingr.lower()]
                        
                        if naugat:
                            st.error(f"⚠️ **POZOR:** V zložení sa spomínajú podozrivé zložky: {', '.join(naugat)}")
                        else:
                            st.info("V zložení neboli nájdené základné slovenské výrazy pre lepok. Vždy si však prečítajte obal!")
                    
                    else:
                        st.error(f"Produkt s kódom {ean} sa nenašiel v žiadnej databáze.")
                
                elif response.status_code == 403:
                    st.error("Chyba 403: Prístup zamietnutý. Skúste neskôr.")
                elif response.status_code == 429:
                    st.error("Chyba 429: Príliš veľa požiadaviek. Server nás na chvíľu zablokoval.")
                else:
                    st.error(f"Server vrátil chybu: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Chyba pri pripájaní: {e}")

st.divider()
st.caption("Projekt: Bezlepkový Skener | Dáta: MZ SR & Open Food Facts")
