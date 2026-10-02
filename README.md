# Forecasting electricity use in Espinho, Portugal

A monthly forecast of electricity consumption in Espinho, built only from open data and tested month by month without looking ahead. Then an investigation into the winter of 2025/26, when consumption jumped and the forecast fell behind.

**Interactive page:** https://tbportfolio2026.netlify.app/energia/
It includes a forecast for the next six months that updates itself every week from E-Redes data.

## Result

Method kept: **the average of the same month in the two previous years.**
Every month is forecast using only the months before it. Test window: November 2023 to April 2026.

| Method | Mean error, 30 test months | Mean error, 26 normal months |
|---|---|---|
| Same month last year | 2.76% | 1.86% |
| **Average of the last 2 years** | **2.48%** | **1.62%** |
| Average of the last 3 years | 2.67% | 1.80% |

The 2-year average beats last year's value in 15 of the 26 normal months. A real but small edge, and it could be luck.

## The winter that broke the forecast

From November 2025 to February 2026, low-voltage consumption in Espinho rose 12% to 16% on the year before (total consumption: +8.0% to +10.5%). In March it was back to normal. What I checked:

**It wasn't local.** The jump appears in all four of Espinho's parishes, and in the median of Portugal's 278 mainland municipalities (low voltage): +11.7% in November, +12.4% in December, +13.1% in January, +8.7% in February, −2.6% in March.

**It was mostly real consumption, not a billing error.** REN, which measures what the national grid supplies rather than what is billed, shows national consumption up 6.6% in November, 6.9% in December, 7.6% in January and 3.7% in February (REN Data Hub, read on 30 September 2026; REN revises these figures). National growth explains about two thirds to three quarters of Espinho's jump from November to January, and less than half in February. This is a rough comparison, because the two sources measure different things.

