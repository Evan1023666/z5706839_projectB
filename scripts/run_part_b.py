"""Reproduce all SignalBlend Project B data, tables and figures.

Run from the project root with the course environment:

    python scripts/run_part_b.py
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import etl, features, fusion, portfolios, reporting, sentiment  # noqa: E402


DATA_DIR = ROOT / "results" / "data"
TABLE_DIR = ROOT / "results" / "tables"
FIGURE_DIR = ROOT / "results" / "figures"

FAMILY_LABELS = {
    "Equity": "Equity",
    "Crypto": "Crypto",
    "Combined": "Combined",
}
METHOD_LABELS = {
    "equal_weight": "Equal Weight",
    "min_variance": "Minimum Variance",
    "max_sharpe": "Maximum Sharpe",
    "risk_parity": "Risk Parity",
}


def write_csv(frame: pd.DataFrame, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    print(f"wrote {path.relative_to(ROOT)} ({len(frame):,} rows)")


def fund_name(family: str, method: str) -> str:
    return f"{FAMILY_LABELS[family]} {METHOD_LABELS[method]}"


def decorate_returns(values: pd.Series, family: str, method: str, name: str) -> pd.DataFrame:
    growth = (1 + values).cumprod()
    drawdown = growth / growth.cummax() - 1
    return pd.DataFrame(
        {
            "date": values.index,
            "fund": name,
            "family": family,
            "method": method,
            "return": values.to_numpy(),
            "growth_of_one": growth.to_numpy(),
            "drawdown": drawdown.to_numpy(),
        }
    )


def weights_long(weights: pd.DataFrame, family: str, method: str, name: str) -> pd.DataFrame:
    output = weights.rename_axis("rebalance_date").reset_index().melt(
        id_vars="rebalance_date", var_name="ticker", value_name="weight"
    )
    output.insert(1, "fund", name)
    output.insert(2, "family", family)
    output.insert(3, "method", method)
    return output


def build_baseline_funds(
    return_sets: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[tuple[str, str], pd.DataFrame]]:
    """Build 12 baseline funds: three families by four methods."""
    return_rows, weight_rows, audit_rows, metric_rows = [], [], [], []
    weight_lookup: dict[tuple[str, str], pd.DataFrame] = {}
    configs = {
        "Equity": portfolios.BacktestConfig(252, 252, 0.10),
        "Crypto": portfolios.BacktestConfig(365, 365, 0.25),
        "Combined": portfolios.BacktestConfig(252, 252, 0.10),
    }
    for family, returns in return_sets.items():
        config = configs[family]
        for method in portfolios.METHODS:
            name = fund_name(family, method)
            print(f"backtesting {name} ...")
            realised, weights, audit = portfolios.oos_backtest(returns, method, config)
            weight_lookup[(family, method)] = weights
            return_rows.append(decorate_returns(realised, family, method, name))
            weight_rows.append(weights_long(weights, family, method, name))
            audit.insert(0, "fund", name)
            audit.insert(1, "family", family)
            audit.insert(2, "method", method)
            audit_rows.append(audit)
            metrics = portfolios.performance_metrics(realised, config.periods_per_year)
            metrics.update(
                {
                    "fund": name,
                    "family": family,
                    "method": method,
                    "lookback_observations": config.lookback,
                    "rebalance_frequency": "monthly_first_observed_day",
                    "risk_free_rate": config.risk_free_rate,
                    "transaction_cost_bps": config.transaction_cost_bps,
                    "mean_one_way_turnover": float(audit["turnover"].mean()),
                    "latest_max_weight": float(weights.iloc[-1].max()),
                    "latest_effective_holdings": int((weights.iloc[-1] > 1e-6).sum()),
                }
            )
            metric_rows.append(metrics)
    return (
        pd.concat(return_rows, ignore_index=True),
        pd.concat(weight_rows, ignore_index=True),
        pd.concat(audit_rows, ignore_index=True),
        pd.DataFrame(metric_rows),
        weight_lookup,
    )


def add_fusion_funds(
    fund_returns: pd.DataFrame,
    fund_weights: pd.DataFrame,
    metrics: pd.DataFrame,
    equity_returns: pd.DataFrame,
    base_weights: pd.DataFrame,
    sector_index: pd.DataFrame,
    ticker_sector: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Add plain and coverage-aware sentiment versions of equity min variance."""
    return_rows, weight_rows, metric_rows, audit_rows = [], [], [], []
    specifications = [
        (False, "sentiment", "Equity Min Variance + Sentiment"),
        (True, "coverage_sentiment", "Equity Min Variance + Coverage-Aware Sentiment"),
    ]
    for reliable, method, name in specifications:
        tilted, audit = fusion.sentiment_tilt_weights(
            base_weights,
            sector_index,
            ticker_sector,
            strength=0.35,
            reliability_adjusted=reliable,
            max_weight=0.10,
        )
        realised = fusion.returns_from_rebalance_weights(equity_returns, tilted)
        return_rows.append(decorate_returns(realised, "Equity", method, name))
        weight_rows.append(weights_long(tilted, "Equity", method, name))
        audit.insert(0, "fund", name)
        audit.insert(1, "method", method)
        audit_rows.append(audit)
        row = portfolios.performance_metrics(realised, 252)
        row.update(
            {
                "fund": name,
                "family": "Equity",
                "method": method,
                "lookback_observations": 252,
                "rebalance_frequency": "monthly_first_observed_day",
                "risk_free_rate": 0.0,
                "transaction_cost_bps": 0.0,
                "mean_one_way_turnover": float(tilted.diff().abs().sum(axis=1).div(2).iloc[1:].mean()),
                "latest_max_weight": float(tilted.iloc[-1].max()),
                "latest_effective_holdings": int((tilted.iloc[-1] > 1e-6).sum()),
            }
        )
        metric_rows.append(row)
    return (
        pd.concat([fund_returns, *return_rows], ignore_index=True),
        pd.concat([fund_weights, *weight_rows], ignore_index=True),
        pd.concat([metrics, pd.DataFrame(metric_rows)], ignore_index=True),
        pd.concat(audit_rows, ignore_index=True),
    )


