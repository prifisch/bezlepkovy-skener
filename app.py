import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

st.set_page_config(page_title="Bezlepkový Skener", page_icon="🌾")
st.title("🌾 Inteligentný Skener")

# 1. Funkcia na preklad technických tagov z databázy
def clean_tags(text):
    if not text:
        return "Neuvedené"
    
    # Mapa prekladov
    preklady = {
        "en:gluten": "Lepok",
        "en:wheat": "Pšenica",
        "en:milk": "Mlieko",
        "en:eggs": "Vajcia",
        "en:nuts": "Orechy",
        "en:soybeans": "Sója",
        "en:lupin": "Lupina (Vlčí bôb)",
        "en:peanuts": "Arašidy",
        "en:sesame-seeds": "Sezam",
        "en:mustard": "Horčica",
        "en:none": "Žiadne",
        "en:safe": "Bezpečné"
    }
    
    vystup = text
    for kod, nazov in preklady.items():
        vystup = vystup.replace(kod, nazov)
    
    # Odstránenie zvyšných "en:" ak by tam nejaké zostali
    vystup = vystup.replace("en:", "")
    return vystup

# 2. Načítanie lokálnej databázy
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
            st.error("Kód na fotke sa nepodarilo prečítať.")

with tab2:
    manual_ean = st.text_input("Alebo zadajte kód ručne:")
    if manual_ean:
        ean = manual_ean.strip()

# --- HLAVNÁ LOGIKA VYHĽADÁVANIA ---
if ean:
    st.divider()
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.write(f"**Výrobca:** {product['producer']}")
        st.info(f"ℹ️ **Status:** {product['note']}")
    else:
        with st.spinner('Hľadám v globálnej databáze...'):
            headers = {"User-Agent": "BezlepkovySkenerSK - WebApp - Version 1.3"}
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    res_data = response.json()
                    if res_data.get("status") == 1:
                        prod = res_data.get("product", {})
                        name = prod.get('product_name') or prod.get('product_name_en') or "Neznámy produkt"
                        st.warning(f"### 📦 {name}")

                        # Získanie raw dát
                        ingr_raw = prod.get("ingredients_text_sk") or prod.get("ingredients_text_cs") or prod.get("ingredients_text_en") or prod.get("ingredients_text") or ""
                        allergens_raw = prod.get("allergens") or ", ".join(prod.get("allergens_hierarchy", [])) or ""
                        traces_raw = prod.get("traces") or ", ".join(prod.get("traces_hierarchy", [])) or ""
                        
                        # Kontrola zakázaných slov (pred prekladom pre presnosť)
                        zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "špalda", "wheat", "barley", "rye", "oat", "spelt", "malt"]
                        
                        ingr_l = ingr_raw.lower()
                        all_l = allergens_raw.lower()
                        trc_l = traces_raw.lower()

                        naslo_v_zlozeni = [s for s in zakazane if s in ingr_l]
                        naslo_v_alergenoch = [s for s in zakazane if s in all_l]
                        naslo_v_stopach = [s for s in zakazane if s in trc_l]

                        # Vyhodnotenie
                        if naslo_v_zlozeni or naslo_v_alergenoch:
                            st.error("### ❌ OBSAHUJE LEPOK")
                            st.write(f"**Zistené zložky:** {', '.join(set(naslo_v_zlozeni + naslo_v_alergenoch))}")
                        elif naslo_v_stopach:
                            st.warning("### ⚠️ MÔŽE OBSAHOVAŤ LEPOK")
                            st.info("Produkt nemá lepok v zložení, ale hrozí kontaminácia (stopy).")
                        else:
                            st.success("### ✅ NEBOLI NÁJDENÉ ALERGÉNY")

                        # Zobrazenie detailov s PREKLADOM
                        with st.expander("🔍 Zobraziť detailné texty z databázy"):
                            st.write(f"**Zloženie:** {ingr_raw if ingr_raw else 'Neuvedené'}")
                            st.write(f"**Alergény:** {clean_tags(allergens_raw)}")
                            st.write(f"**Stopy:** {clean_tags(traces_raw)}")
                    else:
                        st.error(f"Produkt s kódom {ean} sa v databáze nenašiel.")
                else:
                    st.error(f"Server vrátil chybu: {response.status_code}")
            except Exception as e:
                st.error(f"Chyba pri pripájaní: {e}")

st.divider()
st.caption("Projekt: Bezlepkový Skener | Dáta: MZ SR & Open Food Facts")
