# SignalBlend - FINS5545 Project B

SignalBlend is an educational systematic-fund prototype for young novice investors who have limited time to compare investment strategies, risks and news. It offers equity-only, crypto-only and combined funds, provides fund fact sheets and an allocation lab, and shows whether equity-sector headline sentiment adds useful evidence.

## What is built

- 12 baseline funds: three asset families × equal weight, minimum variance, maximum Sharpe and risk parity.
- Walk-forward out-of-sample backtests with monthly rebalancing and past-only rolling estimation windows.
- Two equity minimum-variance extensions: a plain sentiment tilt and a coverage-aware sentiment tilt.
- A standalone VADER equity-sector index with ticker coverage, headline concentration and signal reliability.
- A precomputed Streamlit investor journey: fund comparison, fact sheet, allocation lab and sentiment lens.
- A reproducible validation pack covering weights, date alignment, solver feasibility and sentiment lagging.

## Environment

The project uses Python 3.13 with the packages in `requirements.txt` and `requirements-dev.txt`.

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

`requirements-dev.txt` includes NLTK for the local sentiment build. The deployed app does not import NLTK or rerun VADER.

## Reproduce the results

From this folder:

```bash
python scripts/run_part_b.py
```

The script loads the hosted course data through the provided `src/data_access.py`, validates and cleans it, runs every walk-forward fund, scores news locally, and writes precomputed outputs under `results/`.

## Test

```bash
pytest
python scripts/check_handin.py
```

## Run the app

```bash
streamlit run streamlit_app.py
```

The app reads the committed CSV files in `results/`; it does not perform heavy modelling at runtime.

## Core assumptions

- Sample capped at 31 December 2023; OOS performance begins after the initial rolling window.
- Adjusted-close simple returns; monthly rebalancing on the first observed date.
- Equity and combined funds trade on the equity calendar and use 252-day annualisation; crypto-only funds use their daily calendar and 365-day annualisation.
- Long-only and fully invested; maximum target weight is 10% for equity/combined funds and 25% for crypto-only optimised funds.
- Zero risk-free rate and zero transaction cost in the baseline. Turnover is reported so this simplification can be assessed.
- Sharpe is annualised arithmetic mean return minus the zero risk-free rate, divided by annualised volatility; compounded annual return is reported separately.
- Sector sentiment equal-weights covered ticker-day scores. Missing ticker-days are omitted from polarity and separately reduce coverage.
- All sentiment used for a decision is lagged by at least one observed equity trading day.

This is an educational prototype, not personal financial advice. Past simulated results do not guarantee future performance.
