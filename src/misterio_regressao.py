"""Mystery, step 5: how much of the single-rate jump is weather, and how much is left?

Reads data/processed/misterio_frio.csv (one row per municipality) and fits, across
municipalities:

    winter jump (%) = a + b * extra heating degree days (Nov-Dec 2025 against 2024)
    summer jump (%) = a + b * extra cooling degree days (Jul-Aug 2025 against 2024)

  b          percentage points of jump per extra degree day
  a          the jump left when there is no extra cold (or heat): what is common to all
             municipalities and not explained by differences in local weather
  weather    b * median extra degree days: the part of the typical jump that the weather
             accounts for, in percentage points and as a share of the median jump

95% ranges come from resampling the municipalities 2000 times (bootstrap).
Caution: this compares municipalities with each other. It is not proof of cause, and
'a' is extrapolated when no municipality had zero extra cold.

Only the Python standard library is used (Python 3.10+).
Usage: py src/misterio_regressao.py
"""
import csv
import random
import statistics

random.seed(1)
with open("data/processed/misterio_frio.csv", newline="", encoding="utf-8") as f:
    rows = [{k: (v if k == "code" else float(v)) for k, v in r.items()} for r in csv.DictReader(f)]
print("Municipalities:", len(rows))


def fit(x, y):
    r = statistics.linear_regression(x, y)
    return r.slope, r.intercept, statistics.correlation(x, y) ** 2


def pct(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, max(0, round(p / 100 * (len(values) - 1))))]


def report(title, xkey, ykey, unit, espinho_code="0107"):
    x = [r[xkey] for r in rows]
    y = [r[ykey] for r in rows]
    b, a, r2 = fit(x, y)
    med_x, med_y = statistics.median(x), statistics.median(y)
    weather = b * med_x

    boots = {"b": [], "a": [], "w": []}
    n = len(rows)
    for _ in range(2000):
        idx = random.choices(range(n), k=n)
        xs, ys = [x[i] for i in idx], [y[i] for i in idx]
        if len(set(xs)) < 2:
            continue
        bb, aa, _ = fit(xs, ys)
        boots["b"].append(bb)
        boots["a"].append(aa)
        boots["w"].append(bb * statistics.median(xs))

    def rng(key, scale=1.0):
        return f"{pct(boots[key], 2.5) * scale:+.2f} to {pct(boots[key], 97.5) * scale:+.2f}"

    print()
    print("=" * 70)
    print(title)
    print(f"  median {unit}: {med_x:+.0f}   |   median jump: {med_y:+.1f}%   |   observed {unit} range: {min(x):+.0f} to {max(x):+.0f}")
    print(f"  R-squared: {r2:.2f}  (share of the differences between municipalities explained)")
    print(f"  b: {b * 100:+.2f} points per 100 {unit}   (95% range {rng('b', 100)})")
    print(f"  a: {a:+.1f}% jump with no extra {unit.split()[0]}   (95% range {rng('a')})")
    print(f"  weather part of the typical jump: {weather:+.1f} points = {weather / med_y * 100:.0f}% of {med_y:.1f}%"
          f"   (95% range {rng('w')} points)")
    print(f"  left over (the intercept): {a:+.1f} points = {a / med_y * 100:.0f}% of the typical jump")
    if min(x) > 0:
        print(f"  note: no municipality had zero extra {unit.split()[0]} (lowest {min(x):+.0f}), so the intercept is extrapolated")
    for r in rows:
        if r["code"] == espinho_code:
            pred = a + b * r[xkey]
            print(f"  Espinho: {unit} {r[xkey]:+.0f}, jump {r[ykey]:+.1f}%, model predicts {pred:+.1f}%")


report("WINTER: single-rate jump, Nov-Dec 2025 vs 2024, against extra heating degree days",
       "hdd_change", "winter", "heating degree days")
report("SUMMER: single-rate jump, Jul-Aug 2025 vs 2024, against extra cooling degree days",
       "cdd_change", "summer", "cooling degree days")
print()
print("Reminder: differences between municipalities, not proof of cause. Report the intercept as a range.")
