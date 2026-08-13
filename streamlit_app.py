"""SignalBlend: precomputed systematic funds and sentiment analytics."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULT_PATHS = {
    "returns": RESULTS / "data" / "fund_returns.csv",
    "weights": RESULTS / "data" / "fund_weights.csv",
    "sentiment": RESULTS / "data" / "sector_sentiment_index.csv",
    "metrics": RESULTS / "tables" / "performance_metrics.csv",
}
NAVY = "#17324D"
TEAL = "#087E8B"
GOLD = "#D9A441"
CRIMSON = "#B23A48"
LIGHT = "#F3F6F8"

st.set_page_config(
    page_title="SignalBlend | Systematic Fund Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      .stApp {{background: #FBFCFD; color: #17212B;}}
      [data-testid="stSidebar"] {{background: {NAVY};}}
      [data-testid="stSidebar"] * {{color: white;}}
      .brand-kicker {{letter-spacing:.13em; text-transform:uppercase; color:{TEAL}; font-weight:700; font-size:.78rem;}}
      .hero {{background:linear-gradient(120deg,{NAVY},#245276); color:white; padding:1.7rem 2rem; border-radius:18px; margin-bottom:1rem;}}
      .hero h1 {{margin:0 0 .35rem; font-size:2.25rem;}}
      .hero p {{margin:0; color:#D9E5EC; max-width:760px;}}
      .note-card {{background:{LIGHT}; border-left:4px solid {TEAL}; padding:.85rem 1rem; border-radius:8px;}}
      .risk-card {{background:#FFF8E8; border-left:4px solid {GOLD}; padding:.85rem 1rem; border-radius:8px;}}
      div[data-testid="stMetric"] {{background:white; border:1px solid #E1E7EC; border-radius:12px; padding:.7rem .85rem;}}
      h2, h3 {{color:{NAVY};}}
    </style>
    """,
    unsafe_allow_html=True,
)


def results_fingerprint() -> str:
    """Return a content key so deployments cannot reuse stale result frames."""
    digest = hashlib.sha256()
    for name, path in sorted(RESULT_PATHS.items()):
        digest.update(name.encode("utf-8"))
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()


