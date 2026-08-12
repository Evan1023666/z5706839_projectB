# Project B HD rubric audit

This audit maps the submitted evidence to the official Part B HD descriptors. It is a quality-control record, not a claim that a particular mark is guaranteed.

## Funds: Optimal Portfolios & OOS Backtest — 15%

- **HD requirement:** equity-only, crypto-only and combined funds across several methods; correct walk-forward OOS design; correct calendars and annualisation; fact sheets and all core exhibits.
- **Evidence:** 12 baseline funds across four methods; monthly past-only portfolio formation; 252/365 annualisation; position constraints; `performance_metrics.csv`; `fund_returns.csv`; `fund_weights.csv`; growth, drawdown, weights and risk-return exhibits; interactive fact sheet.
- **Student direction:** I chose the expanded 3 × 4 fund menu, monthly horizon, long-only caps and conservative drawdown framing.
- **QA:** build audit confirms estimation ends before rebalance and weights are feasible; unit tests challenge every optimiser.

## Sentiment Index & Fusion — 10%

- **HD requirement:** validated sector index over time and look-ahead-safe fusion whose effect is critically assessed.
- **Evidence:** VADER ticker-day/sector index, explicit missingness and coverage, one-equity-day lag, plain and coverage-aware fusion variants, before/after table and figure.
- **Student direction:** I required raw VADER text, equal weighting at ticker-day, missing observations separated from neutral scores, and retention of the negative result.
- **QA:** the full equity calendar fixed the initial lag error; validation reports zero timing violations.

## Innovation & Data-Driven Results — 30%

- **HD requirement:** distinctive implemented extension demonstrated with evidence; negative results count when carefully evaluated.
- **Evidence:** reliability = coverage × (1 − normalised headline concentration), applied to the same sentiment tilt and comparator dates; a custom four-step investor journey; custom visual system; 14 total funds.
- **Student direction:** I converted Project A's unequal-news-availability finding into the principal quantitative extension and required an unchanged baseline comparison.
- **Result:** reliability reduced the damage from the plain tilt but did not beat base Minimum Variance; the product accordingly treats sentiment as context rather than promotion.

## Streamlit App & Implementation — 15%

- **HD requirement:** reliable deployed app supporting comparison, fact sheets, allocation and sentiment with polished UX.
- **Evidence:** all four journeys exist, precomputed artifacts keep the app responsive, allocation inputs normalise transparently, crypto prompts support conservative users, and 15 automated tests include every page and interactive selectors.
- **Remaining external requirement:** public GitHub repository and live Streamlit URL must be completed and checked logged-out at hand-in.

## Interpretation, Reflection & Writing — 10%

- **HD requirement:** evidence-based account of what worked, what did not and why, plus three specific recommendations; every exhibit interpreted.
- **Evidence:** the report interprets return, volatility, drawdown, concentration, turnover, sentiment quality and fusion; Section 8 contains three product actions and remaining uncertainty.
- **Student direction:** I reject a universal “best” fund, give drawdown priority for conservative novices and keep sentiment informational pending stronger tests.
- **Student sign-off required:** I must read the final report and confirm that its first-person judgments match my own reasoning before submission.

## AI Workflow & Transparency — 20%

- **HD requirement:** own instructions and curated logs across the build, including prompts, outputs, corrections and reasons.
- **Evidence:** custom `AGENTS.md`; `AI_NOTES.md`; four task logs; this rubric audit. Logs disclose the calendar-lag bug, Maximum-Sharpe solver failure, bounded-projection violation and resulting tests.
- **Integrity boundary:** the records distinguish my specifications, review and decisions from the agent's implementation and drafting; they do not claim I manually wrote AI-assisted code.

## Overall residual risks

1. The marker determines the grade; this audit cannot guarantee HD.
2. The report's interpretation must receive the student's final personal review because the brief requires own writing and reasoning.
3. The deployment criterion cannot reach the top band until the repository is public at hand-in and the live app works for a logged-out marker.
