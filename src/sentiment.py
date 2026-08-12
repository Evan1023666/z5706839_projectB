"""VADER headline scoring and coverage-aware equity-sector sentiment."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import features


def vader_analyser():
    """Load VADER, downloading its small lexicon only during the local build."""
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer

    try:
        return SentimentIntensityAnalyzer()
    except LookupError:
        nltk.download("vader_lexicon", quiet=True)
        return SentimentIntensityAnalyzer()


def score_headlines(
    headlines: pd.DataFrame,
    trading_dates,
    analyser=None,
) -> pd.DataFrame:
    """Score raw headlines and retain the source/aligned date audit trail."""
    aligned = features.align_headlines_to_trading_days(headlines, trading_dates)
    scored = aligned.loc[aligned["trading_date"].notna()].copy()
    analyser = vader_analyser() if analyser is None else analyser
    scored["sentiment"] = scored["title"].map(
        lambda text: float(analyser.polarity_scores(str(text))["compound"])
    )
    return scored[
        ["source_date", "trading_date", "ticker", "sector", "title", "sentiment"]
    ].reset_index(drop=True)


def ticker_day_sentiment(scores: pd.DataFrame) -> pd.DataFrame:
    """Average all headlines for a ticker on its aligned equity trading day."""
    required = {"trading_date", "ticker", "sector", "sentiment"}
    missing = required.difference(scores.columns)
    if missing:
        raise ValueError(f"scores missing columns: {sorted(missing)}")
    return (
        scores.groupby(["trading_date", "ticker", "sector"], as_index=False)
        .agg(sentiment=("sentiment", "mean"), headline_count=("sentiment", "size"))
        .sort_values(["trading_date", "sector", "ticker"])
        .reset_index(drop=True)
    )


def sector_sentiment_index(
    scores: pd.DataFrame,
    sector_universe: pd.DataFrame,
    trading_dates,
) -> pd.DataFrame:
    """Build a past-observable sector index without treating missing news as zero.

    Sentiment is the equal-weight mean across covered tickers. Coverage and
    normalised ticker concentration are saved beside polarity so the app and
    coverage-aware fusion can distinguish weak evidence from neutral news.
    `signal_date` is the first trading date on which the aligned day's news can be
    used (one observed equity day later).
    """
    ticker_day = ticker_day_sentiment(scores)
    universe = sector_universe[["ticker", "sector"]].drop_duplicates()
    sector_sizes = universe.groupby("sector")["ticker"].nunique().rename("sector_tickers")
    grouped = ticker_day.groupby(["trading_date", "sector"])
    index = grouped.agg(
        sentiment=("sentiment", "mean"),
        covered_tickers=("ticker", "nunique"),
        headline_count=("headline_count", "sum"),
        neutral_tickers=("sentiment", lambda x: int(np.isclose(x, 0.0).sum())),
    ).reset_index()
    index = index.merge(sector_sizes, on="sector", how="left", validate="many_to_one")
    index["coverage_rate"] = index["covered_tickers"] / index["sector_tickers"]

    counts = ticker_day[["trading_date", "sector", "ticker", "headline_count"]].copy()
    counts["headline_share"] = counts["headline_count"] / counts.groupby(
        ["trading_date", "sector"]
    )["headline_count"].transform("sum")
    hhi = counts.groupby(["trading_date", "sector"])["headline_share"].apply(
        lambda x: float(np.square(x).sum())
    ).rename("headline_hhi").reset_index()
    index = index.merge(hhi, on=["trading_date", "sector"], how="left")
    equal_hhi = 1 / index["covered_tickers"]
    denominator = 1 - equal_hhi
    index["normalised_concentration"] = np.where(
        index["covered_tickers"].gt(1),
        (index["headline_hhi"] - equal_hhi) / denominator,
        1.0,
    ).clip(0, 1)
    index["neutral_share_covered"] = index["neutral_tickers"] / index["covered_tickers"]
    # Reliability is transparent and bounded: broad coverage increases it while
    # concentration in a single name reduces it.
    index["reliability"] = (
        index["coverage_rate"] * (1 - index["normalised_concentration"])
    ).clip(0, 1)

    trading_calendar = pd.DatetimeIndex(
        sorted(pd.to_datetime(pd.Series(list(trading_dates))).dropna().unique())
    )
    if trading_calendar.empty:
        raise ValueError("complete equity trading calendar cannot be empty")
    positions = trading_calendar.searchsorted(index["trading_date"], side="right")
    usable = positions < len(trading_calendar)
    signal_dates = np.full(len(index), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    signal_dates[usable] = trading_calendar.to_numpy()[positions[usable]]
    index["signal_date"] = pd.to_datetime(signal_dates)
    index["missing_ticker_treatment"] = "drop_from_daily_mean_and_report_coverage"
    columns = [
        "trading_date", "signal_date", "sector", "sentiment", "covered_tickers",
        "sector_tickers", "coverage_rate", "headline_count", "headline_hhi",
        "normalised_concentration", "reliability", "neutral_tickers",
        "neutral_share_covered", "missing_ticker_treatment",
    ]
    return index[columns].sort_values(["trading_date", "sector"]).reset_index(drop=True)