@st.cache_data(show_spinner=False)
def load_results(artifact_version: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load committed precomputed artifacts, keyed by their content hash."""
    del artifact_version  # Included solely in Streamlit's cache key.
    missing = [str(path.relative_to(ROOT)) for path in RESULT_PATHS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Precomputed result files are missing: " + ", ".join(missing)
            + ". Run python scripts/run_part_b.py locally and commit results/."
        )
    returns = pd.read_csv(RESULT_PATHS["returns"], parse_dates=["date"])
    weights = pd.read_csv(RESULT_PATHS["weights"], parse_dates=["rebalance_date"])
    sentiment = pd.read_csv(RESULT_PATHS["sentiment"], parse_dates=["trading_date", "signal_date"])
    metrics = pd.read_csv(RESULT_PATHS["metrics"])
    return returns, weights, sentiment, metrics


def percent(value: float) -> str:
    return f"{value:.1%}"


def clean_label(value: str) -> str:
    return value.replace("_", " ").title()


def base_layout(fig: go.Figure, *, y_title: str, height: int = 440) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=15, r=15, t=45, b=15),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", color="#25313C"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(title=None, showgrid=False),
        yaxis=dict(title=y_title, gridcolor="#E7EDF1", zerolinecolor="#9AA8B2"),
        hovermode="x unified",
    )
    return fig


try:
    fund_returns, fund_weights, sector_sentiment, performance = load_results(results_fingerprint())
except Exception as exc:
    st.error("SignalBlend cannot load its precomputed results.")
    st.code(str(exc))
    st.stop()

baseline = performance.loc[~performance["method"].str.contains("sentiment")].copy()
fund_names = performance["fund"].tolist()

with st.sidebar:
    st.markdown("## ◈ SignalBlend")
    st.caption("SYSTEMATIC FUND STUDIO")
    page = st.radio(
        "Investor journey",
        ["Fund comparison", "Fund fact sheet", "Allocation lab", "Sentiment lens"],
    )
    st.markdown("---")
    st.markdown("**Model window** 2020–2023")
    st.markdown("**Live OOS period** 2021–2023")
    st.markdown("**Rebalance** Monthly")
    st.markdown("**Risk-free rate** 0%")
    st.markdown("**Trading costs** 0 bps baseline")
    st.markdown("---")
    st.caption("Educational analytics only. Not personal financial advice. Past simulated performance does not predict future results.")

st.markdown(
    """
    <div class="hero">
      <div class="brand-kicker" style="color:#75D3DA">FROM DATA TO A DECISION YOU CAN EXPLAIN</div>
      <h1>SignalBlend</h1>
      <p>Compare rules-based equity, crypto and blended funds, then inspect whether headline sentiment adds useful evidence—or only extra noise.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


if page == "Fund comparison":
    st.markdown('<div class="brand-kicker">STEP 1 · COMPARE</div>', unsafe_allow_html=True)
    st.header("Choose the trade-off, not the highest return")
    st.write("Each point is a distinct investable fund: an asset family combined with one portfolio rule. All results are walk-forward and out of sample.")

    col1, col2, col3 = st.columns(3)
    best_sharpe = baseline.loc[baseline["sharpe_ratio"].idxmax()]
    lowest_risk = baseline.loc[baseline["annualised_volatility"].idxmin()]
    shallowest = baseline.loc[baseline["maximum_drawdown"].idxmax()]
    col1.metric("Highest Sharpe", f"{best_sharpe.sharpe_ratio:.2f}", best_sharpe.fund)
    col2.metric("Lowest annual risk", percent(lowest_risk.annualised_volatility), lowest_risk.fund)
    col3.metric("Shallowest max drawdown", percent(shallowest.maximum_drawdown), shallowest.fund)

    family_filter = st.multiselect("Asset families", ["Equity", "Crypto", "Combined"], default=["Equity", "Crypto", "Combined"])
    view = baseline.loc[baseline["family"].isin(family_filter)]
    fig = px.scatter(
        view,
        x="annualised_volatility",
        y="annualised_return",
        color="family",
        symbol="method",
        hover_name="fund",
        hover_data={"sharpe_ratio": ":.2f", "maximum_drawdown": ":.1%", "annualised_volatility": ":.1%", "annualised_return": ":.1%", "family": False, "method": False},
        color_discrete_map={"Equity": NAVY, "Crypto": GOLD, "Combined": TEAL},
    )
    fig.update_traces(marker=dict(size=13, line=dict(width=1, color="white")))
    fig.update_xaxes(tickformat=".0%")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(base_layout(fig, y_title="Annualised compounded return"), width="stretch")

    display = view[["fund", "annualised_return", "annualised_volatility", "sharpe_ratio", "maximum_drawdown", "mean_one_way_turnover"]].copy()
    st.dataframe(
        display.style.format({"annualised_return": "{:.1%}", "annualised_volatility": "{:.1%}", "sharpe_ratio": "{:.2f}", "maximum_drawdown": "{:.1%}", "mean_one_way_turnover": "{:.1%}"}),
        width="stretch",
        hide_index=True,
    )
    st.markdown('<div class="risk-card"><b>Conservative reading:</b> the lowest-volatility fund reduced risk in this sample, but it still lost money from peak to trough. Crypto funds produced much larger gains in some cases while also suffering drawdowns above 70%; return alone is not a risk label.</div>', unsafe_allow_html=True)


elif page == "Fund fact sheet":
    st.markdown('<div class="brand-kicker">STEP 2 · INSPECT</div>', unsafe_allow_html=True)
    st.header("Open a fund fact sheet")
    selected = st.selectbox("Fund", fund_names, index=fund_names.index("Combined Risk Parity") if "Combined Risk Parity" in fund_names else 0)
    metric = performance.loc[performance["fund"].eq(selected)].iloc[0]
    series = fund_returns.loc[fund_returns["fund"].eq(selected)].sort_values("date")
    weights = fund_weights.loc[fund_weights["fund"].eq(selected)]
    latest_date = weights["rebalance_date"].max()
    latest = weights.loc[weights["rebalance_date"].eq(latest_date)].sort_values("weight", ascending=False)

    cols = st.columns(5)
    cols[0].metric("Annual return", percent(metric.annualised_return))
    cols[1].metric("Annual risk", percent(metric.annualised_volatility))
    cols[2].metric("Sharpe", f"{metric.sharpe_ratio:.2f}")
    cols[3].metric("Max drawdown", percent(metric.maximum_drawdown))
    cols[4].metric("Terminal $1", f"${metric.terminal_growth_of_one:.2f}")

    left, right = st.columns([1.8, 1])
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series["date"], y=series["growth_of_one"], name="Growth of $1", line=dict(color=TEAL, width=2.2)))
        st.plotly_chart(base_layout(fig, y_title="Portfolio value ($)"), width="stretch")
        dd = go.Figure(go.Scatter(x=series["date"], y=series["drawdown"], fill="tozeroy", name="Drawdown", line=dict(color=CRIMSON)))
        dd.update_yaxes(tickformat=".0%")
        st.plotly_chart(base_layout(dd, y_title="Drawdown", height=330), width="stretch")
    with right:
        st.subheader("Current target holdings")
        st.caption(f"Latest rebalance: {latest_date:%d %b %Y}. Target weights, not live drifted holdings.")
        top = latest.head(12)
        bars = px.bar(top.sort_values("weight"), x="weight", y="ticker", orientation="h", color_discrete_sequence=[NAVY])
        bars.update_xaxes(tickformat=".0%")
        bars.update_layout(height=470, margin=dict(l=10, r=10, t=15, b=10), showlegend=False, plot_bgcolor="white", paper_bgcolor="white", xaxis_title="Target weight", yaxis_title=None)
        st.plotly_chart(bars, width="stretch")
        st.caption(f"{metric.latest_effective_holdings:.0f} effective holdings; latest largest position {metric.latest_max_weight:.1%}.")
    st.markdown(f'<div class="note-card"><b>Method:</b> {clean_label(metric.method)} uses a {int(metric.lookback_observations)}-observation rolling estimation window and rebalances on the first observed day of each month. Sharpe is annualised arithmetic mean return divided by annualised volatility, using a 0% risk-free rate; the baseline excludes transaction costs.</div>', unsafe_allow_html=True)


