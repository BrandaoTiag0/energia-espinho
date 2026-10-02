"""Mystery, step 6: is the cold effect real, or do colder municipalities just heat more with electricity?

Uses DGEG's official 2024 figures by municipality (consumption by consumer type and number of
consumers) to build two controls:
  kWh per home   domestic consumption / domestic consumers - how much homes rely on electricity
  domestic share domestic consumption / all consumption, in %
and repeats the regression across municipalities (src/misterio_regressao.py) with them:

  M1  winter jump = a + b * extra heating degree days
  M2  + kWh per home
  M3  + kWh per home + domestic share

If b barely moves, the cold effect is not just "inland homes heat with electricity".

Input: data/raw/dgeg-ect-2024.xlsx and data/raw/dgeg-enc-2024.xlsx (downloaded from dgeg.gov.pt,
Estatistica > Energia > Eletricidade). The extracted figures are saved to
data/processed/dgeg_municipios_2024.csv, so the analysis also runs without the Excel files.
Only the Python standard library is used. Usage: py src/dgeg_controlo.py
"""
import csv
import random
import statistics
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RAW = Path("data/raw")
OUT = Path("data/processed/dgeg_municipios_2024.csv")


def pivot_records(path):
    """The DGEG files are pivot tables; the full data sits in the pivot cache."""
    z = zipfile.ZipFile(path)
    d = ET.fromstring(z.read("xl/pivotCache/pivotCacheDefinition1.xml"))
    fields = []
    for cf in d.find("m:cacheFields", NS).findall("m:cacheField", NS):
        shared = cf.find("m:sharedItems", NS)
        fields.append((cf.get("name"), [it.get("v") for it in shared] if shared is not None else []))
    rows = []
    for rec in ET.fromstring(z.read("xl/pivotCache/pivotCacheRecords1.xml")).findall("m:r", NS):
        row = {}
        for (name, items), cell in zip(fields, list(rec)):
            tag, v = cell.tag.split("}")[1], cell.get("v")
            row[name] = items[int(v)] if tag == "x" else float(v) if tag == "n" else None if tag == "m" else v
        rows.append(row)
    return rows


