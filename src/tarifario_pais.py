import csv
import requests

BASE = ("https://e-redes.opendatasoft.com/api/explore/v2.1/"
        "catalog/datasets/"
        "consumos-faturados-por-periodo-tarifario/records")
SEL = ("data, sum(energia_ativa_simples_kwh) as simples, "
       "sum(energia_ativa_total_kwh) as total")
params = {"select": SEL, "group_by": "data",
          "order_by": "data", "limit": 100}
r = requests.get(BASE, params=params, timeout=60)
print("Estado:", r.status_code)
if r.status_code != 200:
    print(r.text[:500])
    raise SystemExit

pais = {}
for l in r.json()["results"]:
    pais[l["data"][:7]] = {"simples": l["simples"],
                       "total": l["total"]}

esp = {}
with open("data/processed/espinho_tarifario.csv",
          newline="", encoding="utf-8") as f:
    for l in csv.DictReader(f):
        esp[l["data"]] = {
            "simples": float(l["energia_ativa_simples_kwh"]),
            "total": float(l["energia_ativa_total_kwh"])}


def ant(m):
    return str(int(m[:4]) - 1) + m[4:]


def variacao(d, m):
    a = ant(m)
    if m not in d or a not in d:
        return None
    s1, s0 = d[m]["simples"], d[a]["simples"]
    c1 = d[m]["total"] - s1
    c0 = d[a]["total"] - s0
    return (s1 / s0 - 1) * 100, (c1 / c0 - 1) * 100


print("Meses do pais:", len(pais),
      "de", min(pais), "a", max(pais))
print()
print("Variacao face ao mesmo mes do ano anterior (%)")
print("mes        PAIS simples / c.horario",
      "  ESPINHO simples / c.horario")
for m in ["2024-10", "2024-11", "2024-12",
          "2025-10", "2025-11", "2025-12"]:
    p = variacao(pais, m)
    e = variacao(esp, m)
    if p is None or e is None:
        print(m, "sem dados")
        continue
    print(m, f"{p[0]:+9.1f} {p[1]:+9.1f}",
          f"   {e[0]:+9.1f} {e[1]:+9.1f}")
