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

**The cold explains only part of it.** Using heating degree days (Eurostat's definition), December 2025 was as cold as December 2024 (227 against 228) and February too (180 against 177), yet consumption rose 10.3% and 8.0%. Two estimates put the cold's share of the 3.06 GWh increase at 11% (year-on-year fit, 2.5 MWh per degree day) and 29% (regression over all months, 7.0 MWh per degree day, an upper bound).

**It was concentrated in single-rate tariffs.** In November and December, 80% and 89% of Espinho's increase came from single-rate tariffs (+14.8% and +17.4%), while time-of-use tariffs rose only 3.5% and 2.4%. Portugal as a whole shows the same pattern (+14.3% and +15.2% against +1.0% and +1.1%). Time-of-use consumption didn't fall, so this doesn't look like customers switching tariffs. Tariff data only goes up to December 2025.

**The cause is not identified** with the data available. No model trained on Espinho alone predicted the jump, so every result is reported with and without these four months.

## What didn't help

- **Growth correction** (average growth of the last 12 months; `src/avaliar.py`, 42 test months from November 2022 to April 2026): 3.41% mean error, against 2.69% for last year's value in the same window.
- **Monthly mean temperature:** its −0.81 correlation with consumption is mostly the seasons. Year on year, one degree colder means only about 0.8% more consumption.
- **Heating degree days with a trend** (`src/graus_dia.py`): 2.29% on all months, 1.62% on normal months, 6.65% in November–February 2025/26, against 2.48%, 1.62% and 8.05% for the 2-year average. No gain in normal months, and it uses the month's real temperature, which isn't known in advance.

## Limits

- Monthly, billed data, not real-time consumption.
- 30 test months, four of them an unusual winter.
- May 2026 was left out because it was incomplete. As of October 2026, E-Redes hasn't published later months.
- Comparisons between E-Redes and REN are approximate.

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

## Data

- E-Redes Open Data: billed consumption by municipality, and by tariff period.
- Open-Meteo: daily temperature.
- REN Data Hub, consumption trends: https://datahub.ren.pt/pt/eletricidade/evolucao-do-consumo/
- REN, November 2025: https://www.ren.pt/media/noticias/consumo-com-recorde-historico-ate-novembro
- REN, December 2025: https://www.ren.pt/media/noticias/consumo-de-energia-eletrica-atinge-valor-mais-elevado-de-sempre-em-2025

Also explored, not used: hourly consumption by postcode (4500 is Espinho), which only covers November 2022 to September 2023; and REN's API (`src/ren_teste.py`), which gives national daily consumption only.

## About

By Tiago Brandão, Computer Engineering student at ISEC, Coimbra. Built with the help of Claude and Claude Code. A summary in Portuguese is in [docs/resumo.md](docs/resumo.md).
