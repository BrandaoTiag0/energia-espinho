import json
import requests

URL = "https://servicebus.ren.pt/datahubapi/electricity/ElectricityConsumptionSupplyDaily"
r = requests.get(URL, params={"culture": "pt-PT", "date": "2026-01-23"}, timeout=30)
print("Estado:", r.status_code)
try:
    print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:2500])
except ValueError:
    print("Resposta que não é JSON:", r.text[:500])
