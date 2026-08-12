"""Return features and headline-to-trading-day alignment."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from src import etl


def daily_returns(prices: pd.DataFrame, price_col: str = "adjClose") -> pd.DataFrame:
    """Compute simple returns within ticker on the native asset calendar."""
    etl.require_columns(prices, {"ticker", "date", price_col}, "prices")
    columns = ["date", "ticker", price_col]
    if "sector" in prices.columns:
        columns.append("sector")
    ordered = prices[columns].copy()
    ordered["date"] = etl.normalise_date(ordered["date"])
    ordered = ordered.sort_values(["ticker", "date"], kind="stable")
    ordered["return"] = ordered.groupby("ticker", sort=False)[price_col].pct_change(
        fill_method=None
    )
    output = ["date", "ticker"]
    if "sector" in ordered.columns:
        output.append("sector")
    output.append("return")
    return ordered[output].reset_index(drop=True)


def returns_wide(prices: pd.DataFrame) -> pd.DataFrame:
    """Return a complete date-by-ticker simple-return matrix."""
    long = daily_returns(prices).dropna(subset=["return"])
    if long.duplicated(["date", "ticker"]).any():
        raise ValueError("returns contain duplicate date-ticker keys")
    wide = long.pivot(index="date", columns="ticker", values="return").sort_index()
    wide.columns.name = None
    return wide


def combined_returns(equity_prices: pd.DataFrame, crypto_prices: pd.DataFrame) -> pd.DataFrame:
    """Join native-calendar returns on the equity trading calendar.

    Crypto returns are computed before the join, so weekend-only crypto returns are
    not rolled into Monday. This reproduces the calendar decision made in Part A.
    """
    equity = returns_wide(equity_prices)
    crypto = returns_wide(crypto_prices)
    overlap = set(equity.columns).intersection(crypto.columns)
    if overlap:
        raise ValueError(f"overlapping ticker labels: {sorted(overlap)}")
    joined = equity.join(crypto, how="left")
    if joined.isna().any().any():
        raise ValueError("combined return panel unexpectedly contains missing values")
    joined.index.name = "date"
    return joined


def align_headlines_to_trading_days(
    headlines: pd.DataFrame, trading_dates: Iterable[object]
) -> pd.DataFrame:
    """Map headlines to the same or next equity day without using future prices."""
    etl.require_columns(headlines, {"date", "ticker", "sector", "title"}, "headlines")
    aligned = headlines.copy()
    aligned["source_date"] = etl.normalise_date(aligned["date"])
    dates = pd.Series(list(trading_dates), dtype="object")
    calendar = pd.DatetimeIndex(etl.normalise_date(dates).dropna().unique()).sort_values()
    if calendar.empty:
        raise ValueError("trading calendar cannot be empty")
    positions = calendar.searchsorted(aligned["source_date"], side="left")
    valid = positions < len(calendar)
    mapped = np.full(len(aligned), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    mapped[valid] = calendar.to_numpy()[positions[valid]]
    aligned["trading_date"] = pd.to_datetime(mapped)
    aligned["alignment_lag_days"] = (
        aligned["trading_date"] - aligned["source_date"]
    ).dt.days.astype("Int64")
    return aligned


def ticker_sector_map(equity_prices: pd.DataFrame) -> pd.DataFrame:
    """Return one validated sector for each equity ticker."""
    mapping = equity_prices[["ticker", "sector"]].drop_duplicates()
    if mapping["ticker"].duplicated().any():
        raise ValueError("an equity ticker maps to multiple sectors")
    return mapping.sort_values(["sector", "ticker"]).reset_index(drop=True)
