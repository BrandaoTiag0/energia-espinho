import csv
from collections import defaultdict

tot = defaultdict(float)
freguesias = set()
with open("data/raw/eredes_municipios.csv", newline="", encoding="utf-8-sig") as f:
    for l in csv.DictReader(f, delimiter=";"):
        if l["coddistritoconcelho"] != "0107":
            continue
        if l["nivel_de_tensao"] != "Baixa Tensão" or l["energia_ativa_kwh"] == "":
            continue
        tot[(l["data"], l["freguesia"])] += float(l["energia_ativa_kwh"])
        freguesias.add(l["freguesia"])

freguesias = sorted(freguesias)
print("Baixa Tensão, variação face ao mesmo mês do ano anterior (%)")
print("mês".ljust(9), *[f[:14].ljust(15) for f in freguesias])

for ano in ["2025", "2026"]:
    for mes in range(1, 13):
        m = f"{ano}-{mes:02d}"
        if not ("2025-06" <= m <= "2026-04"):
            continue
        ant = f"{int(ano) - 1}-{mes:02d}"
        celulas = []
        for fr in freguesias:
            a, b = tot.get((ant, fr)), tot.get((m, fr))
            celulas.append((f"{(b / a - 1) * 100:+.1f}" if a and b else "n/d").ljust(15))
        print(m.ljust(9), *celulas)
