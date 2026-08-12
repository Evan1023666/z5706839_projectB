"""High-value tests for Project B time alignment and portfolio constraints."""

import numpy as np
import pandas as pd
import pytest

from src import fusion, portfolios, sentiment


def synthetic_returns(rows=90, assets=5, seed=5706839):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-03", periods=rows)
    data = rng.normal(0.0004, 0.012, size=(rows, assets))
    return pd.DataFrame(data, index=dates, columns=[f"A{i}" for i in range(assets)])


@pytest.mark.parametrize("method", portfolios.METHODS)
def test_optimisers_are_long_only_and_fully_invested(method):
    returns = synthetic_returns()
    weights = portfolios.optimise_weights(
        returns, method, periods_per_year=252, max_weight=0.4
    )
    assert weights.sum() == pytest.approx(1.0, abs=1e-8)
    assert weights.min() >= -1e-10
    assert weights.max() <= 0.4 + 1e-8


def test_walk_forward_uses_only_past_observations():
    returns = synthetic_returns(rows=140)
    config = portfolios.BacktestConfig(lookback=40, periods_per_year=252, max_weight=0.4)
    realised, weights, audit = portfolios.oos_backtest(returns, "min_variance", config)
    assert not realised.index.duplicated().any()
    assert (pd.to_datetime(audit["estimation_end"]) < audit["rebalance_date"]).all()
    assert np.allclose(weights.sum(axis=1), 1.0)
    assert realised.index.min() == weights.index.min()
    assert audit.iloc[0]["turnover"] == pytest.approx(0.0)
    manual_mean_rebalance_turnover = audit["turnover"].iloc[1:].mean()
    assert manual_mean_rebalance_turnover >= 0


def test_performance_metrics_match_manual_growth_and_drawdown():
    returns = pd.Series([0.10, -0.20, 0.05], index=pd.date_range("2022-01-01", periods=3))
    metrics = portfolios.performance_metrics(returns, periods_per_year=3)
    growth = (1.10 * 0.80 * 1.05)
    assert metrics["terminal_growth_of_one"] == pytest.approx(growth)
    assert metrics["maximum_drawdown"] == pytest.approx(-0.20)
    expected_mean = np.mean([0.10, -0.20, 0.05]) * 3
    expected_vol = np.std([0.10, -0.20, 0.05], ddof=1) * np.sqrt(3)
    assert metrics["annualised_mean_return"] == pytest.approx(expected_mean)
    assert metrics["sharpe_ratio"] == pytest.approx(expected_mean / expected_vol)


class DummyAnalyser:
    def polarity_scores(self, text):
        return {"compound": 0.5 if "GOOD" in text else -0.5}


def test_sentiment_signal_is_next_trading_day_and_missing_is_not_zero():
    calendar = pd.bdate_range("2022-01-03", periods=4)
    news = pd.DataFrame(
        {
            "date": [pd.Timestamp("2022-01-03", tz="UTC")],
            "ticker": ["AAA"],
            "sector": ["Tech"],
            "title": ["GOOD update!"],
        }
    )
    scores = sentiment.score_headlines(news, calendar, DummyAnalyser())
    universe = pd.DataFrame(
        {"ticker": ["AAA", "BBB"], "sector": ["Tech", "Tech"]}
    )
    index = sentiment.sector_sentiment_index(scores, universe, calendar)
    row = index.iloc[0]
    assert row["trading_date"] == calendar[0]
    assert row["signal_date"] == calendar[1]
    assert row["coverage_rate"] == pytest.approx(0.5)
    assert row["sentiment"] == pytest.approx(0.5)
    assert row["missing_ticker_treatment"].startswith("drop")


def test_coverage_adjustment_reduces_active_tilt():
    date = pd.Timestamp("2022-02-01")
    base = pd.DataFrame([[0.25] * 4], index=[date], columns=list("ABCD"))
    sectors = pd.Series({"A": "S1", "B": "S1", "C": "S2", "D": "S2"})
    index = pd.DataFrame(
        {
            "signal_date": [date, date],
            "sector": ["S1", "S2"],
            "sentiment": [0.8, -0.8],
            "reliability": [0.2, 0.2],
        }
    )
    plain, plain_audit = fusion.sentiment_tilt_weights(
        base, index, sectors, strength=0.5, max_weight=0.5
    )
    reliable, reliable_audit = fusion.sentiment_tilt_weights(
        base, index, sectors, strength=0.5, reliability_adjusted=True, max_weight=0.5
    )
    assert np.allclose(plain.sum(axis=1), 1.0)
    assert np.allclose(reliable.sum(axis=1), 1.0)
    assert reliable_audit.loc[0, "active_weight_change"] < plain_audit.loc[0, "active_weight_change"]


def test_max_sharpe_is_deterministic_with_multistart():
    returns = synthetic_returns(rows=100, assets=12)
    first = portfolios.optimise_weights(
        returns, "max_sharpe", periods_per_year=252, max_weight=0.15
    )
    second = portfolios.optimise_weights(
        returns, "max_sharpe", periods_per_year=252, max_weight=0.15
    )
    assert np.allclose(first, second)


def test_bounded_projection_handles_concentrated_tilt():
    raw = np.array([100.0, 10.0, 1.0, 1.0, 1.0, 1.0])
    weights = fusion._bounded_projection(raw, max_weight=0.25)
    assert weights.sum() == pytest.approx(1.0, abs=1e-9)
    assert weights.max() <= 0.25 + 1e-9
    assert weights.min() >= 0
