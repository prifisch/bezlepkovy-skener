# src/utils/keywords.py

# Zoznam surovín, ktoré priamo obsahujú lepok
GLUTEN_INGREDIENTS = [
    "pšenica", "pšeničný", "raž", "ražný", "jačmeň", "jačmenný", 
    "ovos", "ovsený", "špaldová", "špalda", "kamut", "tritikále", 
    "slad", "sladový", "jačmeňový slad", "pšeničný škrob", "krupica"
]

# Zoznam fráz, ktoré naznačujú riziko kontaminácie
MAY_CONTAIN = [
    "môže obsahovať stopy", "môže obsahovať lepok", 
    "vyrobené v závode, kde sa spracováva"
]

def analyze_ingredients(text_sk):
    """
    Analyzuje zloženie potraviny a vráti status bezpečnosti.
    """
    text_raw = text_sk.lower()
    found_gluten = [item for item in GLUTEN_INGREDIENTS if item in text_raw]
    found_traces = [item for item in MAY_CONTAIN if item in text_raw]

    if found_gluten:
        return {
            "status": "RED",
            "message": "Obsahuje lepok!",
            "detected": found_gluten
        }
    
    if found_traces:
        return {
            "status": "ORANGE",
            "message": "Pozor na stopy lepku.",
            "detected": found_traces
        }

    return {
        "status": "GREEN",
        "message": "Podľa zloženia neobsahuje lepok.",
        "detected": []
    }
