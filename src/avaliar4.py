import csv
import statistics

def ler(caminho, coluna):
    d = {}
    with open(caminho, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            d[linha["data"]] = float(linha[coluna])
    return d

consumo = ler("data/processed/espinho_mensal.csv", "energia_ativa_kwh")
temp = ler("data/processed/temperatura_mensal.csv", "temperatura_media_c")
consumo.pop("2026-05", None)
meses = sorted(m for m in consumo if m in temp)

def erro(previsto, real):
    return abs(previsto - real) / real * 100

def ajustar(i):
    # usa só meses ANTES de i (sem espreitar o futuro)
    dT = [temp[meses[j]] - temp[meses[j - 12]] for j in range(12, i)]
    dC = [consumo[meses[j]] / consumo[meses[j - 12]] - 1 for j in range(12, i)]
    sem_tend = statistics.linear_regression(dT, dC, proportional=True)
    com_tend = statistics.linear_regression(dT, dC)
    return sem_tend, com_tend

nomes = ["simples", "media 2 anos", "temp sem tendencia", "temp com tendencia"]
erros = {n: [] for n in nomes}
linhas_inverno = []

for i in range(36, len(meses)):
    mes = meses[i]
    real = consumo[mes]
    a1 = consumo[meses[i - 12]]
    a2 = consumo[meses[i - 24]]
    dT_atual = temp[mes] - temp[meses[i - 12]]
    sem_tend, com_tend = ajustar(i)

    prev = {
        "simples": a1,
        "media 2 anos": (a1 + a2) / 2,
        "temp sem tendencia": a1 * (1 + sem_tend.slope * dT_atual),
        "temp com tendencia": a1 * (1 + com_tend.slope * dT_atual + com_tend.intercept),
    }
    for n in nomes:
        erros[n].append(erro(prev[n], real))
    if "2025-11" <= mes <= "2026-02":
        linhas_inverno.append((mes, [round(erro(prev[n], real), 1) for n in nomes]))

n_meses = len(erros["simples"])
print("Meses testados:", n_meses, "de", meses[36], "a", meses[-1])
print()
for n in nomes:
    ganha = sum(1 for a, b in zip(erros[n], erros["simples"]) if a < b)
    print(n.ljust(20), round(sum(erros[n]) / n_meses, 2), "%  | ganha ao simples em", ganha, "de", n_meses)

print()
print("Inverno 2025/26 (erro %):", nomes)
for mes, e in linhas_inverno:
    print(mes, e)

sem_tend, com_tend = ajustar(len(meses))
print()
print("Ajuste final (todos os dados):")
print("  cada 1 C mais frio -> consumo", round(-com_tend.slope * 100, 1), "% mais alto")
print("  tendencia de fundo (sem efeito do frio):", round(com_tend.intercept * 100, 1), "% por ano")
