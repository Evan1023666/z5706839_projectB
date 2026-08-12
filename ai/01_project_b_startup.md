# Prompt log - Project B startup, requirements and workflow

## What I wanted

I wanted Codex to restore the decisions made during Project A, read the new Project B starter and teacher documents, and begin Project B without losing the product direction or introducing methodological errors.

## Prompt(s)

Translated from my Chinese instructions:

> First review our previous conversation and `agent.md`. I am sending the project requirements again. Now start Project B.

> Follow the teacher's folder instructions. Part B must also become a GitHub repository and a deployed Streamlit app. Keep the repository private during development and make it public only at hand-in.

> I have moved the folder. Continue. I give you permission to handle it.

## What the assistant produced

Codex reread the independent Project A progress record and Project B working protocol, reviewed both supplied PDFs, and inspected the full starter structure, brief, checklist, deployment guide, code stubs, tests, requirements and hand-in checker. It confirmed the official folder as `z5706839_projectB`, checked the existing PyCharm environment, and drafted a project-local instruction file covering product continuity, walk-forward backtesting, sentiment lagging, coverage-aware innovation, app requirements and verification.

## What was wrong or risky

The original Codex task initially lacked write permission to the formal course folder. Several attempts to copy or edit the folder failed because the approval service disconnected. It would have been risky to build inside the Downloads template or the unrelated Codex notes folder because that would violate the teacher's one-folder workflow and could omit files from hand-in.

The untouched smoke test also failed to load hosted data because the earlier sandbox could not resolve the download hosts. This was recorded as an environment/network failure, not misrepresented as a modelling bug.

## What I changed and why

I manually moved and renamed the starter to `fins-agent/fins2026/z5706839_projectB`, then explicitly gave Codex permission to work in it. I retained the Project A product decisions: SignalBlend targets young novice investors with little research time, reduces information-search cost, and explains why a conservative user may lower risky allocations. I also directed the workflow to preserve my role in quantitative choices, validation and final interpretation rather than claiming that I manually wrote all AI-assisted code.

## Decision

Accepted the requirements audit and the coverage-aware sentiment reliability direction as the primary innovation, subject to empirical validation. The official brief remains the source of truth, and the repository will stay private during development.

## First test-driven correction

Codex's first sentiment-index implementation searched for the next usable date only among dates that also had scored news. My synthetic test required a Monday headline to become usable on Tuesday even if Tuesday had no news, and the test failed because the code returned a missing signal date. I required the signal lag to use the complete equity trading calendar instead. Codex changed the function to accept that full calendar, after which this rule could be tested directly. This correction prevents signal availability from depending incorrectly on future news coverage.

The first full-data run also stopped at a Combined Maximum-Sharpe rebalance because SLSQP reported a positive directional derivative. I did not allow an unreported equal-weight fallback. Codex changed the non-convex maximum-Sharpe solver to use deterministic multi-start optimisation and select only a successful, feasible candidate; it still raises an error if every start fails. A repeatability test was added so this robustness change does not make the pipeline stochastic.

The next full-data run completed all 12 baseline funds and VADER scoring, but a sentiment-tilted rebalance exposed a numerical upper-bound violation in the repeated clipping routine. I required the 10% equity cap to remain a hard constraint. Codex replaced clipping with a capped proportional water-filling projection solved by bisection and added a concentrated-input test. The pipeline therefore stops rather than publishing infeasible sentiment weights.
