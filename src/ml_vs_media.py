"""Does a learned model beat the 2-year average? Same test as src/avaliar6.py.

Test months: 2023-11 to 2026-04 (30 months), each forecast with data from before it.
Two scenarios:
  12 months ahead  - only data up to 12 months before the target (how the live page forecasts)
  1 month ahead    - data up to the month before the target (models may use recent months)
The 2-year average and last year's value are the same in both scenarios.

Also tests a hybrid (1 month ahead): the 2-year average, scaled by last month's miss
whenever that miss was more than twice the typical error so far.

Needs numpy, scikit-learn and statsmodels: pip install -r requirements-ml.txt
Usage: py src/ml_vs_media.py
"""
import csv
import warnings
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")
data = {}
with open("data/processed/espinho_mensal.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        data[r["data"]] = float(r["energia_ativa_kwh"]) / 1e6
data.pop("2026-05", None)
months = sorted(data)
y = np.array([data[m] for m in months])
N = len(y)
FIRST = 36
ANOM = {"2025-11", "2025-12", "2026-01", "2026-02"}

def err(p, a): return abs(p - a) / a * 100

def feats(t, use_recent):
    row = [y[t - 12], y[t - 24]]
    if use_recent:
        row += [y[t - 1], y[t - 2], y[t - 3], y[t - 13], y[t - 14], y[t - 15]]
    return row

def learned_linear(i, cut, use_recent):
    # train on rows whose target is known at the cut-off (target index < cut)
    X = [feats(j, use_recent) for j in range(24, cut)]
    Y = [y[j] for j in range(24, cut)]
    model = LinearRegression().fit(X, Y)
    return float(model.predict([feats(i, use_recent)])[0])

def gbm(i, cut, use_recent):
    X = [feats(j, use_recent) + [int(months[j][5:7])] for j in range(24, cut)]
    Y = [y[j] for j in range(24, cut)]
    model = GradientBoostingRegressor(n_estimators=200, max_depth=2, learning_rate=0.05, random_state=0).fit(X, Y)
    return float(model.predict([feats(i, use_recent) + [int(months[i][5:7])]])[0])

def holt_winters(i, cut):
    fit = ExponentialSmoothing(y[:cut], trend="add", damped_trend=True, seasonal="mul", seasonal_periods=12).fit()
    return float(fit.forecast(i - cut + 1)[-1])

def recent_growth(i, cut):
    # last year's value scaled by growth of the last 3 known months against the same months a year before
    g = sum(y[cut - k] for k in (1, 2, 3)) / sum(y[cut - k - 12] for k in (1, 2, 3))
    return y[i - 12] * g

results = {}
def add(name, preds):
    results[name] = preds

tests = list(range(FIRST, N))
add("Last year (simple)", [y[i - 12] for i in tests])
add("Average of 2 years (current)", [(y[i - 12] + y[i - 24]) / 2 for i in tests])
add("Average of 3 years", [(y[i - 12] + y[i - 24] + y[i - 36]) / 3 for i in tests])
for scen, ahead, recent in [("12 months ahead", 12, False), ("1 month ahead", 1, True)]:
    add(f"Learned weights, {scen}", [learned_linear(i, i - ahead + 1, recent) for i in tests])
    add(f"Gradient boosting, {scen}", [gbm(i, i - ahead + 1, recent) for i in tests])
    add(f"Holt-Winters, {scen}", [holt_winters(i, i - ahead + 1) for i in tests])
add("Recent-growth-adjusted last year, 1 month ahead", [recent_growth(i, i) for i in tests])

base = results["Average of 2 years (current)"]
print(f"Test months: {len(tests)} ({months[FIRST]} to {months[-1]}), {sum(months[i] not in ANOM for i in tests)} without the 4 anomalous ones\n")
print(f"{'method':50s} {'all':>7s} {'normal':>8s} {'nov-feb':>8s}  beats 2-yr avg (normal months)")
rows = []
for name, preds in results.items():
    e = [err(p, y[i]) for p, i in zip(preds, tests)]
    en = [x for x, i in zip(e, tests) if months[i] not in ANOM]
    ea = [x for x, i in zip(e, tests) if months[i] in ANOM]
    eb = [err(p, y[i]) for p, i in zip(base, tests) if months[i] not in ANOM]
    wins = sum(a < b for a, b in zip(en, eb))
    rows.append((name, sum(e) / len(e), sum(en) / len(en), sum(ea) / len(ea), wins, len(en)))
for name, a, n, w, wins, k in rows:
    print(f"{name:50s} {a:6.2f}% {n:7.2f}% {w:7.2f}%  {wins} of {k}")


# Hybrid, 1 month ahead: keep the 2-year average, but when last month's forecast missed by more
# than twice the typical error so far, scale this month's forecast by last month's miss.
# No tuning on the test months: "typical error" uses only months before the target.
def avg2(t): return (y[t - 12] + y[t - 24]) / 2
hyb = []
for i in tests:
    past = [err(avg2(t), y[t]) for t in range(24, i)]
    typical = sum(past) / len(past)
    ratio = y[i - 1] / avg2(i - 1)
    hyb.append(avg2(i) * ratio if abs(ratio - 1) * 100 > 2 * typical else avg2(i))
e = [err(p, y[i]) for p, i in zip(hyb, tests)]
en = [x for x, i in zip(e, tests) if months[i] not in ANOM]
ea = [x for x, i in zip(e, tests) if months[i] in ANOM]
eb = [err(avg2(i), y[i]) for i in tests if months[i] not in ANOM]
used = sum(1 for p, i in zip(hyb, tests) if p != avg2(i))
print(f"{'Hybrid: 2-yr avg + correction after a big miss':50s} {sum(e)/len(e):6.2f}% {sum(en)/len(en):7.2f}% {sum(ea)/len(ea):7.2f}%  "
      f"{sum(a < b for a, b in zip(en, eb))} of {len(en)}   (correction used in {used} of {len(tests)} months)")
