import pandas as pd # Budeme potrebovať knižnicu pandas: pip install pandas openpyxl
import json
import os

def import_kategorizacia(file_path):
    """
    Spracuje Excel zoznam z MZ SR a uloží ho ako JSON.
    Očakáva stĺpce ako 'Názov doplnku', 'Výrobca', 'EAN'.
    """
    # Načítanie Excelu (často začína na 4. alebo 5. riadku, treba upraviť podľa súboru)
    df = pd.read_excel(file_path, skiprows=4) 
    
    database = {}
    
    for _, row in df.iterrows():
        # MZ SR zoznamy majú špecifické názvy stĺpcov
        ean = str(row.get('EAN kód', '')).strip()
        name = row.get('Názov dietetickej potraviny', '')
        vyrobca = row.get('Držiteľ rozhodnutia o registrácii', '')

        if ean and ean != 'nan':
            database[ean] = {
                "name": name,
                "producer": vyrobca,
                "source": "MZ SR Kategorizácia",
                "status": "GREEN", # Všetko v tomto zozname MUSÍ byť bezlepkové
                "message": "Overená dietetická potravina (kategorizovaná)"
            }
    
    # Uloženie do spracovanej podoby
    with open('data/processed/kategorizacia.json', 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Importovaných {len(database)} produktov zo zoznamu MZ SR.")
