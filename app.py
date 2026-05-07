import streamlit as st
import requests
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

# ... (CSS sekcia zostáva nezmenená) ...

# 3. ROZŠÍRENÁ MAPA ALERGÉNOV (Kľúčové slová pre detekciu)
ALERGENY_MAPA = {
    "Lepok": ["lepok", "pšenič", "jačmeň", "raž", "ovos", "slad", "pohánka", "špald", "gluten", "wheat", "barley", "rye", "oat"],
    "Kôrovce": ["kôrovce", "krevety", "homár", "rak", "krab", "crustaceans", "shrimp", "prawns"],
    "Vajcia": ["vajcia", "vaječ", "žĺtok", "bielok", "egg", "albumin"],
    "Ryby": ["ryby", "rybac", "fish", "tuniak", "losos", "treska"],
    "Arašidy": ["arašidy", "arašid", "arašidov", "peanuts"],
    "Sója": ["sója", "sójov", "lecitín", "soy", "soya"],
    "Mlieko": ["mlieko", "mlieč", "laktóz", "srvátka", "tvaroh", "smotana", "maslo", "milk", "lactose", "whey"],
    "Orechy": ["orechy", "mandle", "lieskov", "vlašs", "kešu", "pekan", "para", "pistáci", "makadam", "nuts", "almonds", "hazelnut", "cashew"],
    "Zeler": ["zeler", "celery"],
    "Horčica": ["horčica", "mustard"],
    "Sézam": ["sézam", "sesame"],
    "SO2": ["oxid siričitý", "siričitan", "so2", "sulphites", "sulfites"],
    "Vlčí bôb": ["vlčí bôb", "lupina", "lupin"],
    "Mäkkýše": ["mäkkýše", "ustrice", "mušle", "chobotnic", "molluscs", "mussels"]
}

def analyzuj_alergeny(text_slozenie, text_stopy):
    nidene_v_slozeni = []
    najdene_v_stopach = []
    text_slozenie = text_slozenie.lower()
    text_stopy = text_stopy.lower()

    for alergen, kluce in ALERGENY_MAPA.items():
        if any(k in text_slozenie for k in kluce):
            nidene_v_slozeni.append(alergen)
        elif any(k in text_stopy for k in kluce):
            najdene_v_stopach.append(alergen)
            
    return nidene_v_slozeni, najdene_v_stopach

# ... (load_local_db a UI časť s kartami zostáva) ...

# --- SPRACOVANIE VÝSLEDKOV (Upravená časť semaforu) ---
if ean:
    # ... (získanie prod_info a source ostáva rovnaké) ...

    if prod_info:
        # (Zobrazenie Thumbnailu a Názvu ostáva rovnaké)
        
        st.markdown("---")

        # LOGIKA SEMAFORU PRE 14 ALERGÉNOV
        if source == "local":
            st.success("🟢 **OVERENÝ PRODUKT (DIETETICKÝ ZOZNAM)**")
            st.info("Tento produkt je v oficiálnom zozname bezpečných potravín.")
        else:
            p = prod_info["raw"]
            ingr = (p.get("ingredients_text_sk") or p.get("ingredients_text_cs") or p.get("ingredients_text") or "").lower()
            traces = (p.get("traces") or "").lower()
            
            # Detekcia cez funkciu
            najdene, stopy = analyzuj_alergeny(ingr, traces)
            labels = p.get('labels_tags', [])
            is_gluten_free = any('gluten-free' in l or 'crossed-grain' in l for l in labels)

            # Zobrazenie semaforu
            if najdene:
                st.error(f"🔴 **OBSAHUJE ALERGÉNY:**\n{', '.join(najdene)}")
                if "Lepok" in najdene and is_gluten_free:
                    st.warning("⚠️ Rozpor: Produkt má certifikát, ale v zložení boli nájdené kľúčové slová lepku!")
            
            elif stopy:
                st.warning(f"🟡 **MOŽNÉ STOPY ALERGÉNOV:**\n{', '.join(stopy)}")
                if is_gluten_free and "Lepok" not in stopy:
                    st.success("🛡️ Produkt má certifikát 'Gluten-free'")
            
            else:
                if is_gluten_free:
                    st.success("🟢 **BEZPEČNÉ (Certifikovaný Gluten-free)**")
                else:
                    st.success("🟢 **VYZERÁ TO BEZPEČNE**")
                    st.caption("Neboli nájdené zmienky o 14 hlavných alergénoch.")

        # Detailná sekcia (Expander)
        with st.expander("🔍 Kompletná analýza 14 alergénov"):
            for alergen in ALERGENY_MAPA.keys():
                icon = "❌" if alergen in najdene else ("⚠️" if alergen in stopy else "✅")
                stav = "Obsiahnuté" if alergen in najdene else ("Stopy" if alergen in stopy else "Nezistené")
                st.write(f"{icon} **{alergen}:** {stav}")

            # Aditíva
            if source == "off":
                additives = p.get('additives_tags', [])
                if additives:
                    st.write(f"**Aditíva (E-čka):** {', '.join([a.replace('en:', '').upper() for a in additives])}")

        # ... (RASFF a Footer ostáva) ...
