# Prompt log — app, report and final quality assurance

## My product direction

I asked the agent to turn the modelling evidence into a low-friction journey for young novice investors. I retained four steps: compare funds, inspect a fact sheet, experiment with a fund allocation, and question the sentiment signal. I specifically required a conservative-risk prompt when a user selects a material crypto-only allocation.

## AI contribution

The agent implemented a custom Streamlit interface and generated the Word/PDF report from verified CSV artifacts. The deployed app reads committed results only; it does not download raw data, run VADER or recompute backtests. The agent also created a consistent navy/teal/gold visual system, captions, limitations and investor-facing explanations.

## My review criteria

I required the report to remain evidence-led and understandable rather than sounding artificially academic. I checked that:

- each key result is interpreted for the target investor;
- the coverage-aware method is presented as an evaluated innovation, not guaranteed alpha;
- drawdown and turnover qualify return claims;
- the report gives three concrete recommendations;
- references use the UNSW Harvard format and are fully left aligned; and
- the app includes educational-use and past-performance warnings.

I also asked for AI records in English and for my genuine role in quantitative direction, validation and interpretation to be explicit. I did not claim to have manually written AI-assisted code.

## Verification

The final QA includes deterministic model tests, timing and constraint tests, checks of all required CSV schemas, four Streamlit page renders plus interactive selection tests, report rendering and page inspection, and the starter hand-in checker. Any failed check was corrected and rerun rather than removed.

The final browser inspection also exposed a non-fatal slider warning: the three-fund allocation defaults were 33 while the control advanced in steps of five. I required a valid nearest-step default rather than ignoring the console warning. The app now uses step-compatible defaults and a regression test checks every allocation slider.

## Final student sign-off

After the HD-rubric audit, Codex asked me to confirm three judgments rather than infer them: (1) coverage quality is my principal innovation and the negative sentiment result should remain; (2) the conservative product stance should avoid naming one universally best fund and should prioritise drawdown, volatility and crypto share; and (3) the monthly rebalance, 10% equity/combined cap, 25% crypto cap, zero risk-free rate and zero-cost baseline with disclosed turnover are the modelling choices I reviewed and adopted. I replied “同意” (“Agreed”). The report's first-person decision statements therefore reflect my explicit sign-off.