**The cold explains only part of it.** Using heating degree days (Eurostat's definition), December 2025 was as cold as December 2024 (227 against 228) and February too (180 against 177), yet consumption rose 10.3% and 8.0%. Two estimates put the cold's share of the 3.06 GWh increase at 11% (year-on-year fit, 2.5 MWh per degree day) and 29% (regression over all months, 7.0 MWh per degree day, an upper bound). A third estimate compares Portugal's 278 mainland municipalities (`src/misterio_frio.py`, `src/misterio_regressao.py`) and is higher: the municipalities that got colder jumped more, from +12.1% in the quarter with the least extra cold to +16.5% in the quarter with the most (correlation +0.53). A fit across municipalities puts the weather at about 43% of the typical single-rate jump in November and December (95% range 36% to 50%). In summer, heat explains a smaller share, about 23%.

**It was concentrated in single-rate tariffs.** In November and December, 80% and 89% of Espinho's increase came from single-rate tariffs (+14.8% and +17.4%), while time-of-use tariffs rose only 3.5% and 2.4%. Portugal as a whole shows the same pattern (+14.3% and +15.2% against +1.0% and +1.1%). Time-of-use consumption didn't fall, so this doesn't look like customers switching tariffs. Tariff data only goes up to December 2025.

**More customers and smart meters don't explain it.** Contracts grew a steady +0.9% a year with no winter jump, smart-meter coverage was already above 99%, and the municipalities where remote readings grew most did not jump more (correlation −0.26).

**The cause is only partly identified.** For the typical single-rate jump of +14.4% in November and December, about 6 points are weather and about 3 look like ordinary growth (single-rate consumption was already up 2.6% and 3.2% in September and October), which leaves about 5 points, roughly a third, unexplained. This split is rough: comparing municipalities is not proof of cause, and none had zero extra cold, so the part left over is extrapolated. No model trained on Espinho alone predicted the jump, so every result is reported with and without these four months.

**The cold effect holds when accounting for how homes use electricity.** Colder inland municipalities might simply heat more with electricity, which would inflate the weather's share. To check, I added two controls from DGEG's official 2024 figures by municipality (`src/dgeg_controlo.py`): electricity used per home (median 2,248 kWh a year; Espinho 2,556) and the share of consumption that is domestic (median 40%; Espinho 46%). The weather's share barely moves, from 43% to 40-41% (95% range for the cold effect with both controls: 5.8 to 8.0 points per 100 degree days), because the municipalities that got colder were, on the whole, not the ones whose homes rely most on electricity (correlation +0.11). Separately, municipalities where homes use more electricity jumped more for the same extra cold: about +1.6 points for every extra 1,000 kWh per home a year. Cold does not clearly hit those homes harder, though: an interaction term ranges from -1.7 to +3.8 and includes zero.

## What didn't help

- **Growth correction** (average growth of the last 12 months; `src/avaliar.py`, 42 test months from November 2022 to April 2026): 3.41% mean error, against 2.69% for last year's value in the same window.
- **Monthly mean temperature:** its −0.81 correlation with consumption is mostly the seasons. Year on year, one degree colder means only about 0.8% more consumption.
- **Heating degree days with a trend** (`src/graus_dia.py`): 2.29% on all months, 1.62% on normal months, 6.65% in November–February 2025/26, against 2.48%, 1.62% and 8.05% for the 2-year average. No gain in normal months, and it uses the month's real temperature, which isn't known in advance.

## Did machine learning help?

`src/ml_vs_media.py` repeats the same test (the same 30 months, each forecast only with earlier data) for learned models, in two scenarios: forecasting **12 months ahead**, which is what the live page does, and **1 month ahead**, where models may also use the latest months.

| Method | All 30 months | 26 normal months | Nov-Feb 2025/26 |
|---|---|---|---|
| **2-year average (kept)** | 2.48% | **1.62%** | 8.05% |
| Gradient boosting, 12 months ahead | 2.84% | 1.93% | 8.76% |
| Holt-Winters, 12 months ahead | 2.91% | 2.03% | 8.66% |
| Learned weights (linear), 12 months ahead | 4.13% | 3.58% | 7.68% |
| Gradient boosting, 1 month ahead | 2.75% | 1.90% | 8.31% |
| Holt-Winters, 1 month ahead | 2.33% | 2.22% | 3.03% |
| Hybrid: 2-year average, corrected after a big miss, 1 month ahead | **1.98%** | 1.86% | **2.73%** |

- **12 months ahead, nothing beats the 2-year average.** With 66 months of one town there is too little data to learn more than the seasonal pattern.
- **1 month ahead, models that see the latest month catch the winter jump** (from about 8% to about 3%), but they are worse in normal months.
- **The hybrid** keeps the 2-year average and, when last month's forecast missed by more than twice the typical error so far, scales this month's forecast by that miss. It is the best overall (1.98%) and fixed December to February (from 8-9% to about 1%), but it failed in March 2026: the jump ended suddenly, and the correction pushed the error from 0.02% to 8.25%. The idea came after seeing this winter, so it is not proven. The months E-Redes has not published yet will be the real test.
- **Conclusion:** the live forecast keeps the 2-year average.

Needs `pip install -r requirements-ml.txt` (numpy, scikit-learn, statsmodels).

## Limits

- Monthly, billed data, not real-time consumption.
- 30 test months, four of them an unusual winter.
- May 2026 was left out because it was incomplete. As of October 2026, E-Redes hasn't published later months.
- Comparisons between E-Redes and REN are approximate.
- The comparison between municipalities is not proof of cause, and its intercept is extrapolated.

## Reproduce

Python 3 with the standard library and `requests`. Run in this order (on Windows, `py` instead of `python`):

    python src/download_eredes.py            download E-Redes data
    python src/limpar_espinho.py             monthly totals for Espinho
    python src/temperatura.py                daily temperature from Open-Meteo
    python src/avaliar.py                    growth correction, 42 months
    python src/avaliar4.py                   temperature effect
    python src/avaliar6.py                   final results table, 30 months
    python src/diagnostico.py                jump by voltage level
    python src/diagnostico_freguesias.py     jump by parish
    python src/diagnostico_nacional.py       jump across Portugal's municipalities
    python src/graus_dia.py                  heating degree days
    python src/tarifario_espinho.py          Espinho by tariff period
    python src/tarifario_salto.py            increase by tariff period
    python src/tarifario_pais.py             comparison with Portugal
    python src/misterio_catalogo.py          list the E-Redes datasets that could explain the jump
    python src/misterio_hipoteses.py         customers, meters and remote readings over time
    python src/misterio_concelhos.py         municipalities: jump against remote readings
    python src/misterio_frio.py              cold and heat by municipality (Open-Meteo, a few minutes)
    python src/misterio_regressao.py         how much of the jump is weather
    python src/dgeg_controlo.py              the same, with DGEG controls (kWh per home, domestic share)
    python src/ml_vs_media.py                machine learning against the 2-year average (needs requirements-ml.txt)

## Data

- E-Redes Open Data: billed consumption by municipality, and by tariff period.
- Open-Meteo: daily temperature.
- DGEG (Direção-Geral de Energia e Geologia): electricity consumption by municipality and consumer type, and number of consumers, 2024 (provisional). Put `dgeg-ect-2024.xlsx` and `dgeg-enc-2024.xlsx` in `data/raw/` to rebuild `data/processed/dgeg_municipios_2024.csv`.
- REN Data Hub, consumption trends: https://datahub.ren.pt/pt/eletricidade/evolucao-do-consumo/
- REN, November 2025: https://www.ren.pt/media/noticias/consumo-com-recorde-historico-ate-novembro
- REN, December 2025: https://www.ren.pt/media/noticias/consumo-de-energia-eletrica-atinge-valor-mais-elevado-de-sempre-em-2025

Also explored, not used: hourly consumption by postcode (4500 is Espinho), which only covers November 2022 to September 2023; and REN's API (`src/ren_teste.py`), which gives national daily consumption only.

## About

By Tiago Brandão, Computer Engineering student at ISEC, Coimbra. Built with the help of Claude and Claude Code. A summary in Portuguese is in [docs/resumo.md](docs/resumo.md).
