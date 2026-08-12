"""Long-only portfolio methods and walk-forward out-of-sample backtests."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize


METHODS = ("equal_weight", "min_variance", "max_sharpe", "risk_parity")


@dataclass(frozen=True)
class BacktestConfig:
    """Transparent assumptions shared by the portfolio builds."""

    lookback: int
    periods_per_year: int
    max_weight: float
    risk_free_rate: float = 0.0
    transaction_cost_bps: float = 0.0


def _validate_return_frame(returns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    frame = returns.copy().sort_index()
    frame.index = pd.to_datetime(frame.index)
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("return dates must be unique and increasing")
    if frame.columns.duplicated().any():
        raise ValueError("return tickers must be unique")
    if frame.isna().any().any() or not np.isfinite(frame.to_numpy()).all():
        raise ValueError("return frame must be finite and complete")
    if len(frame) <= lookback:
        raise ValueError("return frame is shorter than its estimation window")
    return frame.astype(float)


def _normalise_solution(result, n_assets: int, method: str) -> np.ndarray:
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"{method} optimisation failed: {result.message}")
    weights = np.clip(np.asarray(result.x, dtype=float), 0.0, None)
    total = weights.sum()
    if total <= 0:
        raise RuntimeError(f"{method} optimisation returned zero total weight")
    weights /= total
    if len(weights) != n_assets or abs(weights.sum() - 1.0) > 1e-8:
        raise RuntimeError(f"{method} optimisation returned infeasible weights")
    return weights


def _cap_and_normalise(values: np.ndarray, max_weight: float) -> np.ndarray:
    """Create a feasible start as a convex blend with equal weight.

    Both endpoints are long-only and fully invested. Moving from equal weight
    toward the random draw only as far as the first upper bound preserves those
    properties without the oscillation possible in repeated clipping.
    """
    draw = np.clip(np.asarray(values, dtype=float), 0, None)
    draw /= draw.sum()
    equal = np.repeat(1.0 / len(draw), len(draw))
    if (draw <= max_weight).all():
        return draw
    positive = draw > max_weight
    limits = (max_weight - equal[positive]) / (draw[positive] - equal[positive])
    scale = float(np.clip(limits.min() * 0.98, 0.0, 1.0))
    weights = equal + scale * (draw - equal)
    if (weights > max_weight + 1e-8).any():
        raise RuntimeError("could not create a feasible optimiser start")
    return weights


def optimise_weights(
    estimation_returns: pd.DataFrame,
    method: str,
    *,
    periods_per_year: int,
    max_weight: float,
    risk_free_rate: float = 0.0,
) -> np.ndarray:
    """Estimate long-only weights from information strictly before a rebalance."""
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    n_assets = estimation_returns.shape[1]
    if max_weight * n_assets < 1 - 1e-10:
        raise ValueError("max_weight makes the fully invested constraint infeasible")
    equal = np.repeat(1.0 / n_assets, n_assets)
    if method == "equal_weight":
        return equal

    # Annualising improves numerical scale and avoids false SLSQP convergence on
    # very small daily covariance values (a known issue in the assignment brief).
    mean = estimation_returns.mean().to_numpy() * periods_per_year
    covariance = estimation_returns.cov().to_numpy() * periods_per_year
    covariance = covariance + np.eye(n_assets) * 1e-8
    bounds = [(0.0, max_weight)] * n_assets
    constraints = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)

    if method == "min_variance":
        objective = lambda w: float(w @ covariance @ w)
    elif method == "max_sharpe":
        def objective(w):
            variance = float(w @ covariance @ w)
            return -float((w @ mean - risk_free_rate) / np.sqrt(max(variance, 1e-16)))
    else:
        def objective(w):
            portfolio_variance = float(w @ covariance @ w)
            marginal = covariance @ w
            contribution = w * marginal
            target = portfolio_variance / n_assets
            return float(np.square(contribution - target).sum() * 1e4)

    starts = [equal]
    if method == "max_sharpe":
        # Maximum Sharpe is non-convex in weights and SLSQP can fail from a
        # single start. Fixed-seed multi-starts are reproducible; only successful,
        # feasible candidates may be selected (never a silent equal-weight fallback).
        rng = np.random.default_rng(5706839 + n_assets)
        starts.extend(
            _cap_and_normalise(rng.dirichlet(np.ones(n_assets)), max_weight)
            for _ in range(10)
        )
    candidates = []
    failures = []
    for start in starts:
        result = minimize(
            objective,
            start,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-11, "maxiter": 3_000, "disp": False},
        )
        if result.success and np.isfinite(result.fun):
            candidate = _normalise_solution(result, n_assets, method)
            if (candidate <= max_weight + 1e-7).all():
                candidates.append((float(result.fun), result))
        else:
            failures.append(str(result.message))
    if not candidates:
        messages = sorted(set(failures))
        raise RuntimeError(f"{method} optimisation failed across all starts: {messages}")
    result = min(candidates, key=lambda item: item[0])[1]
    weights = _normalise_solution(result, n_assets, method)
    if (weights > max_weight + 1e-7).any():
        raise RuntimeError(f"{method} solution violates max_weight")
    return weights


def monthly_rebalance_dates(index: pd.DatetimeIndex, lookback: int) -> pd.DatetimeIndex:
    """Use the first available return date of each month after warm-up."""
    eligible = pd.Series(index[lookback:], index=index[lookback:])
    dates = eligible.groupby(eligible.index.to_period("M")).first()
    return pd.DatetimeIndex(dates.to_numpy())


def oos_backtest(
    returns: pd.DataFrame,
    method: str,
    config: BacktestConfig,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Run a monthly walk-forward backtest with past-only rolling estimates.

    At each rebalance date, the estimation slice ends on the previous observed
    return date. The new target weights apply to the rebalance day's return.
    """
    frame = _validate_return_frame(returns, config.lookback)
    dates = monthly_rebalance_dates(frame.index, config.lookback)
    output_returns: list[pd.Series] = []
    weight_rows: list[pd.Series] = []
    audit_rows: list[dict[str, object]] = []
    previous_weights: np.ndarray | None = None

    for position, rebalance_date in enumerate(dates):
        loc = frame.index.get_loc(rebalance_date)
        estimation = frame.iloc[loc - config.lookback:loc]
        if estimation.index.max() >= rebalance_date:
            raise RuntimeError("look-ahead detected in estimation window")
        weights = optimise_weights(
            estimation,
            method,
            periods_per_year=config.periods_per_year,
            max_weight=config.max_weight,
            risk_free_rate=config.risk_free_rate,
        )
        next_date = dates[position + 1] if position + 1 < len(dates) else None
        holding = frame.loc[rebalance_date:]
        if next_date is not None:
            holding = holding.loc[holding.index < next_date]
        realised = holding @ weights
        turnover = 0.0 if previous_weights is None else float(np.abs(weights - previous_weights).sum() / 2)
        if config.transaction_cost_bps and len(realised):
            realised.iloc[0] -= turnover * config.transaction_cost_bps / 10_000
        output_returns.append(realised)
        weight_rows.append(pd.Series(weights, index=frame.columns, name=rebalance_date))
        audit_rows.append(
            {
                "rebalance_date": rebalance_date,
                "estimation_start": estimation.index.min(),
                "estimation_end": estimation.index.max(),
                "holding_end": holding.index.max(),
                "observations": len(estimation),
                "turnover": turnover,
                "max_weight_observed": float(weights.max()),
            }
        )
        previous_weights = weights

    portfolio_returns = pd.concat(output_returns).sort_index()
    weights = pd.DataFrame(weight_rows).rename_axis("rebalance_date")
    audit = pd.DataFrame(audit_rows)
    if portfolio_returns.index.duplicated().any():
        raise RuntimeError("holding periods overlap")
    return portfolio_returns.rename("return"), weights, audit


