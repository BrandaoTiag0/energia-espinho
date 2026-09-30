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

soma = defaultdict(float)
contagem = defaultdict(int)
for dia, t in zip(diario["time"], diario["temperature_2m_mean"]):
    if t is None:
        continue
    mes = dia[:7]
    soma[mes] += t
    contagem[mes] += 1
temp = {m: soma[m] / contagem[m] for m in soma}

consumo = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for linha in csv.DictReader(f):
        consumo[linha["data"]] = float(linha["energia_ativa_kwh"])
consumo.pop("2026-05", None)

meses = sorted(m for m in consumo if m in temp)

with open("data/processed/temperatura_mensal.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["data", "temperatura_media_c"])
    for m in meses:
        w.writerow([m, round(temp[m], 2)])

print("Correlação temperatura x consumo:",
      round(statistics.correlation([temp[m] for m in meses], [consumo[m] for m in meses]), 2))
print()
print("mês      temp(C)  consumo(kWh)")
for m in meses:
    if m >= "2024-10":
        print(m, " ", round(temp[m], 1), "  ", round(consumo[m]))
