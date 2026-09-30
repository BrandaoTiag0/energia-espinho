import csv
import requests
from collections import defaultdict

BASE = ("https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
        "consumos-faturados-por-periodo-tarifario/records")
COLS = ["energia_ativa_simples_kwh", "energia_ativa_vazio_kwh",
        "energia_ativa_fora_de_vazio_kwh", "energia_ativa_super_vazio_kwh",
        "energia_ativa_ponta_kwh", "energia_ativa_cheias_kwh",
        "energia_ativa_total_kwh"]

linhas = []
offset = 0
while True:
    r = requests.get(BASE, params={"where": 'con_code="0107"', "limit": 100, "offset": offset}, timeout=60)
    r.raise_for_status()
    lote = r.json().get("results", [])
    linhas.extend(lote)
    if len(lote) < 100:
        break
    offset += 100

print("Registos de Espinho:", len(linhas))
if not linhas:
    raise SystemExit("Sem registos para con_code 0107")
print("Freguesias:", sorted({l["fre_name"] for l in linhas}))

mes = defaultdict(lambda: defaultdict(float))
for l in linhas:
    for c in COLS:
        mes[l["data"]][c] += l.get(c) or 0.0

meses = sorted(mes)
print("Meses:", len(meses), "de", meses[0], "a", meses[-1])

with open("data/processed/espinho_tarifario.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["data"] + COLS)
    for m in meses:
        w.writerow([m] + [round(mes[m][c], 3) for c in COLS])

nosso = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for l in csv.DictReader(f):
        nosso[l["data"]] = float(l["energia_ativa_kwh"])

print()
print("mês      total GWh  simples vazio fora_vz super_vz ponta cheias   vs espinho_mensal")
for m in meses[:3] + meses[-3:]:
    t = mes[m]["energia_ativa_total_kwh"]
    pc = [mes[m][c] / t * 100 for c in COLS[:6]]
    if m in nosso:
        comp = f"{(t / nosso[m] - 1) * 100:+.1f}%"
    else:
        comp = "sem dados"
    print(m, f"{t / 1e6:9.2f}", " ".join(f"{p:6.1f}" for p in pc), "  ", comp)
