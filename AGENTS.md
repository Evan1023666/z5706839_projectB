# AGENTS.md - SignalBlend Project B Working Instructions

## Ownership and purpose

This is the working instruction file used by z5706839 with Codex for FINS5545 Project B. The product is **SignalBlend**, an educational investment decision-support app for young people who are new to investing, short on research time, and unsure how to compare investment directions and allocations.

The student owns the product decisions, quantitative assumptions, interpretation, acceptance criteria, and final submission. Codex may propose, implement, test, document, and revise work under the student's direction. AI assistance must be recorded honestly; never claim that the student manually authored AI-generated code or reasoning.

## Source of truth and boundaries

1. Read `PROJECT_BRIEF.md`, `SUBMISSION_CHECKLIST.md`, `context/`, and `docs/STUDENT_DEPLOY.md` before implementation.
2. The official brief and starter interfaces override these instructions if a conflict appears.
3. Work only inside `z5706839_projectB`. Do not inspect or copy another student's work.
4. Reuse only z5706839's own Project A decisions and verified derived findings. Do not modify Project A.
5. Do not edit the provided frozen `src/data_access.py` or the supplied `context/` files.
6. Do not commit raw data, secrets, caches, virtual environments, or local absolute paths.
7. Keep the GitHub repository private while building and make it public only when the student authorises the final hand-in step.

## Product continuity and student direction

Preserve these student decisions:

- Target user: a young novice investor with limited time to learn strategies, monitor risk, and follow news.
- Value proposition: reduce information-search and analysis cost, helping the user compare directions and allocations quickly.
- Risk communication: SignalBlend does not promise returns or provide personalised financial advice.
- Conservative-user interpretation: higher uncertainty or risk may justify a lower allocation to the relevant risky fund.
- Product language must remain understandable to a financially curious but non-technical user.

Ask the student to approve material choices that change the fund lineup, portfolio constraints, signal construction, innovation, or investor recommendations. Record those real decisions in the AI workflow pack.

## Implementation target

Build and compare equity-only, crypto-only, and combined equity-and-crypto funds across several meaningfully distinct methods. Expected baseline methods are equal weight, minimum variance, maximum Sharpe, and risk parity where technically sound. Also build a standalone equity-sector sentiment index and a look-ahead-safe sentiment-enhanced equity strategy.

The preferred deep innovation is a **coverage-aware sentiment reliability mechanism** extending the student's Project A audit. It should measure whether sector signals have enough ticker/news coverage, then flag, shrink, or withhold unreliable tilts. Compare this with a plain sentiment baseline. Do not assume either sentiment method improves returns; negative findings must be reported candidly.

## Quantitative and backtest rules

- Use adjusted close and compute returns within ticker before calendar alignment.
- Cap the dataset at 2023-12-31.
- State asset universe, return convention, estimation window, first live date, rebalance schedule, constraints, risk-free rate, transaction-cost assumption, and annualisation convention.
- Use a genuine walk-forward out-of-sample design. A decision at time `t` may use only information available before that decision.
- Rebalance monthly or less often, as required by the brief.
- Treat equity, crypto, and combined calendars explicitly. Do not silently apply 252-day annualisation to crypto-only results or 365-day annualisation to equity-only results.
- For combined funds trading on the equity calendar, document how weekend crypto information is incorporated and which annualisation factor is used.
- Scale optimisation inputs where needed so SciPy solvers do not falsely stop on tiny daily covariance values.
- Check solver status, feasibility, weight sums, bounds, NaNs, concentration, and meaningful differences between methods.
- Use deterministic procedures and record any fallback. Never silently replace an unsuccessful optimiser with equal weights.
- Report turnover and, if transaction costs are modelled, show both gross and net results under explicit assumptions.

Required validation includes independent checks of date alignment, no look-ahead, metric formulae, weight constraints, method differentiation, output schemas, and reproducibility.

## Sentiment rules