def performance_metrics(
    daily_returns: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> dict[str, float | int | str]:
    """Return compounded annual metrics and maximum peak-to-trough drawdown."""
    values = pd.Series(daily_returns).dropna().astype(float)
    if values.empty or (values <= -1).any():
        raise ValueError("daily returns must be non-empty and greater than -100%")
    growth = (1 + values).cumprod()
    years = len(values) / periods_per_year
    annual_return = float(growth.iloc[-1] ** (1 / years) - 1)
    annual_mean_return = float(values.mean() * periods_per_year)
    annual_volatility = float(values.std(ddof=1) * np.sqrt(periods_per_year))
    sharpe = (
        (annual_mean_return - risk_free_rate) / annual_volatility
        if annual_volatility > 0 else np.nan
    )
    drawdown = growth / growth.cummax() - 1
    return {
        "start_date": values.index.min().date().isoformat(),
        "end_date": values.index.max().date().isoformat(),
        "observations": int(len(values)),
        "annualisation_days": int(periods_per_year),
        "annualised_return": annual_return,
        "annualised_mean_return": annual_mean_return,
        "annualised_volatility": annual_volatility,
        "sharpe_ratio": float(sharpe),
        "maximum_drawdown": float(drawdown.min()),
        "terminal_growth_of_one": float(growth.iloc[-1]),
    }
