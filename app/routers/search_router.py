from fastapi import APIRouter

router = APIRouter(prefix="/search-parts", tags=["Search"])


@router.post("/")
def search_parts_mock():
    """Мок-ручка для имитации результата поиска запчастей."""
    return {
        "status": "ok",
        "data": {
            "products": [
                {
                    "product_url": "https://www.autoteile-markt.de/shop/artikel/bremsbelagsatz-scheibenbremse-vorderachse-master-sport-germany-13046027642n-set-ms-d235e106d005c3f0e7c4b63951ffc162",
                    "title": "Bremsbelagsatz, Scheibenbremse Vorderachse MASTER-SPORT GERMANY 13046027642N-SET-MS",
                    "image_url": "https://cdn.autoteile-markt.de/tecdoc/0358/13046027642N-SET-MS_550_500_75.webp",
                    "price": "30,91 €",
                    "seller_name": "N/A",
                    "delivery_time": "3 - 5 Werktage",
                    "description": "Das Produkt Bremsbelagsatz, Scheibenbremse des Herstellers MASTER-SPORT GERMANY hat die Breite 175 mm. Die Dicke/Stärke ist 20,1 mm, das Bruttogewicht beträgt 2,75 kg und die Höhe lautet 70 mm. Bremsbelagsatz, Scheibenbremse hat die ergänzenden Artikelinformationen mit Anti-Quietsch-Blech und passt beispielsweise zu Fahrzeugen von SKODA, VW und SEAT. Der angebotene Artikel wird unter anderem unter den Original Ersatzteilnummern bzw. Vergleichsnummern 3C0 698 151 E, 3C0 698 151 F, 7N0 698 151 A, 7N0 698 151 C, 7N0 698 151 D geführt.",
                },
                {
                    "product_url": "https://www.autoteile-markt.de/shop/artikel/bremsbelagsatz-scheibenbremse-vorderachse-trw-gdb3206-14876062127a98860d7243cef15232f5",
                    "title": "Bremsbelagsatz, Scheibenbremse Vorderachse TRW GDB3206",
                    "image_url": "https://cdn.autoteile-markt.de/tecdoc/0161/0161gdb3206_550_500_75.webp",
                    "price": "15,14 €",
                    "seller_name": "N/A",
                    "delivery_time": "1 - 7 Werktage",
                    "description": "Das Produkt Bremsbelagsatz, Scheibenbremse des Herstellers TRW hat die Breite 91,6 mm. Der Artikel besitzt das Prüfzeichen E2 90R 01124/002, die Höhe lautet 64 mm und die Herstellereinschränkungen lauten SUMITOMO. Bremsbelagsatz, Scheibenbremse hat eine Dicke/Stärke von 15,5 mm und passt beispielsweise zu Fahrzeugen von KIA und MAZDA. Der angebotene Artikel wird unter anderem unter den Original Ersatzteilnummern bzw. Vergleichsnummern DCY0-33-23Z A, DCY0-33-23Z B, DCY03323Z, 0K30A3328Z, K0BA23328Z geführt.",
                },
                {
                    "product_url": "https://www.autoteile-markt.de/shop/artikel/bremsbelagsatz-scheibenbremse-vorderachse-trw-gdb3273-bb4f6cce6aead69789e9d56eff1e3d7f",
                    "title": "Bremsbelagsatz, Scheibenbremse Vorderachse TRW GDB3273",
                    "image_url": "https://cdn.autoteile-markt.de/tecdoc/0161/0161gdb3273_550_500_75.webp",
                    "price": "28,20 €",
                    "seller_name": "N/A",
                    "delivery_time": "1 - 3 Werktage",
                    "description": "Das Produkt Bremsbelagsatz, Scheibenbremse des Herstellers TRW hat das Prüfzeichen E2 90R 01124/012. Die Herstellereinschränkungen lauten AKEBONO, die Breite beträgt 139,3 mm und die Höhe lautet 59,5 mm. Bremsbelagsatz, Scheibenbremse hat eine Dicke/Stärke von 14,8 mm und passt beispielsweise zu Fahrzeugen von INFINITI und NISSAN. Der angebotene Artikel wird unter anderem unter den Original Ersatzteilnummern bzw. Vergleichsnummern 41060-0P690, 41060-0P691, 41060-0P693, 41060-3Y690, 41060-60U90 geführt.",
                },
            ]
        },
        "search_parameters_used": {
            "vin_recognized": "WVWZZZ3CZLE073029",
            "kba_recognized": "0603/BRA",
            "identified_part_type": "Bremsbelag",
            "vehicle_model": {
                "brand_model": "VW Passat B8 Variant (3G)",
                "engine": "2.0 TDI",
                "kba_id": "19080",
                "url": "https://www.autoteile-markt.de/shop/q-lamp/vw-passat-b8-variant-(3g)-2.0-tdi-ersatzteile-fi19080",
            },
        },
    }
