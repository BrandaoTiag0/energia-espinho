"""Mystery, step 3: compare municipalities to separate H2 (meters) from H3 (weather).

For each mainland municipality:
  winter jump   single-rate energy, Nov-Dec 2025 against Nov-Dec 2024
  summer jump   single-rate energy, Jul-Aug 2025 against Jul-Aug 2024
  read change   share of low-voltage points with remote reads, Nov 2025 minus Nov 2024

If H2 is right, municipalities with a bigger rise in remote reads have bigger winter jumps.
If H3 is right, municipalities with bigger summer jumps also have bigger winter jumps.

Only the Python standard library is used (Python 3.12+ for ranked correlation).
Usage: py src/misterio_concelhos.py
"""
import csv
import json
import statistics
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/{}/exports/json"


def fetch(dataset, select, group_by):
    url = BASE.format(dataset) + "?" + urllib.parse.urlencode({"select": select, "group_by": group_by})
    request = urllib.request.Request(url, headers={"User-Agent": "energia-espinho/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def valid(code):
    return isinstance(code, str) and len(code) == 4 and code.isdigit()


print("Downloading single-rate energy by municipality...")
simples = defaultdict(float)  # (code, month) -> kWh
for r in fetch("consumos-faturados-por-periodo-tarifario",
               "con_code, data, sum(energia_ativa_simples_kwh) as s", "con_code, data"):
    if valid(r.get("con_code")) and r.get("s") is not None:
        simples[(r["con_code"], str(r["data"])[:7])] += float(r["s"])

print("Downloading low-voltage consumption points by municipality...")
pontos = defaultdict(float)
for r in fetch("20-caracterizacao-pes-contrato-ativo",
               "coddistritoconcelho, data, nivel_de_tensao, sum(cpes) as n",
               "coddistritoconcelho, data, nivel_de_tensao"):
    code = r.get("coddistritoconcelho")
    if valid(code) and r.get("nivel_de_tensao") == "Baixa Tensão Normal" and r.get("n") is not None:
        pontos[(code, str(r["data"])[:7])] += float(r["n"])

print("Downloading remote reads by municipality...")
leituras = defaultdict(float)
for r in fetch("23-leituras-recolhidas-remotamente",
               "coddistritoconcelho, data, sum(cpes_com_leituras) as n", "coddistritoconcelho, data"):
    code = r.get("coddistritoconcelho")
    if valid(code) and r.get("n") is not None:
        leituras[(code, str(r["data"])[:7])] += float(r["n"])


def jump(code, new_months, old_months):
    new = sum(simples.get((code, m), 0) for m in new_months)
    old = sum(simples.get((code, m), 0) for m in old_months)
    return (new / old - 1) * 100 if old > 0 and new > 0 else None


def read_share(code, month):
    p = pontos.get((code, month))
    l = leituras.get((code, month))
    return l / p * 100 if p and l else None


rows = []
for code in sorted({c for c, _ in simples}):
    w = jump(code, ["2025-11", "2025-12"], ["2024-11", "2024-12"])
    s = jump(code, ["2025-07", "2025-08"], ["2024-07", "2024-08"])
    r1, r0 = read_share(code, "2025-11"), read_share(code, "2024-11")
    if None in (w, s, r1, r0):
        continue
    rows.append({"code": code, "winter": w, "summer": s, "reads_change": r1 - r0})

print("Municipalities with complete data:", len(rows))
if len(rows) < 30:
    raise SystemExit("Too few municipalities to compare.")

Path("data/processed").mkdir(parents=True, exist_ok=True)
with open("data/processed/misterio_concelhos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["code", "winter", "summer", "reads_change"])
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})


def corr(a, b):
    x = [r[a] for r in rows]
    y = [r[b] for r in rows]
    return statistics.correlation(x, y), statistics.correlation(x, y, method="ranked")


print()
print("Median winter jump (single rate, Nov-Dec):", f"{statistics.median(r['winter'] for r in rows):+.1f}%")
print("Median summer jump (single rate, Jul-Aug):", f"{statistics.median(r['summer'] for r in rows):+.1f}%")
print("Median change in remote-read share:      ", f"{statistics.median(r['reads_change'] for r in rows):+.1f} points")
print()
print("Correlations (Pearson / ranked):")
p, s = corr("reads_change", "winter")
print(f"  H2  remote-read change vs winter jump:  {p:+.2f} / {s:+.2f}")
p, s = corr("summer", "winter")
print(f"  H3  summer jump vs winter jump:         {p:+.2f} / {s:+.2f}")
p, s = corr("reads_change", "summer")
print(f"      remote-read change vs summer jump:  {p:+.2f} / {s:+.2f}")

print()
print("Winter jump by quarter of remote-read change (H2 predicts it rises from Q1 to Q4):")
rows_sorted = sorted(rows, key=lambda r: r["reads_change"])
q = len(rows_sorted) // 4
for i in range(4):
    part = rows_sorted[i * q:(i + 1) * q] if i < 3 else rows_sorted[3 * q:]
    print(f"  Q{i + 1}  read change {part[0]['reads_change']:+6.1f} to {part[-1]['reads_change']:+6.1f} points"
          f"   median winter jump {statistics.median(r['winter'] for r in part):+6.1f}%")
print()
print("Saved data/processed/misterio_concelhos.csv")
