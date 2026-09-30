import csv

dados = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for linha in csv.DictReader(f):
        dados[linha["data"]] = float(linha["energia_ativa_kwh"])
dados.pop("2026-05", None)
meses = sorted(dados)

ANOMALOS = {"2025-11", "2025-12", "2026-01", "2026-02"}

def erro(previsto, real):
    return abs(previsto - real) / real * 100

nomes = ["simples", "media 2 anos", "media 3 anos"]
todos = {n: [] for n in nomes}
normais = {n: [] for n in nomes}

for i in range(36, len(meses)):
    mes = meses[i]
    real = dados[mes]
    a1 = dados[meses[i - 12]]
    a2 = dados[meses[i - 24]]
    a3 = dados[meses[i - 36]]
    prev = {
        "simples": a1,
        "media 2 anos": (a1 + a2) / 2,
        "media 3 anos": (a1 + a2 + a3) / 3,
    }
    for n in nomes:
        e = erro(prev[n], real)
        todos[n].append(e)
        if mes not in ANOMALOS:
            normais[n].append(e)

print("Meses testados:", len(todos["simples"]), "| sem os 4 meses anomalos:", len(normais["simples"]))
print()
print("metodo".ljust(14), "todos os meses", " sem anomalos", " ganha ao simples (sem anomalos)")
for n in nomes:
    m_todos = sum(todos[n]) / len(todos[n])
    m_norm = sum(normais[n]) / len(normais[n])
    ganha = sum(1 for a, b in zip(normais[n], normais["simples"]) if a < b)
    print(n.ljust(14), f"{m_todos:6.2f} %      {m_norm:6.2f} %      {ganha} de {len(normais[n])}")
