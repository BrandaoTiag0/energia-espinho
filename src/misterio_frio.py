"""Mystery, step 4: did the municipalities that got colder (or hotter) jump more?

For each mainland municipality:
  - finds its coordinates (Open-Meteo geocoding; three names are set by hand)
  - downloads daily mean temperature (Open-Meteo archive), only the days needed
  - heating degree days, Nov-Dec 2025 against Nov-Dec 2024 (Eurostat: 18 - T when T <= 15)
  - cooling degree days, Jul-Aug 2025 against Jul-Aug 2024 (Eurostat: T - 21 when T >= 24)
and compares them with the single-rate jumps in data/processed/misterio_concelhos.csv.

Strong positive correlation: the weather explains the jumps.
Near zero: the cause is national and not about local weather.

Open-Meteo's free API has limits per minute, hour and day. Progress is saved after
every batch (data/processed/concelhos_temperaturas.json), so if the script stops,
run it again and it carries on where it stopped.

Run src/misterio_concelhos.py first. Only the Python standard library is used.
Usage: py src/misterio_frio.py
"""
import csv
import json
import statistics
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EREDES = "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/{}/exports/json"
GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
PROCESSED = Path("data/processed")
COORDS = PROCESSED / "concelhos_coordenadas.csv"
TEMPS = PROCESSED / "concelhos_temperaturas.json"
BATCH = 25  # places per request

# Only the days we need: (start, end, kind, year)
WINDOWS = [
    ("2024-07-01", "2024-08-31", "cdd", "2024"),
    ("2024-11-01", "2024-12-31", "hdd", "2024"),
    ("2025-07-01", "2025-08-31", "cdd", "2025"),
    ("2025-11-01", "2025-12-31", "hdd", "2025"),
]

# Municipality seats that the geocoder did not find (approximate coordinates)
MANUAL = {
    "carrazeda de ansiaes": (41.2376, -7.3001),
    "vila nova de poiares": (40.2086, -8.2531),
    "almeida": (40.7244, -6.9065),
}


