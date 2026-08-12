"""Clean and validate the three supplied FINS5545 datasets.

Only known structural issues are changed: dates are normalised, the sample is
capped at 2023-12-31, and exact duplicate headlines are removed. Genuine market
extremes remain in the data because they are part of the investment risk.
"""

from __future__ import annotations

import pandas as pd

from src import data_access


SAMPLE_START = pd.Timestamp("2020-01-01")
SAMPLE_END = pd.Timestamp("2023-12-31")
PRICE_KEY = ["ticker", "date"]
NEWS_KEY = ["ticker", "date", "title"]
PRICE_COLUMNS = {
    "ticker", "date", "open", "high", "low", "close", "adjClose", "volume"
}


def require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    """Raise a readable error when an input schema is incomplete."""
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def normalise_date(values: pd.Series) -> pd.Series:
    """Return timezone-naive midnight dates without changing the UTC day."""
    parsed = pd.to_datetime(values, errors="raise", utc=True)
    return parsed.dt.tz_convert(None).dt.normalize()


def clean_prices(
    prices: pd.DataFrame, *, name: str, require_sector: bool
) -> pd.DataFrame:
    """Clean a price panel while preserving valid observations."""
    required = PRICE_COLUMNS | ({"sector"} if require_sector else set())
    require_columns(prices, required, name)
    clean = prices.copy()
    clean["date"] = normalise_date(clean["date"])
    clean = clean.loc[clean["date"].between(SAMPLE_START, SAMPLE_END)].copy()
    clean["ticker"] = clean["ticker"].astype("string").str.strip()
    if require_sector:
        clean["sector"] = clean["sector"].astype("string").str.strip()

    duplicate_rows = clean.duplicated(PRICE_KEY, keep=False)
    if duplicate_rows.any():
        groups = clean.loc[duplicate_rows].groupby(PRICE_KEY, dropna=False)
        conflicts = groups.nunique(dropna=False).max(axis=1).gt(1)
        if conflicts.any():
            raise ValueError(f"{name} contains conflicting ticker-date observations")
        clean = clean.drop_duplicates(PRICE_KEY, keep="first")

    numeric = ["open", "high", "low", "close", "adjClose", "volume"]
    if clean[numeric].isna().any().any():
        raise ValueError(f"{name} contains missing required numeric values")
    invalid = (
        clean[["open", "high", "low", "close", "adjClose"]].le(0).any(axis=1)
        | clean["volume"].lt(0)
        | clean["high"].lt(clean[["open", "close", "low"]].max(axis=1))
        | clean["low"].gt(clean[["open", "close", "high"]].min(axis=1))
    )
    if invalid.any():
        raise ValueError(f"{name} contains {int(invalid.sum())} invalid OHLCV rows")
    return clean.sort_values(PRICE_KEY, kind="stable").reset_index(drop=True)


def clean_news(headlines: pd.DataFrame) -> pd.DataFrame:
    """Preserve raw text and remove exact ticker-date-title duplicates."""
    required = {"date", "ticker", "sector", "title", "url", "publisher"}
    require_columns(headlines, required, "news_headlines")
    clean = headlines.copy()
    clean["date"] = normalise_date(clean["date"])
    clean = clean.loc[clean["date"].between(SAMPLE_START, SAMPLE_END)].copy()
    clean["ticker"] = clean["ticker"].astype("string").str.strip()
    clean["sector"] = clean["sector"].astype("string").str.strip()
    # VADER uses punctuation, casing, intensifiers and negation. Do not normalise title.
    clean["title"] = clean["title"].astype("string")
    clean = clean.drop_duplicates(NEWS_KEY, keep="first")
    return clean.sort_values(NEWS_KEY, kind="stable").reset_index(drop=True)


def load_clean_equities(prices: pd.DataFrame | None = None) -> pd.DataFrame:
    raw = data_access.load_equity_prices() if prices is None else prices
    return clean_prices(raw, name="equity_prices", require_sector=True)


def load_clean_crypto(prices: pd.DataFrame | None = None) -> pd.DataFrame:
    raw = data_access.load_crypto_prices() if prices is None else prices
    return clean_prices(raw, name="crypto_prices", require_sector=False)


def load_clean_news(headlines: pd.DataFrame | None = None) -> pd.DataFrame:
    raw = data_access.load_news_headlines() if headlines is None else headlines
    return clean_news(raw)


def load_all_clean() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load each hosted source once and return clean equity, crypto and news."""
    return load_clean_equities(), load_clean_crypto(), load_clean_news()
