from src.api.off_client import OpenFoodFactsClient

def main():
    client = OpenFoodFactsClient()
    
    # Príklad: EAN kód pre nejaký produkt (napr. 8008698001065 je Schär Chlieb)
    ean_to_test = input("Zadajte EAN kód produktu: ")
    
    result = client.get_product_info(ean_to_test)
    
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"\n📦 Produkt: {result['name']}")
        print(f"🛡️ Status: {result['analysis']['message']}")
        if result['analysis']['detected']:
            print(f"⚠️ Nájdené látky: {', '.join(result['analysis']['detected'])}")
        print(f"📝 Zloženie: {result['ingredients'][:100]}...")

if __name__ == "__main__":
    main()
