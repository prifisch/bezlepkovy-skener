import requests
# Importujeme našu analytickú funkciu z predchádzajúceho kroku
from src.utils.checker import analyze_ingredients

class OpenFoodFactsClient:
    def __init__(self):
        self.base_url = "https://world.openfoodfacts.org/api/v2/product/"
        # User-Agent je slušnosť pri volaní API, aby vedeli, kto sa pýta
        self.headers = {
            "User-Agent": "BezlepkovySkenerSK - GitHubProject - Version 0.1"
        }

    def get_product_info(self, ean):
        """
        Získa dáta z OFF a preženie ich cez náš bezlepkový filter.
        """
        url = f"{self.base_url}{ean}.json"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 0:
                return {"error": "Produkt nebol v databáze nájdený."}

            product = data.get("product", {})
            
            # Skúšame získať slovenský popis, ak nie je, skúsime češtinu alebo angličtinu
            ingredients = product.get("ingredients_text_sk") or \
                          product.get("ingredients_text_cs") or \
                          product.get("ingredients_text_en") or ""
            
            product_name = product.get("product_name_sk") or \
                           product.get("product_name") or "Neznámy názov"

            # Tu využijeme náš checker.py
            analysis = analyze_ingredients(ingredients)

            return {
                "name": product_name,
                "ean": ean,
                "ingredients": ingredients,
                "analysis": analysis
            }

        except Exception as e:
            return {"error": f"Chyba pri spojení s API: {str(e)}"}
