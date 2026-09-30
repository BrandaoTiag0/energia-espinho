import csv
import statistics
from collections import defaultdict

tot = defaultdict(float)
with open("data/raw/eredes_municipios.csv", newline="", encoding="utf-8-sig") as f:
    for l in csv.DictReader(f, delimiter=";"):
        if l["nivel_de_tensao"] != "Baixa Tensão" or l["energia_ativa_kwh"] == "":
            continue
        if l["coddistritoconcelho"].endswith("--"):
            continue
        tot[(l["coddistritoconcelho"], l["data"])] += float(l["energia_ativa_kwh"])

concelhos = sorted({c for c, _ in tot})
print("Concelhos com dados de Baixa Tensão:", len(concelhos))
print("mês       mediana    10%      90%     concelhos")

for m in ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]:
    ant = str(int(m[:4]) - 1) + m[4:]
    variacoes = []
    for c in concelhos:
        a = tot.get((c, ant))
        b = tot.get((c, m))
        if a and b:
            variacoes.append((b / a - 1) * 100)
    if len(variacoes) < 10:
        print(m, "poucos dados")
        continue
    decis = statistics.quantiles(variacoes, n=10)
    print(m, f"{statistics.median(variacoes):+7.1f}% {decis[0]:+7.1f}% {decis[-1]:+7.1f}%   {len(variacoes)}")
