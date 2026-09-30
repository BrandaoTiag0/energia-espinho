import csv

dados = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for linha in csv.DictReader(f):
        dados[linha["data"]] = float(linha["energia_ativa_kwh"])

dados.pop("2026-05")
meses = sorted(dados)

ganha = 0
total = 0
for i in range(36, len(meses)):
    real = dados[meses[i]]
    a1 = dados[meses[i - 12]]
    a2 = dados[meses[i - 24]]
    erro_simples = abs(a1 - real) / real * 100
    erro_media = abs((a1 + a2) / 2 - real) / real * 100
    total += 1
    if erro_media < erro_simples:
        ganha += 1
    print(meses[i], "simples", round(erro_simples, 1), "% | media 2 anos", round(erro_media, 1), "%")

print("Media de 2 anos ganha em", ganha, "de", total, "meses")