def municipality_codes(path):
    """Code -> name from the 'Municipios' sheet (code 107 is Espinho -> '0107')."""
    z = zipfile.ZipFile(path)
    shared = [("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
              for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid = [s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
           for s in wb.find("m:sheets", NS) if s.get("name") == "Municipios"][0]
    target = [r.get("Target") for r in rels if r.get("Id") == rid][0].lstrip("/")
    sheet = ET.fromstring(z.read(target if target.startswith("xl/") else "xl/" + target))
    codes = {}
    for row in sheet.iter("{%s}row" % NS["m"]):
        vals = []
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if v is None:
                vals.append(None)
            elif c.get("t") == "s":
                vals.append(shared[int(v.text)])
            else:
                vals.append(v.text)
        if len(vals) >= 2 and vals[0] and str(vals[0]).replace(".0", "").isdigit():
            codes[vals[1].strip()] = f"{int(float(vals[0])):04d}"
    return codes


def build_csv():
    ect, enc = RAW / "dgeg-ect-2024.xlsx", RAW / "dgeg-enc-2024.xlsx"
    codes = municipality_codes(ect)
    dom_kwh, tot_kwh, dom_n = defaultdict(float), defaultdict(float), defaultdict(float)
    for r in pivot_records(ect):
        if r["Tensão"] not in ("Alta", "Baixa") or not r["Consumo"]:
            continue  # grid consumption only: self-consumption (Autoconsumo) is not billed by the grid
        name = r["Município"].strip()
        tot_kwh[name] += r["Consumo"]
        if r["TipoConsumo"] == "Doméstico":
            dom_kwh[name] += r["Consumo"]
    for r in pivot_records(enc):
        if r["Tipo"] == "Doméstico" and r["Nº Consumidores"]:
            dom_n[r["Município"].strip()] += r["Nº Consumidores"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "municipio", "domestic_kwh", "domestic_consumers", "total_kwh"])
        for name in sorted(tot_kwh):
            if name in codes and dom_n.get(name):
                w.writerow([codes[name], name, round(dom_kwh[name]), int(dom_n[name]), round(tot_kwh[name])])
    print("Saved", OUT)


def ols(X, y):
    """Least squares with an intercept, by solving the normal equations (no numpy needed)."""
    rows = [[1.0] + list(x) for x in X]
    k = len(rows[0])
    A = [[sum(r[i] * r[j] for r in rows) for j in range(k)] for i in range(k)]
    b = [sum(r[i] * t for r, t in zip(rows, y)) for i in range(k)]
    for c in range(k):  # Gauss-Jordan elimination
        p = max(range(c, k), key=lambda i: abs(A[i][c]))
        A[c], A[p], b[c], b[p] = A[p], A[c], b[p], b[c]
        for i in range(k):
            if i != c:
                f = A[i][c] / A[c][c]
                A[i] = [a - f * ac for a, ac in zip(A[i], A[c])]
                b[i] -= f * b[c]
    coef = [b[i] / A[i][i] for i in range(k)]
    pred = [sum(c * v for c, v in zip(coef, r)) for r in rows]
    mean = sum(y) / len(y)
    r2 = 1 - sum((t - p) ** 2 for t, p in zip(y, pred)) / sum((t - mean) ** 2 for t in y)
    return coef, r2


if (RAW / "dgeg-ect-2024.xlsx").exists() and (RAW / "dgeg-enc-2024.xlsx").exists():
    build_csv()

dgeg = {}
with open(OUT, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        dgeg[r["code"]] = r
rows = []
with open("data/processed/misterio_frio.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        d = dgeg.get(r["code"])
        if not d:
            continue
        rows.append({
            "code": r["code"],
            "winter": float(r["winter"]),
            "hdd": float(r["hdd_change"]),
            "kwh_home": float(d["domestic_kwh"]) / float(d["domestic_consumers"]),
            "dom_share": float(d["domestic_kwh"]) / float(d["total_kwh"]) * 100,
        })
print("Municipalities with both weather and DGEG data:", len(rows))
print(f"kWh per home, median: {statistics.median(r['kwh_home'] for r in rows):,.0f}   "
      f"domestic share, median: {statistics.median(r['dom_share'] for r in rows):.0f}%")
print(f"Correlation extra cold vs kWh per home:   {statistics.correlation([r['hdd'] for r in rows], [r['kwh_home'] for r in rows]):+.2f}")
print(f"Correlation extra cold vs domestic share: {statistics.correlation([r['hdd'] for r in rows], [r['dom_share'] for r in rows]):+.2f}")
print(f"Correlation kWh per home vs winter jump:  {statistics.correlation([r['kwh_home'] for r in rows], [r['winter'] for r in rows]):+.2f}")

MODELS = [("M1  extra cold", ["hdd"]),
          ("M2  + kWh per home", ["hdd", "kwh_home"]),
          ("M3  + kWh per home + domestic share", ["hdd", "kwh_home", "dom_share"])]
med_hdd = statistics.median(r["hdd"] for r in rows)
med_jump = statistics.median(r["winter"] for r in rows)
random.seed(1)
print()
print(f"{'model':38s} {'b (pts/100 dd)':>15s} {'95% range':>16s} {'weather share':>14s} {'R2':>5s}")
for name, keys in MODELS:
    X = [[r[k] for k in keys] for r in rows]
    y = [r["winter"] for r in rows]
    coef, r2 = ols(X, y)
    boots = []
    for _ in range(1000):
        idx = random.choices(range(len(rows)), k=len(rows))
        c, _ = ols([X[i] for i in idx], [y[i] for i in idx])
        boots.append(c[1])
    boots.sort()
    lo, hi = boots[25] * 100, boots[974] * 100
    share = coef[1] * med_hdd / med_jump * 100
    print(f"{name:38s} {coef[1] * 100:+15.2f} {lo:+7.2f} to {hi:+6.2f} {share:13.0f}% {r2:5.2f}")
    if len(keys) > 1:
        extras = ", ".join(f"{k}: {c:+.4f}" for k, c in zip(keys[1:], coef[2:]))
        print(f"{'':38s} other coefficients: {extras}")
for r in rows:
    if r["code"] == "0107":
        print(f"\nEspinho: {r['kwh_home']:,.0f} kWh per home, domestic share {r['dom_share']:.0f}%, "
              f"extra cold {r['hdd']:+.0f}, winter jump {r['winter']:+.1f}%")
