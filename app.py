import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="Bezlepkový Skener", page_icon="🌾")
st.title("🌾 Bezlepkový Skener")

# 1. Funkcia na načítanie lokálnej databázy
def load_local_db():
    path = "data/kategorizacia.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

local_db = load_local_db()

ean = st.text_input("Zadajte alebo naskenujte EAN kód:")

if ean:
    # KROK A: Kontrola v štátnej databáze
    if ean in local_db:
        product = local_db[ean]
        st.success(f"### ✅ {product['name']}")
        st.balloons()
        st.write(f"**Výrobca:** {product['producer']}")
        st.info(f"ℹ️ **Info:** {product['note']}")
        
    # KROK B: Ak nie je v štátnej, hľadaj v Open Food Facts
    else:
        with st.spinner('Hľadám v globálnej databáze...'):
            url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
            try:
                res = requests.get(url).json()
                if res.get("status") == 1:
                    prod_data = res["product"]
                    name = prod_data.get("product_name", "Neznámy produkt")
                    ingr = prod_data.get("ingredients_text_sk") or prod_data.get("ingredients_text_en") or "Zloženie neznáme"
                    
                    st.warning(f"### 📦 {name}")
                    st.write("Produkt nie je v oficiálnom zozname na predpis, ale našiel sa v globálnej databáze.")
                    with st.expander("Zobraziť zloženie"):
                        st.write(ingr)
                else:
                    st.error("Produkt sa nenašiel v žiadnej databáze. Skontrolujte obal!")
            except:
                st.error("Chyba spojenia.")