elif page == "Allocation lab":
    st.markdown('<div class="brand-kicker">STEP 3 · ALLOCATE</div>', unsafe_allow_html=True)
    st.header("Blend funds and see the historical consequence")
    st.write("Select up to four funds. Slider inputs are automatically normalised to 100%; this is an exploration tool, not a recommendation engine.")
    defaults = ["Equity Minimum Variance", "Combined Risk Parity", "Crypto Minimum Variance"]
    defaults = [name for name in defaults if name in fund_names]
    selected = st.multiselect("Funds", fund_names, default=defaults, max_selections=4)
    if not selected:
        st.info("Select at least one fund to build an allocation.")
    else:
        slider_cols = st.columns(len(selected))
        raw = []
        default_input = max(5, 5 * round((100 / len(selected)) / 5))
        for i, name in enumerate(selected):
            raw.append(slider_cols[i].slider(name, 0, 100, default_input, 5, key=f"allocation_{name}"))
        if sum(raw) == 0:
            st.warning("At least one allocation input must be above zero.")
        else:
            allocation = np.asarray(raw, dtype=float) / sum(raw)
            allocation_table = pd.DataFrame({"fund": selected, "normalised_weight": allocation})
            st.dataframe(allocation_table.style.format({"normalised_weight": "{:.1%}"}), hide_index=True, width="stretch")
            pivot = fund_returns.loc[fund_returns["fund"].isin(selected)].pivot(index="date", columns="fund", values="return").dropna()
            portfolio_return = pivot[selected].to_numpy() @ allocation
            growth = pd.Series(1 + portfolio_return, index=pivot.index).cumprod()
            drawdown = growth / growth.cummax() - 1
            selected_families = performance.set_index("fund").loc[selected, "family"]
            periods = 365 if selected_families.eq("Crypto").all() else 252
            annual_return = growth.iloc[-1] ** (periods / len(growth)) - 1
            annual_vol = pd.Series(portfolio_return).std(ddof=1) * np.sqrt(periods)
            annual_mean_return = float(np.mean(portfolio_return) * periods)
            sharpe = annual_mean_return / annual_vol if annual_vol > 0 else np.nan
            cols = st.columns(4)
            cols[0].metric("Annual return", percent(annual_return))
            cols[1].metric("Annual risk", percent(annual_vol))
            cols[2].metric("Sharpe", f"{sharpe:.2f}")
            cols[3].metric("Max drawdown", percent(drawdown.min()))
            fig = go.Figure(go.Scatter(x=growth.index, y=growth, line=dict(color=TEAL, width=2.3), name="Your blend"))
            st.plotly_chart(base_layout(fig, y_title="Value of $1"), width="stretch")
            st.caption(f"Metrics use {periods}-observation annualisation on the common return dates. Sharpe uses annualised arithmetic mean return and a 0% risk-free rate.")
            crypto_share = sum(weight for name, weight in zip(selected, allocation, strict=True) if "Crypto" in name)
            if crypto_share > 0.20:
                st.markdown(f'<div class="risk-card"><b>Risk prompt:</b> {crypto_share:.0%} of this fund-level allocation is in a crypto-only fund before considering any crypto held inside combined funds. A conservative novice investor may lower this share because the crypto-only fact sheets show substantially deeper drawdowns.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="note-card"><b>Next check:</b> open each selected fact sheet. Fund-level diversification does not guarantee asset-level diversification because different funds can hold the same securities.</div>', unsafe_allow_html=True)


