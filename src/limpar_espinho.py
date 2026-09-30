import csv
from collections import defaultdict
from pathlib import Path

raw = Path("data/raw")
processed = Path("data/processed")
processed.mkdir(parents=True, exist_ok=True)

total_por_mes = defaultdict(float)
with open(raw / "eredes_municipios.csv", newline="", encoding="utf-8-sig") as f:
    for linha in csv.DictReader(f, delimiter=";"):
        if linha["coddistritoconcelho"] != "0107":
            continue
        valor = linha["energia_ativa_kwh"]
        if valor == "":
            continue
        total_por_mes[linha["data"]] += float(valor)

meses = sorted(total_por_mes)
if not meses:
    print("Nenhuma linha encontrada para o concelho 0107")
    raise SystemExit

print("Meses:", len(meses), "de", meses[0], "a", meses[-1])
for m in meses:
    print(m, round(total_por_mes[m]))

with open(processed / "espinho_mensal.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["data", "energia_ativa_kwh"])
    for m in meses:
        w.writerow([m, round(total_por_mes[m], 3)])
