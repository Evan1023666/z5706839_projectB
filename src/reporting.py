"""Self-contained Project B figures using the SignalBlend design system."""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


NAVY = "#17324D"
TEAL = "#087E8B"
GOLD = "#D9A441"
CRIMSON = "#B23A48"
SKY = "#5B8FF9"
GREY = "#6B7280"
GRID = "#D9E1E8"
PALETTE = [NAVY, TEAL, GOLD, CRIMSON, SKY, "#6A4C93", "#2A9D8F", "#E76F51"]


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#30363D",
            "axes.titleweight": "bold",
            "axes.titlecolor": "#111827",
            "axes.labelcolor": "#25313C",
            "xtick.color": "#4B5563",
            "ytick.color": "#4B5563",
            "legend.frameon": False,
            "savefig.dpi": 300,
        }
    )


def _finish(
    fig: plt.Figure,
    output_dir: Path,
    stem: str,
    *,
    title: str,
    note: str,
    units: str,
    sample: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    image = output_dir / f"{stem}.png"
    fig.savefig(image, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    (output_dir / f"{stem}.caption.md").write_text(
        f"# {title}\n\n## Note\n{note}\n\n## Sample\n{sample}\n\n"
        f"## Units\n{units}\n\n## Source\nFINS5545 hosted project data; calculations by the author.\n",
        encoding="utf-8",
    )
    return image


def plot_growth(fund_returns: pd.DataFrame, output_dir: Path) -> Path:
    """Compare growth of one dollar for all baseline funds."""
    _style()
    data = fund_returns.loc[~fund_returns["method"].str.contains("sentiment")].copy()
    fig, axes = plt.subplots(3, 1, figsize=(8.2, 8.5), sharex=False, constrained_layout=True)
    for ax, (family, group) in zip(axes, data.groupby("family", sort=False), strict=True):
        for color, (fund, series) in zip(PALETTE, group.groupby("fund"), strict=False):
            ax.plot(series["date"], series["growth_of_one"], label=series["method"].iloc[0].replace("_", " ").title(), color=color, lw=1.5)
        ax.set_title(f"{family} funds", loc="left")
        ax.set_ylabel("Value of $1")
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.legend(ncol=4, fontsize=8, loc="upper left")
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[-1].set_xlabel("Out-of-sample date")
    sample = f"{data['date'].min():%Y-%m-%d} to {data['date'].max():%Y-%m-%d}"
    return _finish(fig, output_dir, "growth_of_one_all_funds", title="Out-of-sample growth of $1 by fund and method", note="Each line compounds realised walk-forward returns. Weights at each monthly rebalance use only the preceding estimation window.", units="Portfolio value in dollars; initial value = $1.", sample=sample)


def plot_drawdown(fund_returns: pd.DataFrame, output_dir: Path) -> Path:
    """Show drawdowns for the combined funds."""
    _style()
    data = fund_returns.loc[fund_returns["family"].eq("Combined")]
    fig, ax = plt.subplots(figsize=(8.2, 4.3), constrained_layout=True)
    for color, (_, series) in zip(PALETTE, data.groupby("fund"), strict=False):
        ax.plot(series["date"], series["drawdown"], label=series["method"].iloc[0].replace("_", " ").title(), color=color, lw=1.4)
    ax.axhline(0, color="#333333", linewidth=0.7)
    ax.set_title("Combined-fund drawdowns", loc="left")
    ax.set_xlabel("Out-of-sample date")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.legend(ncol=2, fontsize=8)
    sample = f"{data['date'].min():%Y-%m-%d} to {data['date'].max():%Y-%m-%d}"
    return _finish(fig, output_dir, "drawdown_combined_funds", title="Out-of-sample drawdowns for combined funds", note="Drawdown is the percentage fall from each fund's prior high-water mark; zero indicates a new peak.", units="Percent below prior portfolio peak.", sample=sample)


def plot_risk_return(metrics: pd.DataFrame, output_dir: Path) -> Path:
    """Display annualised risk and return across baseline funds."""
    _style()
    data = metrics.loc[~metrics["method"].str.contains("sentiment")].copy()
    fig, ax = plt.subplots(figsize=(8.2, 4.8), constrained_layout=True)
    family_colors = {"Equity": NAVY, "Crypto": GOLD, "Combined": TEAL}
    abbreviations = {"equal_weight": "EW", "min_variance": "MV", "max_sharpe": "MS", "risk_parity": "RP"}
    offsets = {"Equity": (5, -9), "Combined": (5, 4), "Crypto": (5, 4)}
    for family, group in data.groupby("family"):
        ax.scatter(group["annualised_volatility"], group["annualised_return"], s=65, color=family_colors[family], label=family, alpha=0.9)
        for row in group.itertuples():
            ax.annotate(abbreviations[row.method], (row.annualised_volatility, row.annualised_return), xytext=offsets[family], textcoords="offset points", fontsize=7, fontweight="bold")
    ax.axhline(0, color="#555555", lw=0.7)
    ax.set_title("Risk-return comparison across investable funds", loc="left")
    ax.set_xlabel("Annualised volatility")
    ax.set_ylabel("Annualised compounded return")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(color=GRID, linewidth=0.6)
    ax.legend(title="Asset family", loc="upper left")
    ax.text(0.55, 0.08, "Methods: EW = Equal Weight, MV = Minimum Variance,\nMS = Maximum Sharpe, RP = Risk Parity", transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5, color=GREY)
    sample = f"{data['start_date'].min()} to {data['end_date'].max()}"
    return _finish(fig, output_dir, "risk_return_all_funds", title="Annualised return versus volatility", note="Points use each fund's realised out-of-sample daily returns. Method labels identify the portfolio rule; colours identify the asset family.", units="Annualised return and volatility in percent.", sample=sample)


def plot_weights(fund_weights: pd.DataFrame, output_dir: Path) -> Path:
    """Show method-level concentration and asset-class mix over time."""
    _style()
    combined = fund_weights.loc[fund_weights["family"].eq("Combined")].copy()
    combined["asset_class"] = np.where(combined["ticker"].str.endswith("-USD"), "Crypto", "Equity")
    mix = combined.groupby(["rebalance_date", "method", "asset_class"], as_index=False)["weight"].sum()
    methods = list(mix["method"].drop_duplicates())
    fig, axes = plt.subplots(len(methods), 1, figsize=(8.2, 2.15 * len(methods)), sharex=True, constrained_layout=True)
    axes = np.atleast_1d(axes)
    for ax, method in zip(axes, methods, strict=True):
        wide = mix.loc[mix["method"].eq(method)].pivot(index="rebalance_date", columns="asset_class", values="weight").fillna(0)
        ax.stackplot(wide.index, wide.get("Equity", 0), wide.get("Crypto", 0), labels=["Equity", "Crypto"], colors=[NAVY, GOLD], alpha=0.88)
        ax.set_title(method.replace("_", " ").title(), loc="left", fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_ylabel("Weight")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        ax.grid(axis="y", color=GRID, linewidth=0.5)
    axes[0].legend(ncol=2, loc="upper right", fontsize=8)
    axes[-1].set_xlabel("Rebalance date")
    sample = f"{mix['rebalance_date'].min():%Y-%m-%d} to {mix['rebalance_date'].max():%Y-%m-%d}"
    return _finish(fig, output_dir, "combined_weights_over_time", title="Combined-fund asset-class weights over time", note="Ticker target weights are aggregated into equity and crypto at each monthly rebalance. Between rebalances the chart shows target, not drifted, weights.", units="Share of target portfolio weight in percent.", sample=sample)


def plot_sector_sentiment(index: pd.DataFrame, output_dir: Path) -> Path:
    """Plot a readable rolling sector sentiment comparison."""
    _style()
    data = index.copy().sort_values("trading_date")
    data["sentiment_21d"] = data.groupby("sector")["sentiment"].transform(lambda s: s.rolling(21, min_periods=5).mean())
    sectors = sorted(data["sector"].unique())
    fig, axes = plt.subplots(5, 2, figsize=(8.2, 9.3), sharex=True, sharey=True, constrained_layout=True)
    for ax, color, sector in zip(axes.flat, PALETTE + ["#8D99AE", "#43AA8B"], sectors, strict=True):
        group = data.loc[data["sector"].eq(sector)]
        ax.plot(group["trading_date"], group["sentiment_21d"], color=color, lw=1.1)
        ax.axhline(0, color="#555555", lw=0.6)
        ax.set_title(sector, loc="left", fontsize=9.5)
        ax.grid(axis="y", color=GRID, linewidth=0.5)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("Equity-sector headline sentiment (21-trading-day average)", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.supylabel("VADER compound sentiment")
    fig.supxlabel("Headline-aligned equity trading date")
    sample = f"{data['trading_date'].min():%Y-%m-%d} to {data['trading_date'].max():%Y-%m-%d}"
    return _finish(fig, output_dir, "sector_sentiment_index", title="Equity-sector headline sentiment over time", note="Daily sector sentiment equal-weights covered ticker-day scores; missing ticker-days are omitted rather than treated as neutral. The chart smooths the daily index with a 21-trading-day rolling mean for readability.", units="VADER compound score from -1 to +1.", sample=sample)


def plot_fusion(fund_returns: pd.DataFrame, output_dir: Path) -> Path:
    """Compare base, plain and coverage-aware equity minimum-variance funds."""
    _style()
    names = ["Equity Minimum Variance", "Equity Min Variance + Sentiment", "Equity Min Variance + Coverage-Aware Sentiment"]
    data = fund_returns.loc[fund_returns["fund"].isin(names)]
    fig, (ax_growth, ax_active) = plt.subplots(2, 1, figsize=(8.2, 6.7), sharex=True, constrained_layout=True)
    for color, name in zip([NAVY, CRIMSON, TEAL], names, strict=True):
        group = data.loc[data["fund"].eq(name)]
        ax_growth.plot(group["date"], group["growth_of_one"], label=name, color=color, lw=1.6)
    pivot = data.pivot(index="date", columns="fund", values="return").dropna()
    for color, name in zip([CRIMSON, TEAL], names[1:], strict=True):
        active = (pivot[name] - pivot[names[0]]).rolling(63, min_periods=21).mean() * 252
        ax_active.plot(active.index, active, label=name.replace("Equity Min Variance + ", ""), color=color, lw=1.3)
    ax_growth.set_title("Base versus sentiment-enhanced equity fund", loc="left")
    ax_growth.set_ylabel("Value of $1")
    ax_growth.grid(axis="y", color=GRID, linewidth=0.6)
    ax_growth.legend(fontsize=8)
    ax_active.axhline(0, color="#333333", lw=0.7)
    ax_active.set_title("63-day rolling annualised active return", loc="left")
    ax_active.set_xlabel("Out-of-sample date")
    ax_active.set_ylabel("Active return")
    ax_active.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax_active.grid(axis="y", color=GRID, linewidth=0.6)
    ax_active.legend(fontsize=8)
    sample = f"{data['date'].min():%Y-%m-%d} to {data['date'].max():%Y-%m-%d}"
    return _finish(fig, output_dir, "fusion_before_after", title="Sentiment fusion before-versus-after comparison", note="The top panel compounds identical-date OOS returns. The lower panel subtracts the base minimum-variance return from each sentiment version and smooths the difference over 63 trading days.", units="Growth in dollars; active return annualised in percent.", sample=sample)