else:
    st.markdown('<div class="brand-kicker">STEP 4 · QUESTION THE SIGNAL</div>', unsafe_allow_html=True)
    st.header("Sentiment lens: mood plus evidence quality")
    st.write("The daily index equal-weights ticker-day VADER scores within each equity sector. Tickers with no headline are not set to zero; their absence lowers the reported coverage.")
    sector = st.selectbox("Equity sector", sorted(sector_sentiment["sector"].unique()))
    data = sector_sentiment.loc[sector_sentiment["sector"].eq(sector)].sort_values("trading_date").copy()
    data["sentiment_21d"] = data["sentiment"].rolling(21, min_periods=5).mean()
    data["coverage_21d"] = data["coverage_rate"].rolling(21, min_periods=5).mean()
    data["reliability_21d"] = data["reliability"].rolling(21, min_periods=5).mean()
    latest = data.dropna(subset=["sentiment_21d"]).iloc[-1]
    cols = st.columns(4)
    cols[0].metric("Latest smoothed mood", f"{latest.sentiment_21d:+.3f}")
    cols[1].metric("Average ticker coverage", percent(data.coverage_rate.mean()))
    cols[2].metric("Average reliability", percent(data.reliability.mean()))
    cols[3].metric("Covered neutral share", percent(data.neutral_share_covered.mean()))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["trading_date"], y=data["sentiment_21d"], name="21-day sentiment", line=dict(color=TEAL, width=2)))
    fig.add_hline(y=0, line_color="#687680", line_width=1)
    st.plotly_chart(base_layout(fig, y_title="VADER compound score"), width="stretch")
    quality = go.Figure()
    quality.add_trace(go.Scatter(x=data["trading_date"], y=data["coverage_21d"], name="Ticker coverage", line=dict(color=GOLD, width=1.8)))
    quality.add_trace(go.Scatter(x=data["trading_date"], y=data["reliability_21d"], name="Coverage-aware reliability", line=dict(color=NAVY, width=1.8)))
    quality.update_yaxes(tickformat=".0%", range=[0, 1.05])
    st.plotly_chart(base_layout(quality, y_title="Evidence availability", height=350), width="stretch")

    st.subheader("Did sentiment improve the fund?")
    fusion_names = ["Equity Minimum Variance", "Equity Min Variance + Sentiment", "Equity Min Variance + Coverage-Aware Sentiment"]
    fusion_table = performance.loc[performance["fund"].isin(fusion_names), ["fund", "annualised_return", "annualised_volatility", "sharpe_ratio", "maximum_drawdown", "mean_one_way_turnover"]]
    st.dataframe(fusion_table.style.format({"annualised_return": "{:.1%}", "annualised_volatility": "{:.1%}", "sharpe_ratio": "{:.2f}", "maximum_drawdown": "{:.1%}", "mean_one_way_turnover": "{:.1%}"}), hide_index=True, width="stretch")
    st.markdown('<div class="risk-card"><b>Evidence, not promotion:</b> in this sample, both sentiment tilts reduced the base minimum-variance fund’s return and Sharpe ratio. Reliability weighting softened the damage relative to the plain tilt, but did not create outperformance. Headline mood is therefore shown as context, not a buy/sell instruction.</div>', unsafe_allow_html=True)
    with st.expander("How SignalBlend prevents look-ahead"):
        st.write("A headline is aligned to the same or next equity trading day. Its sector score becomes usable only on the following observed equity trading day. A Saturday or Monday headline aligned to Monday can first affect Tuesday’s decision. Reliability uses coverage and concentration known for that same already-observed signal day.")

st.markdown("---")
st.caption("SignalBlend prototype · FINS5545 Project B · Data: 50 US equities, 10 cryptocurrencies and equity news headlines, 2020–2023. OOS results begin after the initial estimation window. Educational use only.")
