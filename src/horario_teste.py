import json
import requests

BASE = ("https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
        "consumos_horario_codigo_postal/records")
r = requests.get(BASE, params={"limit": 5}, timeout=30)
print("Estado:", r.status_code)
dados = r.json()
print("Total de registos no conjunto:", dados.get("total_count"))
for linha in dados.get("results", []):
    print(json.dumps(linha, ensure_ascii=False))