- Preserve raw headline text; VADER uses casing, punctuation, intensifiers, and negation.
- De-duplicate news on ticker, date, and title.
- Map non-trading-day headlines to the next equity trading day consistently with Project A.
- Score headlines, aggregate to ticker-day, then equal-weight ticker-day scores within sector.
- Explicitly distinguish no headline from a valid neutral score of zero.
- Choose and justify missing-headline treatment; expose coverage alongside polarity.
- Lag sentiment by at least one trading day. Saturday and Monday headlines aligned to Monday are first usable on Tuesday.
- Sentiment applies only to equities; crypto is price-only.
- Validate sector coverage, ticker participation, concentration, score distribution, false-neutral risk, and lag alignment.

## Fusion and innovation evaluation

- Preserve an untouched base fund for fair comparison.
- Define the transformation from sector sentiment to ticker/fund tilt with an equation or unambiguous algorithm.
- Apply bounded tilts and renormalise weights without violating portfolio constraints.
- The coverage-aware version must use only contemporaneously available coverage information.
- Compare base, plain sentiment, and coverage-aware sentiment over identical OOS dates.
- Evaluate return, volatility, Sharpe, maximum drawdown, turnover, concentration, and signal availability; add sensitivity or subperiod checks where useful.
- Interpret economic size and stability, not only the largest performance number.

## Required deliverables and reproducibility

`python scripts/run_part_b.py` must produce at least:

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/data/sector_sentiment_index.csv`
- `results/tables/performance_metrics.csv`

Also produce the brief's required exhibits: performance metrics, growth of $1, drawdown, weights over time, return-vs-risk or Sharpe comparison, sector sentiment over time, and fusion before-versus-after table and figure.

Every artifact must have stable field names, explicit dates and units, documented definitions, and validation before use. The app must load committed precomputed results and must not import NLTK, run VADER, or recompute heavy backtests at startup.

## Streamlit investor journey

The root entry point is `streamlit_app.py`. The app must let a user compare funds and methods, open a fact sheet, view growth/drawdown/risk/current holdings, set an allocation across funds, inspect sentiment with coverage/reliability evidence, and understand limitations for a conservative novice investor.

Use a coherent original design system, readable labels, accessible contrast, graceful missing-file handling, and plain-language explanations. Keep the app responsive on Streamlit Community Cloud.

## Report standards

- Author `report/report.docx` and export `report/report.pdf`.
- Respect the maximum 10 pages of written narrative and approximately 5,000 words, excluding appendix and references as permitted.
- Cover fund/backtest design, OOS fact sheets, sentiment, innovation, app journey, and critical reflection with three concrete recommendations.
- Make every exhibit self-contained: caption/title, labelled axes, units, sample period, legend, source/calculation note, and nearby interpretation.
- Use evidence-based English without inflated claims. The student reviews and rewrites final economic interpretation in their own words.
- Use UNSW Harvard referencing consistently; never fabricate references.

## AI workflow and student agency

Maintain curated English records in `ai/`. For each major stage record the student's real request (accurately translated if originally Chinese), what Codex proposed or implemented, the risk identified, checks performed, what the student accepted/changed/challenged/rejected and why, and any AI error with its correction.

Student agency must be demonstrated through genuine specification, method selection, challenge, validation requirements, interpretation, and final sign-off. Do not fabricate corrections merely to make the workflow appear more active.

## Coding and verification protocol

- Prefer small, documented functions and project-relative paths.
- Preserve user changes and use patch-based edits.
- Add tests for material modelling rules, especially time alignment and constraints.
- Do not claim a test, checker, app, deployment, or result passed unless actually run and inspected.
- Diagnose unexpected results before changing the model. Do not tune solely to maximise reported returns.
- Update README instructions and output definitions as implementation changes.
- Communicate with the student in clear Chinese; keep marker-facing content in professional English.

Before completion run and inspect:

```bash
python scripts/run_part_b.py
pytest
streamlit run streamlit_app.py
python scripts/check_handin.py
git status
```

Then inspect CSV schemas and sample rows, manually verify selected calculations, audit look-ahead and sentiment lag, visually inspect every figure and report page, test the app in a browser, inspect the final ZIP, and confirm the public repository and live URL from a logged-out browser at hand-in.
