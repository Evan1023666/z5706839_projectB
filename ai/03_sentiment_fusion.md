# Prompt log — sentiment index and structured/unstructured fusion

## My objective

I wanted the news feature to save a time-poor beginner from monitoring many headlines, but I did not want the app to present sentiment as a reliable trading instruction without evidence. Based on the Project A data audit, I focused the innovation on unequal news availability across sectors and tickers.

## Quantitative direction

I required the agent to:

1. preserve raw headline casing and punctuation for VADER;
2. deduplicate by ticker, date and title;
3. average headlines to ticker-day before equal-weighting covered ticker-days within a sector;
4. keep missing ticker-days out of the polarity mean and report coverage separately;
5. make each score tradable only on the next observed equity trading day; and
6. compare base Minimum Variance, a plain sentiment tilt and a coverage-aware tilt on identical dates.

My extension defines reliability as ticker coverage multiplied by one minus normalised headline-count concentration. This reduces the influence of a sector score when few tickers are represented or news is dominated by one name. I kept the same tilt strength for the plain and reliability-aware variants so the comparison isolates the reliability adjustment.

## AI contribution and error caught

The agent wrote the scoring, indexing and fusion code. Its first lag routine searched only dates containing news. A synthetic Monday-to-Tuesday test exposed the error: availability must follow the full equity calendar even if Tuesday has no headline. I required that correction.

A later fusion build produced a small position-cap violation after repeated clipping. I rejected approximate feasibility and required a capped proportional water-filling projection. A concentrated-vector test now checks the hard cap and full-investment constraints.

## Interpretation I approved

The coverage-aware variant improved on the plain sentiment tilt but both underperformed the base Minimum Variance portfolio. I kept this negative result because innovation is demonstrated by a defensible design and honest evaluation, not by selecting only a profitable backtest. SignalBlend therefore displays sentiment as contextual mood and evidence quality, not as a buy/sell recommendation.