def validation_summary(
    fund_returns: pd.DataFrame,
    fund_weights: pd.DataFrame,
    backtest_audit: pd.DataFrame,
    sector_index: pd.DataFrame,
) -> pd.DataFrame:
    """Record high-value automated gates with evidence counts."""
    weight_sums = fund_weights.groupby(["fund", "rebalance_date"])["weight"].sum()
    checks = [
        ("fund_return_keys_unique", not fund_returns.duplicated(["fund", "date"]).any(), int(fund_returns.duplicated(["fund", "date"]).sum())),
        ("fund_returns_finite", np.isfinite(fund_returns["return"]).all(), int((~np.isfinite(fund_returns["return"])).sum())),
        ("weights_sum_to_one", np.allclose(weight_sums, 1.0, atol=1e-8), float((weight_sums - 1).abs().max())),
        ("weights_nonnegative", fund_weights["weight"].ge(-1e-10).all(), float(fund_weights["weight"].min())),
        ("estimation_ends_before_rebalance", (backtest_audit["estimation_end"] < backtest_audit["rebalance_date"]).all(), int((backtest_audit["estimation_end"] >= backtest_audit["rebalance_date"]).sum())),
        ("sentiment_lagged_one_equity_day", (sector_index["signal_date"].dropna() > sector_index.loc[sector_index["signal_date"].notna(), "trading_date"]).all(), int((sector_index["signal_date"] <= sector_index["trading_date"]).fillna(False).sum())),
        ("reliability_bounded", sector_index["reliability"].between(0, 1).all(), int((~sector_index["reliability"].between(0, 1)).sum())),
    ]
    return pd.DataFrame(checks, columns=["check", "passed", "evidence_value"])


def main() -> None:
    for directory in (DATA_DIR, TABLE_DIR, FIGURE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    print("loading and validating hosted data ...")
    equity, crypto, news = etl.load_all_clean()
    equity_returns = features.returns_wide(equity)
    crypto_returns = features.returns_wide(crypto)
    combined = features.combined_returns(equity, crypto)
    return_sets = {"Equity": equity_returns, "Crypto": crypto_returns, "Combined": combined}

    fund_returns, fund_weights, backtest_audit, metrics, lookup = build_baseline_funds(return_sets)

    print("scoring deduplicated headlines with VADER ...")
    scored = sentiment.score_headlines(news, equity_returns.index)
    universe = features.ticker_sector_map(equity)
    sector_index = sentiment.sector_sentiment_index(scored, universe, equity_returns.index)
    ticker_sector = universe.set_index("ticker")["sector"]
    fund_returns, fund_weights, metrics, fusion_audit = add_fusion_funds(
        fund_returns,
        fund_weights,
        metrics,
        equity_returns,
        lookup[("Equity", "min_variance")],
        sector_index,
        ticker_sector,
    )

    fund_returns = fund_returns.sort_values(["fund", "date"]).reset_index(drop=True)
    fund_weights = fund_weights.sort_values(["fund", "rebalance_date", "ticker"]).reset_index(drop=True)
    metrics = metrics.sort_values(["family", "method"]).reset_index(drop=True)
    checks = validation_summary(fund_returns, fund_weights, backtest_audit, sector_index)
    if not checks["passed"].all():
        raise RuntimeError(f"validation failed:\n{checks.loc[~checks['passed']]}")

    write_csv(fund_returns, DATA_DIR / "fund_returns.csv")
    write_csv(fund_weights, DATA_DIR / "fund_weights.csv")
    write_csv(sector_index, DATA_DIR / "sector_sentiment_index.csv")
    write_csv(metrics, TABLE_DIR / "performance_metrics.csv")
    write_csv(backtest_audit, TABLE_DIR / "backtest_audit.csv")
    write_csv(fusion_audit, TABLE_DIR / "fusion_audit.csv")
    write_csv(checks, TABLE_DIR / "validation_summary.csv")

    fusion_methods = ["min_variance", "sentiment", "coverage_sentiment"]
    write_csv(metrics.loc[(metrics["family"].eq("Equity")) & metrics["method"].isin(fusion_methods)], TABLE_DIR / "fusion_comparison.csv")

    print("generating self-contained figures ...")
    figures = [
        reporting.plot_growth(fund_returns, FIGURE_DIR),
        reporting.plot_drawdown(fund_returns, FIGURE_DIR),
        reporting.plot_risk_return(metrics, FIGURE_DIR),
        reporting.plot_weights(fund_weights, FIGURE_DIR),
        reporting.plot_sector_sentiment(sector_index, FIGURE_DIR),
        reporting.plot_fusion(fund_returns, FIGURE_DIR),
    ]
    for path in figures:
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"build complete: {metrics['fund'].nunique()} funds, {len(sector_index):,} sector-day rows")


if __name__ == "__main__":
    main()
