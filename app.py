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
if ean:
    st.divider()
    
    # KROK A: Kontrola v lokálnej databáze (MZ SR)
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.write(f"**Výrobca:** {product['producer']}")
        st.info(f"ℹ️ **Status:** {product['note']}")
    
    # KROK B: Ak nie je u teba, hľadaj v Open Food Facts
    else:
        with st.spinner('Hľadám v globálnej databáze...'):
            headers = {
                "User-Agent": "BezlepkovySkenerSK - WebApp - Version 1.2 (Kontakt: tvoj@email.com)"
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

                        # --- AGRESÍVNE ZÍSKAVANIE DÁT (Hľadáme v akomkoľvek poli) ---
                        
                        # Zloženie: skús prioritné jazyky, potom čokoľvek
                        ingr_raw = prod.get("ingredients_text_sk") or \
                                   prod.get("ingredients_text_cs") or \
                                   prod.get("ingredients_text_en") or \
                                   prod.get("ingredients_text") or ""
                        ingr = ingr_raw.lower()

                        # Alergény: textové pole alebo tagy (hierarchia)
                        allergens_raw = prod.get("allergens") or ", ".join(prod.get("allergens_hierarchy", [])) or ""
                        allergens = allergens_raw.lower()

                        # Stopy (Môže obsahovať): textové pole alebo tagy
                        traces_raw = prod.get("traces") or ", ".join(prod.get("traces_hierarchy", [])) or ""
                        traces = traces_raw.lower()
                        
                        # Rozšírený zoznam zakázaných slov (SK, CS, EN, DE, FR)
                        zakazane = [
                            "pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "špalda", # SK/CS
                            "wheat", "barley", "rye", "oat", "spelt", "malt",                     # EN
                            "weizen", "gerste", "roggen", "hafer", "malz",                        # DE
                            "blé", "orge", "seigle", "avoine"                                     # FR
                        ]
                        
                        # Kontrola prítomnosti
                        naslo_v_zlozeni = [s for s in zakazane if s in ingr]
                        naslo_v_alergenoch = [s for s in zakazane if s in allergens]
                        naslo_v_stopach = [s for s in zakazane if s in traces]

                        # --- VYHODNOTENIE ---
                        if naslo_v_zlozeni or naslo_v_alergenoch:
                            st.error("### ❌ OBSAHUJE LEPOK")
                            rizika = set(naslo_v_zlozeni + naslo_v_alergenoch)
                            st.write(f"**Nájdené zložky:** {', '.join(rizika)}")
                        
                        elif naslo_v_stopach:
                            st.warning("### ⚠️ MÔŽE OBSAHOVAŤ LEPOK")
                            st.write(f"**Zistené stopy:** {', '.join(set(naslo_v_stopach))}")
                            st.info("Produkt nemá lepok v priamom zložení, ale hrozí kontaminácia (stopy).")
                        
                        else:
                            st.success("### ✅ NEBOLI NÁJDENÉ ALERGÉNY")
                            st.write("V dostupných dátach sa nenašiel lepok ani stopy lepku.")

                        # Zobrazenie detailov (aj keď sú v inom jazyku)
                        with st.expander("🔍 Zobraziť detailné texty z databázy"):
                            st.write(f"**Zloženie:** {ingr_raw if ingr_raw else 'Neuvedené'}")
                            st.write(f"**Alergény:** {allergens_raw if allergens_raw else 'Neuvedené'}")
                            st.write(f"**Stopy:** {traces_raw if traces_raw else 'Neuvedené'}")
                    
                    else:
                        st.error(f"Produkt s kódom {ean} sa v databáze nenašiel.")
                
                elif response.status_code == 403:
                    st.error("Chyba 403: Prístup zamietnutý. Skúste to neskôr.")
                elif response.status_code == 429:
                    st.error("Chyba 429: Príliš veľa požiadaviek (Server má pauzu).")
                else:
                    st.error(f"Server vrátil chybu: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Chyba pri pripájaní: {e}")

st.divider()
st.caption("Projekt: Bezlepkový Skener | Dáta: MZ SR & Open Food Facts")
