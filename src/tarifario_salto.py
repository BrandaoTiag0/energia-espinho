import csv

dados = {}
with open("data/processed/espinho_tarifario.csv",
          newline="", encoding="utf-8") as f:
    for l in csv.DictReader(f):
        dados[l["data"]] = {
            k: float(v) for k, v in l.items() if k != "data"}

T = "energia_ativa_total_kwh"
NOMES = {
    "energia_ativa_simples_kwh": "simples",
    "energia_ativa_vazio_kwh": "vazio",
    "energia_ativa_fora_de_vazio_kwh": "fora de vazio",
    "energia_ativa_super_vazio_kwh": "super vazio",
    "energia_ativa_ponta_kwh": "ponta",
    "energia_ativa_cheias_kwh": "cheias",
}
MESES = ["2024-10", "2024-11", "2024-12",
         "2025-10", "2025-11", "2025-12"]


def ant(m):
    return str(int(m[:4]) - 1) + m[4:]


print("Variação face ao mesmo mês do ano anterior")
for m in MESES:
    a = ant(m)
    tot = dados[m][T] - dados[a][T]
    pt = tot / dados[a][T] * 100
    print()
    print(m, "total:", round(tot / 1e3), "MWh,", f"{pt:+.1f} %")
    for col, nome in NOMES.items():
        d = dados[m][col] - dados[a][col]
        base = dados[a][col]
        pct = d / base * 100 if base else float("nan")
        linha = f"  {nome:14s} {d / 1e3:+8.0f} MWh"
        linha += f" {pct:+7.1f} %"
        if m >= "2025-10" and abs(tot) > 1e5:
            parte = d / tot * 100
            linha += f"  {parte:+6.0f} % do aumento"
        print(linha)
