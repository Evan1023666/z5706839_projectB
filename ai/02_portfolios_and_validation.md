# Prompt log — portfolio design and validation

## My direction

I asked the agent to continue Project B using SignalBlend's target user: a young novice investor who has limited time to research strategies and news. I required the quantitative product to make risk visible, and I stated that a conservative investor may lower the risky allocation rather than chase the highest return.

## Decisions I retained

- I selected a broad product menu rather than the minimum two combined funds: equity-only, crypto-only and combined families, each using Equal Weight, Minimum Variance, Maximum Sharpe and Risk Parity.
- I required walk-forward results because an in-sample optimum would not be appropriate evidence for a client.
- I accepted monthly rebalancing, a rolling 252-observation equity/combined window, a 365-observation crypto window, long-only constraints, 10% equity/combined caps and 25% crypto caps.
- I accepted a zero risk-free rate and zero-cost baseline only when turnover was also reported so implementation friction was not hidden.

## AI contribution

The agent implemented deterministic optimisation, walk-forward backtests, metrics, weights and audit files. It proposed automated constraint and timing tests and created the initial result figures.

## My checking and intervention

I required failed optimisation to stop or be handled explicitly, not silently replaced with Equal Weight. When Maximum Sharpe failed at one combined-fund rebalance, the agent introduced deterministic multi-start optimisation and retained only feasible successful solutions. I also required direct tests of full investment, non-negative weights, caps and estimation-date ordering.

I interpreted the outputs rather than choosing a winner only from return. In particular, I treated the 70%–82% crypto drawdowns as material for the target user, while recognising that the lower-volatility funds still had meaningful peak-to-trough losses.

## Outcome

The final build contains 12 baseline funds and two sentiment variants. Every rebalance uses data ending before the live date; weights sum to one, remain non-negative and respect their caps. The app and report therefore use the same validated precomputed evidence.

