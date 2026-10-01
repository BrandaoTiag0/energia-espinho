"""Mystery, step 2: test the hypotheses for the single-rate jump (winter 2025/26).

For each E-Redes dataset, asks the API for national monthly totals (summed on
their side, so the download is small), saves them to data/processed/ and prints
the year-on-year change from July 2025 onwards.

H1 more customers:      contracts and consumption points over time
H2 billing / meters:    smart meters and remote readings over time
Reference:              single-rate and total billed energy

Only the Python standard library is used.
Usage: py src/misterio_hipoteses.py
"""
import csv
import json
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/{}/exports/json"
OUT = Path("data/processed")
FROM = "2025-07"

# (name, dataset id, extra group field or None, [(sum expression, label)])
QUERIES = [
    ("energia_tarifa", "consumos-faturados-por-periodo-tarifario", None,
     [("sum(energia_ativa_simples_kwh)", "simples_kwh"), ("sum(energia_ativa_total_kwh)", "total_kwh")]),
    ("contratos", "clientes-por-escalao-de-potencia", None,
     [("sum(numero_de_contratos)", "contratos")]),
    ("cpes_tensao", "20-caracterizacao-pes-contrato-ativo", "nivel_de_tensao",
     [("sum(cpes)", "cpes")]),
    ("contadores", "21-contadores-de-energia", "inclui_emi",
     [("sum(cpes)", "cpes")]),
    ("leituras_remotas", "23-leituras-recolhidas-remotamente", None,
     [("sum(cpes_com_leituras)", "cpes_com_leituras")]),
    ("diagramas_carga", "22-diagrama-de-carga-por-instalacao", None,
     [("sum(cpes_com_dcs_recolhidos)", "cpes_com_dcs")]),
]


def fetch(dataset, group, sums):
    select = ["data"] + ([group] if group else []) + [f"{expr} as {label}" for expr, label in sums]
    params = {"select": ",".join(select), "group_by": ",".join(["data"] + ([group] if group else []))}
    url = BASE.format(dataset) + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "energia-espinho/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def prev_year(month):
    return f"{int(month[:4]) - 1:04d}-{month[5:7]}"


OUT.mkdir(parents=True, exist_ok=True)
for name, dataset, group, sums in QUERIES:
    print("=" * 72)
    print(name, "(" + dataset + ")")
    try:
        rows = fetch(dataset, group, sums)
    except Exception as error:
        print("  failed:", error)
        continue

    # series[(group value, label)][month] = value
    series = defaultdict(dict)
    for row in rows:
        month = str(row.get("data", ""))[:7]
        key = str(row.get(group)) if group else "total"
        for _, label in sums:
            value = row.get(label)
            if value is not None and len(month) == 7:
                series[(key, label)][month] = series[(key, label)].get(month, 0) + float(value)

    with open(OUT / f"misterio_{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["serie", "mes", "valor"])
        for (key, label), values in sorted(series.items()):
            for month in sorted(values):
                w.writerow([f"{key}:{label}", month, round(values[month], 3)])

    for (key, label), values in sorted(series.items()):
        months = sorted(values)
        if not months:
            continue
        print(f"  {key} / {label}   ({months[0]} to {months[-1]})")
        for month in months:
            if month < FROM:
                continue
            old = values.get(prev_year(month))
            change = f"{(values[month] / old - 1) * 100:+6.1f}%" if old else "     n/a"
            print(f"    {month}  {values[month]:>18,.0f}   vs year before {change}")
print("=" * 72)
print("Saved in", OUT)
