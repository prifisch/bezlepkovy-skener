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
    
    # KROK A: Kontrola v tvojej vlastnej databáze (MZ SR)
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
                "User-Agent": "BezlepkovySkenerSK - WebApp - Version 1.1 (Kontakt: tvoj@email.com)"
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

                        # --- ROZŠÍRENÁ KONTROLA LEPKU (Zloženie + Alergény + Stopy) ---
                        
                        # Získanie textov (všetko na malé písmená pre jednoduchšie hľadanie)
                        ingr = (prod.get("ingredients_text_sk") or prod.get("ingredients_text_cs") or prod.get("ingredients_text_en") or "").lower()
                        allergens = (prod.get("allergens") or "").lower()
                        traces = (prod.get("traces") or "").lower()
                        
                        # Zoznam rizikových slov (Slovenčina + Angličtina kvôli medzinárodným tagom)
                        zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "wheat", "barley", "rye", "oat", "spelt", "špalda"]
                        
                        # Kontrola prítomnosti v jednotlivých poliach
                        naslo_v_zlozeni = [s for s in zakazane if s in ingr]
                        naslo_v_alergenoch = [s for s in zakazane if s in allergens]
                        naslo_v_stopach = [s for s in zakazane if s in traces]

                        # Vyhodnotenie výsledku
                        if naslo_v_zlozeni or naslo_v_alergenoch:
                            st.error("### ❌ OBSAHUJE LEPOK")
                            vsetky_zlozky = set(naslo_v_zlozeni + naslo_v_alergenoch)
                            st.write(f"**Nájdené rizikové zložky:** {', '.join(vsetky_zlozky)}")
                        
                        elif naslo_v_stopach:
                            st.warning("### ⚠️ MÔŽE OBSAHOVAŤ LEPOK")
                            st.write(f"**Upozornenie na stopy:** {', '.join(set(naslo_v_stopach))}")
                            st.info("Tento produkt nemá lepok v priamom zložení, ale výrobca varuje pred možnou kontamináciou.")
                        
                        else:
                            st.success("### ✅ NEBOLI NÁJDENÉ ALERGÉNY")
                            st.write("V zložení, alergénoch ani stopách neboli nájdené bežné obilniny obsahujúce lepok.")

                        # Zobrazenie surových dát pre kontrolu
                        with st.expander("🔍 Zobraziť detailné texty z databázy"):
                            if ingr: st.write(f"**Zloženie:** {ingr}")
                            if allergens: st.write(f"**Alergény:** {allergens}")
                            if traces: st.write(f"**Stopy (Môže obsahovať):** {traces}")
                    
                    else:
                        st.error(f"Produkt s kódom {ean} sa v databáze nenašiel.")
                
                elif response.status_code == 403:
                    st.error("Chyba 403: Prístup zamietnutý serverom. Skúste neskôr.")
                elif response.status_code == 429:
                    st.error("Chyba 429: Príliš veľa požiadaviek. Server má pauzu.")
                else:
                    st.error(f"Server vrátil chybu: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Chyba pri pripájaní: {e}")

st.divider()
st.caption("Projekt: Bezlepkový Skener | Dáta: MZ SR & Open Food Facts")
