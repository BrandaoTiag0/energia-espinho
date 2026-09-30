import csv

dados = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for linha in csv.DictReader(f):
        dados[linha["data"]] = float(linha["energia_ativa_kwh"])

dados.pop("2026-05")
meses = sorted(dados)

def erro(previsto, real):
    return abs(previsto - real) / real * 100

res = {"simples (1 ano atras)": [], "media 2 anos": [], "media 3 anos": []}
for i in range(36, len(meses)):
    real = dados[meses[i]]
    a1 = dados[meses[i - 12]]
    a2 = dados[meses[i - 24]]
    a3 = dados[meses[i - 36]]
    res["simples (1 ano atras)"].append(erro(a1, real))
    res["media 2 anos"].append(erro((a1 + a2) / 2, real))
    res["media 3 anos"].append(erro((a1 + a2 + a3) / 3, real))

n = len(res["simples (1 ano atras)"])
print("Meses testados:", n, "de", meses[36], "a", meses[-1])
for nome, erros in res.items():
    print(nome, ":", round(sum(erros) / n, 2), "%")
