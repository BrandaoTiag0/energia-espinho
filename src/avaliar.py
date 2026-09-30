import csv

dados = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for linha in csv.DictReader(f):
        dados[linha["data"]] = float(linha["energia_ativa_kwh"])

dados.pop("2026-05")
meses = sorted(dados)

erros_simples = []
erros_tendencia = []
for i in range(24, len(meses)):
    mes = meses[i]
    real = dados[mes]
    simples = dados[meses[i - 12]]
    ultimos_12 = sum(dados[m] for m in meses[i - 12:i])
    anteriores_12 = sum(dados[m] for m in meses[i - 24:i - 12])
    tendencia = simples * (ultimos_12 / anteriores_12)
    erros_simples.append(abs(simples - real) / real * 100)
    erros_tendencia.append(abs(tendencia - real) / real * 100)

n = len(erros_simples)
print("Meses testados:", n, "de", meses[24], "a", meses[-1])
print("Erro médio previsão simples:  ", round(sum(erros_simples) / n, 2), "%")
print("Erro médio com tendência:     ", round(sum(erros_tendencia) / n, 2), "%")
melhores = sum(1 for a, b in zip(erros_tendencia, erros_simples) if a < b)
print("Meses em que a tendência ganha:", melhores, "de", n)
