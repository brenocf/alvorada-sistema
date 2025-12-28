import requests

API_KEY = "e32611ea-918b-4ed0-8b0e-e4432f9de77b-1df5f4c3-cd44-4821-ac4d-ce5b9c34271a"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}
CITY_ID = "2305506"

endpoints = [
    ("GET", "https://api.cnpja.com/office/companies", {"cityId": CITY_ID}),
    ("GET", "https://api.cnpja.com/office/companies", {"city_id": CITY_ID}),
    ("GET", "https://api.cnpja.com/companies", {"cityId": CITY_ID}),
    ("GET", "https://api.cnpja.com/establishments", {"cityId": CITY_ID}),
    ("GET", "https://api.cnpja.com/office/establishments", {"cityId": CITY_ID}),
    ("POST", "https://api.cnpja.com/office/companies/search", {"cityId": CITY_ID}),
]

print(f"Testando chave: {API_KEY[:10]}...")

for method, url, params in endpoints:
    print(f"\n--- Testando {method} {url} ---")
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        else:
            resp = requests.post(url, headers=HEADERS, json=params, timeout=10)
        
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")
