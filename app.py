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
            try: return json.load(f)
            except: return {}
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
        else:
            st.error("Kód sa nepodarilo prečítať.")

with tab2:
    manual_ean = st.text_input("Zadajte kód ručne:")
    if manual_ean: ean = manual_ean.strip()

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
            # Definujeme hlavičky, aby nás server neodmietol
            headers = {
                "User-Agent": "BezlepkovySkenerSK - WebApp - Version 1.3 (Kontakt: tvoj@email.com)"
            }
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                # Skontrolujeme, či server vrátil úspešný kód (200)
                if response.status_code == 200:
                    try:
                        res = response.json()
                        if res.get("status") == 1:
                            prod = res.get("product", {})
                            
                            # --- Zvyšok tvojej logiky (fotka, certifikáty, atď.) ---
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                img_url = prod.get('image_url')
                                if img_url:
                                    st.image(img_url, use_container_width=True)
                                else:
                                    st.info("Bez fotky")
                            
                            with col2:
                                name = prod.get('product_name') or "Neznámy produkt"
                                st.subheader(name)
                                
                                labels = prod.get('labels_tags', [])
                                if any('gluten-free' in l or 'crossed-grain' in l for l in labels):
                                    st.success("✅ **Certifikovaný bezlepkový**")
                                if any('bio' in l or 'organic' in l for l in labels):
                                    st.write("🍃 **BIO certifikát**")

                            # Analýza textov
                            ingr_raw = prod.get("ingredients_text_sk") or prod.get("ingredients_text") or ""
                            allergens_raw = prod.get("allergens") or ", ".join(prod.get("allergens_hierarchy", [])) or ""
                            traces_raw = prod.get("traces") or ", ".join(prod.get("traces_hierarchy", [])) or ""
                            
                            zakazane = ["pšenič", "jačmeň", "raž", "ovos", "lepok", "gluten", "slad", "wheat", "barley"]
                            
                            if any(s in ingr_raw.lower() or s in allergens_raw.lower() for s in zakazane):
                                st.error("### ❌ OBSAHUJE LEPOK")
                            elif any(s in traces_raw.lower() for s in zakazane):
                                st.warning("### ⚠️ MÔŽE OBSAHOVAŤ LEPOK")
                            else:
                                st.success("### ✅ VYZERÁ TO BEZPEČNE")

                        else:
                            st.warning(f"Produkt s EAN {ean} sa v databáze nenašiel.")
                    except ValueError:
                        st.error("Chyba: Server vrátil neplatné dáta (nie JSON).")
                else:
                    st.error(f"Server vrátil chybu: {response.status_code}. Skúste to o chvíľu.")
                    
            except requests.exceptions.Timeout:
                st.error("Chyba: Server neodpovedá včas. Skúste to neskôr.")
            except Exception as e:
                st.error(f"Vyskytla sa neočakávaná chyba: {e}")

st.divider()
st.caption("Dáta: MZ SR & Open Food Facts")
