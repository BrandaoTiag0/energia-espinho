import csv
import requests
from pathlib import Path

URL = ("https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
       "3-consumos-faturados-por-municipio-ultimos-10-anos/exports/csv")

raw = Path("data/raw")
raw.mkdir(parents=True, exist_ok=True)

r = requests.get(URL, timeout=120)
r.raise_for_status()
ficheiro = raw / "eredes_municipios.csv"
ficheiro.write_bytes(r.content)

with open(ficheiro, newline="", encoding="utf-8-sig") as f:
    linhas = list(csv.DictReader(f, delimiter=";"))

print("Colunas:", list(linhas[0].keys()))
print("Linhas:", len(linhas))

espinho = [l for l in linhas if any("espinho" in str(v).lower() for v in l.values())]
print("Linhas de Espinho:", len(espinho))
for l in espinho[:10]:
    print(l)

if espinho:
    with open(raw / "espinho.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(espinho[0].keys()))
        w.writeheader()
        w.writerows(espinho)
