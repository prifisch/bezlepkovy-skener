import streamlit as st
import requests

# Nastavenie webovej stránky
st.set_page_config(page_title="Bezlepkový Skener", page_icon="🌾")

st.title("🌾 Bezlepkový Skener")
st.write("Vitajte! Tento projekt je v štádiu vývoja.")

# Jednoduché vstupné pole
ean = st.text_input("Zadajte EAN kód produktu:")

if ean:
    st.write(f"Hľadám informácie pre kód: {ean}")
    # Tu neskôr prepojíme tvoju logiku z off_client.py
    url = f"https://world.openfoodfacts.org/api/v2/product/{ean}.json"
    
    try:
        response = requests.get(url).json()
        if response.get("status") == 1:
            product = response["product"]
            name = product.get("product_name", "Neznámy produkt")
            st.success(f"Nájdený produkt: {name}")
            
            ingredients = product.get("ingredients_text_sk", "Zloženie v slovenčine chýba.")
            st.info(f"**Zloženie:** {ingredients}")
        else:
            st.warning("Produkt sa nenašiel v globálnej databáze.")
    except:
        st.error("Chyba pri pripájaní k databáze.")
