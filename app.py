import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

st.set_page_config(page_title="Bezlepkový Skener", page_icon="🌾")
st.title("🌾 Inteligentný Skener")

# 1. Funkcia na preklad technických tagov
def clean_tags(text):
    if not text:
        return "Neuvedené"
    preklady = {
        "en:gluten": "Lepok", "en:wheat": "Pšenica", "en:milk": "Mlieko",
        "en:eggs": "Vajcia", "en:nuts": "Orechy", "en:soybeans": "Sója",
        "en:lupin": "Lupina", "en:peanuts": "Arašidy", "en:none": "Žiadne"
    }
    vystup = text
    for kod, nazov in preklady.items():
        vystup = vystup.replace(kod, nazov)
    return vystup.replace("en:", "")

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
        
        # --- VYLEPŠENÝ BLOK SKENOVANIA ---
        # 1. Skúsime previesť na čiernobielu (vysoký kontrast pre pyzbar)
        img_gray = img.convert('L')
        detected_barcodes = decode(img_gray)
        
        # 2. Ak sa nepodarilo v čiernobielej, skúsime pôvodnú fotku
        if not detected_barcodes:
            detected_barcodes = decode(img)
            
        if detected_barcodes:
            ean = detected_barcodes[0].data.decode('utf-8').strip()
        else:
            st.error("Kód sa nepodarilo prečítať. Skúste kód vyrovnať alebo zlepšiť svetlo.")

with tab2:
    manual_ean = st.text_input("Zadajte kód ručne:")
    if manual_ean: 
        ean = manual_ean.strip()

# --- HLAVNÁ LOGIKA ---
if ean:
    st.divider()
    
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.info(f"**Výrobca:** {product['producer']} | **Status:** {product['note']}")
    
    else:
        with st.spinner('Hľadám v globálnej databáze...'):
            headers = {
                "User-Agent": "BezlepkovySkenerSK - WebApp - Version 1.4"
            }
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    res = response.json()
                    
                    if res.get("status") == 1:
                        prod = res.get("product", {})
                        
                        # --- 1. ZOBRAZENIE FOTOGRAFIE ---
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            img_url = prod.get('image_url')
                            if img_url:
                                st.image(img_url, use_container_width=True)
                            else:
                                st.info("Bez fotky")
                        
                        with col2:
                            name = prod.get('product_name') or prod.get('product_name_en') or "Neznámy produkt"
                            st.subheader(name)
                            
                            labels = prod.get('labels_tags', [])
                            if any('gluten-free' in l or 'crossed-grain' in l for l in labels):
                                st.success("✅ **Certifikovaný bezlepkový**")
                            if any('bio' in l or 'organic' in l for l in labels):
                                st.write("🍃 **BIO / Organic certifikát**")

                        # --- 2. ANALÝZA ZLOŽENIA ---
                        ingr_raw = prod.get("ingredients_text_sk") or prod.get("ingredients_text_cs") or prod.get("ingredients_text") or ""
                        allergens_raw = prod.get("allergens") or ", ".join(prod.get("allergens_hierarchy", [])) or ""
                        traces_raw = prod.get("traces") or ", ".join(prod.get("traces_hierarchy", [])) or ""
                        
                        zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "wheat", "barley", "rye", "oat", "spelt"]
                        
                        found_ingr = [s for s in zakazane if s in ingr_raw.lower() or s in allergens_raw.lower()]
                        found_traces = [s for s in zakazane if s in traces_raw.lower()]

                        if found_ingr:
                            st.error(f"### ❌ OBSAHUJE LEPOK\nZistené: {', '.join(set(found_ingr))}")
                        elif found_traces:
                            st.warning(f"### ⚠️ MÔŽE OBSAHOVAŤ LEPOK (Stopy)\nZistené: {', '.join(set(found_traces))}")
                        else:
                            st.success("### ✅ VYZERÁ TO BEZPEČNE")

                        # --- Diéty ---
                        analysis = prod.get('ingredients_analysis_tags', [])
                        if 'en:vegan' in analysis:
                            st.caption("🌱 Vhodné pre vegánov")
                        elif 'en:vegetarian' in analysis:
                            st.caption("🥚 Vhodné pre vegetariánov")

                        st.markdown("---")
                        search_term = prod.get('brands', name).split(',')[0] # Vezmeme značku alebo názov
                        rasff_url = f"https://webgate.ec.europa.eu/rasff-window/screen/search?searchQueries={search_term}&notifStatus=PUBLISHED"
                        
                        st.write("🛡️ **Bezpečnostná kontrola:**")
                        st.link_button(f"Overiť {search_term} v databáze stiahnutých výrobkov (RASFF)", rasff_url)
                        st.caption("Poznámka: Po kliknutí hľadajte záznamy s rizikom 'Allergens' (Gluten).")

                        with st.expander("🔍 Detailné údaje"):
                            st.write(f"**Alergény:** {clean_tags(allergens_raw)}")
                            st.write(f"**Stopy:** {clean_tags(traces_raw)}")
                            if labels:
                                st.write(f"**Všetky štítky:** {', '.join(labels).replace('en:', '')}")
                    else:
                        st.error(f"Produkt s EAN {ean} sa v databáze nenašiel.")
                else:
                    st.error(f"Server vrátil chybu: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Neočakávaná chyba: {e}")

st.divider()
st.caption("Dáta: MZ SR & Open Food Facts")
