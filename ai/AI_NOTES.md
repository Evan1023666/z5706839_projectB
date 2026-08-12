# AI use statement

I used Codex as a coding, document-production and quality-assurance assistant. I set the product audience and value proposition, selected the conservative-investor framing, approved the portfolio assumptions, chose unequal news coverage as the main innovation, and made the final interpretation that sentiment should remain contextual because it did not improve the base fund in this sample.

The agent read the official brief, implemented and debugged Python modules, built the Streamlit interface, generated exhibits and report files, and ran automated checks. I directed it to document failures honestly. Important examples were the initial calendar-lag error, a failed Maximum-Sharpe solve and a numerical weight-cap violation; each produced a code change and a regression test.

I evaluated outputs using financial reasoning rather than accepting generated text or choosing the highest backtested return. My review emphasised drawdowns, concentration, turnover, signal availability and the needs of a time-poor novice investor. I also required the negative fusion result to remain in the product and report. The final wording and recommendations reflect those decisions, while the code and first drafts were AI-assisted.

Files `01_project_b_startup.md` to `04_app_report_and_qa.md` provide the task-level audit trail. `AGENTS.md` records the standing instructions used to keep later AI work aligned with the brief.

Before final packaging, the agent presented the main innovation, conservative interpretation and quantitative assumptions back to me for approval. I explicitly agreed that these choices represent my judgment. This sign-off is recorded in `04_app_report_and_qa.md`.