def get(url, params):
    full = url + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(full, headers={"User-Agent": "energia-espinho/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def get_retry(url, params, tries=15):
    """Like get(), but waits and tries again when Open-Meteo says 'too many requests'."""
    for attempt in range(1, tries + 1):
        try:
            return get(url, params)
        except urllib.error.HTTPError as error:
            if error.code != 429:
                raise
            try:
                reason = json.loads(error.read().decode("utf-8")).get("reason", "")
            except Exception:
                reason = ""
            low = reason.lower()
            if "daily" in low:
                raise SystemExit("Open-Meteo's DAILY limit is used up (" + reason + ").\n"
                                 "Progress is saved. Run the script again tomorrow.")
            wait = 70 if "minut" in low else 300
            print(f"  Open-Meteo says too many requests ({reason or 'no reason given'}). "
                  f"Waiting {wait} s... (try {attempt} of {tries})")
            time.sleep(wait)
    raise SystemExit("Still limited after many tries. Progress is saved: run the script again later.")


def norm(text):
    text = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def mainland(lat, lon):
    return 36.8 <= lat <= 42.2 and -9.6 <= lon <= -6.1


# 1. Municipality names and jumps
jumps = {}
with open(PROCESSED / "misterio_concelhos.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        jumps[r["code"]] = {"winter": float(r["winter"]), "summer": float(r["summer"])}

names = {}
for r in get(EREDES.format("consumos-faturados-por-periodo-tarifario"),
             {"select": "con_code, con_name, dis_name", "group_by": "con_code, con_name, dis_name"}):
    if r.get("con_code") in jumps:
        names[r["con_code"]] = (r.get("con_name"), r.get("dis_name"))
print("Municipalities to place on the map:", len(names))

# 2. Coordinates (cached, so a second run is fast)
coords = {}
if COORDS.exists():
    with open(COORDS, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            coords[r["code"]] = (float(r["lat"]), float(r["lon"]))

missing = []
for code, (name, district) in sorted(names.items()):
    if code in coords:
        continue
    if norm(name) in MANUAL:
        coords[code] = MANUAL[norm(name)]
        continue
    try:
        results = get(GEOCODE, {"name": name, "count": 10, "language": "pt", "country_code": "PT"}).get("results", [])
    except Exception as error:
        print("  geocoding failed for", name, error)
        results = []
    candidates = [r for r in results if mainland(r["latitude"], r["longitude"])]
    best = [r for r in candidates if norm(r.get("admin1")) == norm(district)] or candidates
    if best:
        coords[code] = (best[0]["latitude"], best[0]["longitude"])
    else:
        missing.append(name)
    time.sleep(0.1)

with open(COORDS, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["code", "lat", "lon"])
    for code, (lat, lon) in sorted(coords.items()):
        w.writerow([code, lat, lon])
print("Placed:", len(coords), "| not found:", len(missing), missing[:10])

# 3. Daily temperatures, in batches, saving after each batch
codes = sorted(c for c in coords if c in jumps)
temps = json.loads(TEMPS.read_text(encoding="utf-8")) if TEMPS.exists() else {}
todo = [c for c in codes if c not in temps]
print(f"Temperatures already saved: {len(codes) - len(todo)} | still to download: {len(todo)}")

for i in range(0, len(todo), BATCH):
    batch = todo[i:i + BATCH]
    print(f"Temperatures {i + 1}-{i + len(batch)} of {len(todo)}...")
    acc = {c: {"hdd2024": 0.0, "hdd2025": 0.0, "cdd2024": 0.0, "cdd2025": 0.0} for c in batch}
    for start, end, kind, year in WINDOWS:
        data = get_retry(ARCHIVE, {
            "latitude": ",".join(str(coords[c][0]) for c in batch),
            "longitude": ",".join(str(coords[c][1]) for c in batch),
            "start_date": start, "end_date": end,
            "daily": "temperature_2m_mean", "timezone": "Europe/Lisbon",
        })
        if isinstance(data, dict):
            data = [data]
        for code, place in zip(batch, data):
            for t in place["daily"]["temperature_2m_mean"]:
                if t is None:
                    continue
                if kind == "hdd" and t <= 15:
                    acc[code]["hdd" + year] += 18 - t
                if kind == "cdd" and t >= 24:
                    acc[code]["cdd" + year] += t - 21
        time.sleep(2)
    temps.update(acc)
    TEMPS.write_text(json.dumps(temps), encoding="utf-8")

# 4. Compare
rows = []
for code in codes:
    t = temps.get(code)
    if not t:
        continue
    rows.append({
        "code": code,
        "winter": jumps[code]["winter"],
        "summer": jumps[code]["summer"],
        "hdd_change": t["hdd2025"] - t["hdd2024"],
        "hdd_2024": t["hdd2024"],
        "cdd_change": t["cdd2025"] - t["cdd2024"],
    })

with open(PROCESSED / "misterio_frio.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})


def corr(a, b):
    x, y = [r[a] for r in rows], [r[b] for r in rows]
    return statistics.correlation(x, y), statistics.correlation(x, y, method="ranked")


print()
print("Municipalities compared:", len(rows))
med_h24 = statistics.median(r["hdd_2024"] for r in rows)
med_dh = statistics.median(r["hdd_change"] for r in rows)
print(f"Heating degree days Nov-Dec, median: {med_h24:.0f} in 2024, change in 2025 {med_dh:+.0f} ({med_dh / med_h24 * 100:+.0f}%)")
print(f"Cooling degree days Jul-Aug, median change in 2025: {statistics.median(r['cdd_change'] for r in rows):+.0f}")
print()
print("Correlations (Pearson / ranked):")
p, s = corr("hdd_change", "winter")
print(f"  more cold in Nov-Dec   vs winter jump:  {p:+.2f} / {s:+.2f}")
p, s = corr("cdd_change", "summer")
print(f"  more heat in Jul-Aug   vs summer jump:  {p:+.2f} / {s:+.2f}")
print()
print("Winter jump by quarter of extra cold (weather predicts it rises from Q1 to Q4):")
rows_sorted = sorted(rows, key=lambda r: r["hdd_change"])
q = len(rows_sorted) // 4
for i in range(4):
    part = rows_sorted[i * q:(i + 1) * q] if i < 3 else rows_sorted[3 * q:]
    print(f"  Q{i + 1}  extra cold {part[0]['hdd_change']:+5.0f} to {part[-1]['hdd_change']:+5.0f} degree days"
          f"   median winter jump {statistics.median(r['winter'] for r in part):+6.1f}%")
print()
print("Saved data/processed/misterio_frio.csv and", COORDS)
