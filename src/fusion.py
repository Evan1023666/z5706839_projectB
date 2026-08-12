"""Look-ahead-safe sentiment tilts for equity fund weights."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _bounded_projection(raw: np.ndarray, max_weight: float) -> np.ndarray:
    """Project scores with capped proportional (water-filling) scaling."""
    values = np.clip(np.asarray(raw, dtype=float), 0, None)
    if values.sum() <= 0:
        values = np.ones_like(values)
    if max_weight * len(values) < 1 - 1e-12:
        raise ValueError("max_weight constraint is infeasible")
    # Find lambda such that sum(min(cap, lambda * raw_i)) = 1. The sum is
    # monotone, so bisection is stable even when several assets hit the cap.
    low, high = 0.0, 1.0 / values.max()
    while np.minimum(max_weight, high * values).sum() < 1:
        high *= 2
    for _ in range(200):
        middle = (low + high) / 2
        if np.minimum(max_weight, middle * values).sum() < 1:
            low = middle
        else:
            high = middle
    weights = np.minimum(max_weight, high * values)
    # Floating-point remainder is allocated only to uncapped names.
    remainder = 1.0 - weights.sum()
    if abs(remainder) > 1e-12:
        free = weights < max_weight - 1e-12
        if not free.any():
            raise RuntimeError("projection has no capacity for numerical remainder")
        weights[free] += remainder * values[free] / values[free].sum()
    if abs(weights.sum() - 1) > 1e-9 or (weights > max_weight + 1e-9).any():
        raise RuntimeError("projection failed to respect max_weight")
    return weights


def sentiment_tilt_weights(
    base_weights: pd.DataFrame,
    sector_index: pd.DataFrame,
    ticker_sectors: pd.Series,
    *,
    strength: float = 0.35,
    reliability_adjusted: bool = False,
    max_weight: float = 0.10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tilt each rebalance using the latest signal that is available by that day.

    Sector sentiment is cross-sectionally standardised, clipped to [-2, 2], and
    converted to a multiplicative exponential tilt. The innovation multiplies the
    z-score by contemporaneous coverage reliability before applying the tilt.
    """
    required = {"signal_date", "sector", "sentiment", "reliability"}
    missing = required.difference(sector_index.columns)
    if missing:
        raise ValueError(f"sector_index missing columns: {sorted(missing)}")
    weights = base_weights.copy().sort_index()
    weights.index = pd.to_datetime(weights.index)
    mapping = ticker_sectors.reindex(weights.columns)
    if mapping.isna().any():
        raise ValueError("missing sector mapping for one or more equity tickers")
    signals = sector_index.dropna(subset=["signal_date"]).copy()
    signals["signal_date"] = pd.to_datetime(signals["signal_date"])
    tilted_rows: list[pd.Series] = []
    audit_rows: list[dict[str, object]] = []

    for rebalance_date, base in weights.iterrows():
        available = signals.loc[signals["signal_date"].le(rebalance_date)]
        if available.empty:
            tilted = base.to_numpy()
            signal_date = pd.NaT
            mean_reliability = np.nan
        else:
            signal_date = available["signal_date"].max()
            cross_section = available.loc[available["signal_date"].eq(signal_date)].set_index("sector")
            score = cross_section["sentiment"].astype(float)
            std = score.std(ddof=0)
            z_score = (score - score.mean()) / std if std > 0 else score * 0
            z_score = z_score.clip(-2, 2)
            if reliability_adjusted:
                z_score = z_score * cross_section["reliability"].fillna(0)
            ticker_score = mapping.map(z_score).fillna(0).to_numpy(dtype=float)
            raw = base.to_numpy(dtype=float) * np.exp(strength * ticker_score)
            tilted = _bounded_projection(raw, max_weight)
            mean_reliability = float(cross_section["reliability"].mean())
        tilted_rows.append(pd.Series(tilted, index=weights.columns, name=rebalance_date))
        audit_rows.append(
            {
                "rebalance_date": rebalance_date,
                "signal_date_used": signal_date,
                "reliability_adjusted": reliability_adjusted,
                "mean_signal_reliability": mean_reliability,
                "active_weight_change": float(np.abs(tilted - base.to_numpy()).sum() / 2),
            }
        )
    return pd.DataFrame(tilted_rows), pd.DataFrame(audit_rows)


def returns_from_rebalance_weights(
    asset_returns: pd.DataFrame,
    weights: pd.DataFrame,
) -> pd.Series:
    """Apply target weights from each rebalance through the next rebalance."""
    returns = asset_returns.sort_index()
    dates = pd.DatetimeIndex(weights.index).sort_values()
    pieces = []
    for i, date in enumerate(dates):
        next_date = dates[i + 1] if i + 1 < len(dates) else None
        holding = returns.loc[date:]
        if next_date is not None:
            holding = holding.loc[holding.index < next_date]
        pieces.append(holding @ weights.loc[date])
    result = pd.concat(pieces).sort_index()
    if result.index.duplicated().any():
        raise RuntimeError("fusion holding periods overlap")
    return result.rename("return")
