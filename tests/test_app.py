"""Programmatic interaction checks for every Streamlit investor-journey page."""

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"
PAGES = [
    "Fund comparison",
    "Fund fact sheet",
    "Allocation lab",
    "Sentiment lens",
]


def run_page(page: str) -> AppTest:
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    app.radio[0].set_value(page).run()
    assert not app.exception
    return app


def test_all_investor_journey_pages_render_without_exceptions():
    for page in PAGES:
        run_page(page)


def test_comparison_uses_the_latest_corrected_metrics():
    app = run_page("Fund comparison")
    highest_sharpe = next(metric for metric in app.metric if metric.label == "Highest Sharpe")
    metrics = pd.read_csv(APP.parent / "results" / "tables" / "performance_metrics.csv")
    baseline = metrics.loc[~metrics["method"].str.contains("sentiment")]
    expected = baseline.loc[baseline["sharpe_ratio"].idxmax()]
    assert highest_sharpe.value == f"{expected.sharpe_ratio:.2f}"
    assert highest_sharpe.delta == expected.fund


def test_fact_sheet_fund_selection_is_interactive():
    app = run_page("Fund fact sheet")
    app.selectbox[0].set_value("Combined Minimum Variance").run()
    assert not app.exception
    assert any(metric.label == "Annual risk" for metric in app.metric)


def test_sentiment_sector_selection_is_interactive():
    app = run_page("Sentiment lens")
    app.selectbox[0].set_value("Tech").run()
    assert not app.exception
    assert any(metric.label == "Average reliability" for metric in app.metric)


def test_allocation_defaults_respect_slider_step():
    app = run_page("Allocation lab")
    assert app.slider
    for slider in app.slider:
        assert (slider.value - slider.min) % slider.step == 0
