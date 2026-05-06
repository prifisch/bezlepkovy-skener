import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

st.set_page_config(page_title="Bezlepkový Skener", page_icon="🌾")
st.title("🌾 Inteligentný Skener")

# 1. Načítanie lokálnej databázy
def load_local_db():
    path = "data/kategorizacia.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

local_db = load_local_db()

# --- LOGIKA ZÍSKANIA EAN KÓDU ---
ean = None

# Tabuľky pre lepšiu prehľadnosť
tab1, tab2 = st.tabs(["📸 Skenovať", "⌨️ Zadať kód"])

with tab1:
    img_file = st.camera_input("Odfoťte čiarový kód produktu")
    if img_file:
        img = Image.open(img_file)
        detected_barcodes = decode(img)
        if detected_barcodes:
            ean = detected_barcodes[0].data.decode('utf-8').strip()
            st.success(f"Naskenovaný kód: {ean}")
        else:
            st.error("Kód nebol rozpoznaný. Skúste lepšie svetlo alebo inú vzdialenosť.")

with tab2:
    manual_ean = st.text_input("Zadajte EAN kód ručne:")
    if manual_ean:
        ean = manual_ean.strip()

# --- LOGIKA VYHĽADÁVANIA ---
if ean:
    # Najprv skúsime lokálnu databázu (MZ SR)
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.write(f"**Výrobca:** {product['producer']}")
        st.info(f"ℹ️ **Status:** {product['note']}")
    
    # Ak nie je v lokálnej, ideme na Open Food Facts
    else:
        with st.spinner('Hľadám v globálnej databáze...'):
            # HLAVIČKA (HEADERS) - rieši chybu 403
            headers = {
                "User-Agent": "BezlepkovySkenerSK - WebApp - Version 0.2 (Kontakt: tvoj@email.com)"
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
                        st.write("Produkt nie je v oficiálnom zozname, ale bol nájdený v Open Food Facts.")
                        
                        # Hľadanie zloženia v rôznych jazykoch
                        ingredients = prod.get("ingredients_text_sk") or \
                                      prod.get("ingredients_text_cs") or \
                                      prod.get("ingredients_text_en") or "Zloženie nie je k dispozícii."
                        
                        with st.expander("Zobraziť zloženie"):
                            st.write(ingredients)
                            
                        # Jednoduchá automatická kontrola kľúčových slov
                        forbidden = ["pšenica", "pšeničný", "jačmeň", "jačmenný", "raž", "ovos", "lepok", "gluten"]
                        found_bad_stuff = [word for word in forbidden if word in ingredients.lower()]
                        
                        if found_bad_stuff:
                            st.error(f"⚠️ Pozor! V zložení sa spomína: {', '.join(found_bad_stuff)}")
                        else:
                            st.info("💡 Tip: V texte zloženia neboli nájdené základné slovenské výrazy pre lepok, ale vždy si ho prečítajte celé.")
                            
                    else:
                        st.error(f"Produkt s kódom {ean} sa v databáze nenašiel.")
                elif response.status_code == 403:
                    st.error("Chyba 403: Prístup zamietnutý. Server nás blokuje. Skúste to o chvíľu.")
                else:
                    st.error(f"Server vrátil chybu: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Detailná chyba spojenia: {e}")

# Päta aplikácie
st.divider()
st.caption("Dáta sú čerpané z verejných zdrojov. Vždy si skontrolujte fyzický obal výrobku.")
