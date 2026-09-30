import csv
import statistics
import requests
from collections import defaultdict

URL = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 41.0,
    "longitude": -8.64,
    "start_date": "2020-11-01",
    "end_date": "2026-04-30",
    "daily": "temperature_2m_mean",
    "timezone": "Europe/Lisbon",
}
r = requests.get(URL, params=params, timeout=60)
r.raise_for_status()
diario = r.json()["daily"]

hdd = defaultdict(float)
for dia, t in zip(diario["time"], diario["temperature_2m_mean"]):
    if t is None:
        continue
    hdd[dia[:7]] += (18 - t) if t <= 15 else 0.0

with open("data/processed/graus_dia_mensal.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["data", "graus_dia_aquecimento"])
    for m in sorted(hdd):
        w.writerow([m, round(hdd[m], 1)])

consumo = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for l in csv.DictReader(f):
        consumo[l["data"]] = float(l["energia_ativa_kwh"])
consumo.pop("2026-05", None)
meses = sorted(m for m in consumo if m in hdd)

def ant(m):
    return str(int(m[:4]) - 1) + m[4:]

print("Graus-dia e consumo, inverno a inverno")
print("mês       graus-dia  vs ano ant.   consumo GWh  vs ano ant.")
for m in ["2024-11", "2024-12", "2025-01", "2025-02", "2025-03",
          "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]:
    a = ant(m)
    dh = (hdd[m] / hdd[a] - 1) * 100 if hdd[a] > 0 else float("nan")
    dc = (consumo[m] / consumo[a] - 1) * 100
    print(m, f"{hdd[m]:9.0f} {dh:+10.1f}% {consumo[m] / 1e6:12.2f} {dc:+10.1f}%")

def erro(previsto, real):
    return abs(previsto - real) / real * 100

def ajustar(i, com_tendencia):
    dH = [hdd[meses[j]] - hdd[meses[j - 12]] for j in range(12, i)]
    dC = [consumo[meses[j]] - consumo[meses[j - 12]] for j in range(12, i)]
    if com_tendencia:
        return statistics.linear_regression(dH, dC)
    return statistics.linear_regression(dH, dC, proportional=True)

ANOMALOS = {"2025-11", "2025-12", "2026-01", "2026-02"}
nomes = ["simples", "media 2 anos", "graus-dia sem tend.", "graus-dia com tend."]
todos = {n: [] for n in nomes}
normais = {n: [] for n in nomes}
inverno = {n: [] for n in nomes}

for i in range(36, len(meses)):
    m = meses[i]
    real = consumo[m]
    a1 = consumo[meses[i - 12]]
    a2 = consumo[meses[i - 24]]
    dh = hdd[m] - hdd[meses[i - 12]]
    sem = ajustar(i, False)
    com = ajustar(i, True)
    prev = {
        "simples": a1,
        "media 2 anos": (a1 + a2) / 2,
        "graus-dia sem tend.": a1 + sem.slope * dh,
        "graus-dia com tend.": a1 + com.slope * dh + com.intercept,
    }
    for n in nomes:
        e = erro(prev[n], real)
        todos[n].append(e)
        if m in ANOMALOS:
            inverno[n].append(e)
        else:
            normais[n].append(e)

print()
print("Erro médio (%)".ljust(24), "todos", "  sem anómalos", "  nov-fev 2025/26")
for n in nomes:
    print(n.ljust(24),
          f"{sum(todos[n]) / len(todos[n]):5.2f}",
          f"{sum(normais[n]) / len(normais[n]):10.2f}",
          f"{sum(inverno[n]) / len(inverno[n]):14.2f}")

i0 = meses.index("2025-11")
modelo = ajustar(i0, True)
print()
print("Inverno 2025/26: quanto do aumento se explica pelo frio")
print("(modelo ajustado só com dados anteriores a 2025-11)")
tot_real = 0.0
tot_frio = 0.0
for m in ["2025-11", "2025-12", "2026-01", "2026-02"]:
    a = ant(m)
    real = consumo[m] - consumo[a]
    frio = modelo.slope * (hdd[m] - hdd[a])
    tot_real += real
    tot_frio += frio
    print(m, f"aumento real {real / 1e6:+.2f} GWh | explicado pelo frio {frio / 1e6:+.2f} GWh")
print(f"Total: real {tot_real / 1e6:+.2f} GWh | frio {tot_frio / 1e6:+.2f} GWh | "
      f"explicado {tot_frio / tot_real * 100:.0f} %")
print(f"Cada grau-dia extra = {modelo.slope / 1e3:.1f} MWh; tendência de fundo = "
      f"{modelo.intercept / 1e3:+.0f} MWh por mês")

print()
print("Sensibilidade: declive pelo nível (consumo contra graus-dia, todos os meses)")
niveis = statistics.linear_regression([hdd[m] for m in meses], [consumo[m] for m in meses])
frio_nivel = sum(niveis.slope * (hdd[m] - hdd[ant(m)]) for m in ["2025-11", "2025-12", "2026-01", "2026-02"])
print(f"Cada grau-dia = {niveis.slope / 1e3:.1f} MWh (consumo base {niveis.intercept / 1e6:.2f} GWh)")
print(f"Frio explicaria {frio_nivel / 1e6:+.2f} GWh = {frio_nivel / tot_real * 100:.0f} % do aumento real")
