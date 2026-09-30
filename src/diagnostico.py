import csv
from collections import defaultdict

tot = defaultdict(float)
with open("data/raw/eredes_municipios.csv", newline="", encoding="utf-8-sig") as f:
    for l in csv.DictReader(f, delimiter=";"):
        if l["coddistritoconcelho"] != "0107" or l["energia_ativa_kwh"] == "":
            continue
        tot[(l["data"], l["nivel_de_tensao"])] += float(l["energia_ativa_kwh"])

niveis = sorted({n for _, n in tot})
for m in ["2025-11", "2025-12", "2026-01", "2026-02"]:
    ant = str(int(m[:4]) - 1) + m[4:]
    for n in niveis:
        a = tot.get((ant, n))
        b = tot.get((m, n))
        if a and b:
            print(m, "|", n, "|", round(b), "vs", round(a), "|", f"{(b / a - 1) * 100:+.1f}%")
