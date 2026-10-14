"""Every sample dataset must work in every mode."""
import json

import numpy as np
import pandas as pd
import pytest

from app import basket, clv, forecast, recommend
from app.common import read_table, to_jsonable, to_number
from app.samples import SAMPLES_DIR

from .mappings import (
    SAMPLES,
    basket_params,
    clv_params,
    forecast_params,
    recommendation_params,
)

SAMPLE_IDS = list(SAMPLES)

# Product pairs that were deliberately built into each sample, so Market Basket must find them.
EXPECTED_PAIRS = {
    "office-home-retail": {"HD Webcam", "Noise Cancelling Headset"},
    "grocery-supermarket": {"Cola 2L", "Potato Chips"},
    "online-electronics": {"Indoor Security Camera", "Video Doorbell"},
    "online-fashion": {"Oxford Button Shirt", "Stretch Chinos"},
    "wholesale-cafe-supplies": {"Vanilla Syrup 1L Case of 6", "Caramel Syrup 1L Case of 6"},
}


@pytest.fixture(scope="module")
def frames():
    out = {}
    for sid, spec in SAMPLES.items():
        out[sid] = read_table((SAMPLES_DIR / spec["file"]).read_bytes(), spec["file"])
    return out


def assert_json_safe(result):
    # Must serialize with strict JSON (no NaN or Infinity).
    json.dumps(to_jsonable(result), allow_nan=False)


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_clv(frames, sid):
    df, c = frames[sid], SAMPLES[sid]["cols"]
    result = clv.run(df, clv_params(c))
    assert_json_safe(result)
    segments = result["segments"]
    canonical = [name for name, _ in clv.SEGMENTS]
    names = [s["segment"] for s in segments]
    assert names == [n for n in canonical if n in names], "segments must keep their fixed order"
    assert {"Champions", "At Risk", "Hibernating"} <= set(names)
    assert all(s["customers"] > 0 for s in segments)
    assert sum(s["customers"] for s in segments) == df[c["customer"]].nunique() == result["kpis"]["customers"]
    assert abs(sum(s["pct_customers"] for s in segments) - 100) < 0.5
    assert abs(sum(s["pct_revenue"] for s in segments) - 100) < 0.5
    by = {s["segment"]: s for s in segments}
    # The segments must mean what their names say.
    assert by["Champions"]["avg_days_since_last"] < by["At Risk"]["avg_days_since_last"]
    assert by["Champions"]["avg_days_since_last"] < by["Hibernating"]["avg_days_since_last"]
    assert by["Champions"]["avg_spend"] > by["Hibernating"]["avg_spend"]
    assert by["At Risk"]["avg_spend"] > by["Hibernating"]["avg_spend"]
    assert by["Champions"]["avg_orders"] > by["Promising Customers"]["avg_orders"]
    # Revenue is net of returns: purchases minus any negative (return) lines.
    expected_revenue = (to_number(df[c["qty"]]) * to_number(df[c["price"]])).sum()
    assert result["kpis"]["total_revenue"] == pytest.approx(expected_revenue, rel=1e-6)
    assert len(result["customers"]) == result["kpis"]["customers"]
    assert result["insights"]
    for row in result["customers"][:50]:
        r_, f_, m_ = (int(x) for x in row["rfm"].split("-"))
        assert 1 <= min(r_, f_, m_) and max(r_, f_, m_) <= 5
        assert row["segment"] == clv._segment(r_, f_, m_)


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_clv_text_matches_the_numbers_on_screen(frames, sid):
    """Percentages in the takeaways must round the same way as the segment cards (.5 rounds up)."""
    df, c = frames[sid], SAMPLES[sid]["cols"]
    result = clv.run(df, clv_params(c))
    by = {s["segment"]: s for s in result["segments"]}
    up = lambda x: int(x + 0.5)
    text = " ".join(result["insights"])
    assert f"{up(by['Champions']['pct_revenue'])}% of revenue" in text
    assert f"account for {up(by['At Risk']['pct_revenue'])}% of revenue" in text


def test_rfm_scores_follow_the_rules():
    values = pd.Series([1, 1, 1, 1, 2, 5, 9, 20, 40, 80])
    scores = clv._score(values)
    assert scores.between(1, 5).all()
    assert scores.iloc[0] == scores.iloc[3], "equal values must get equal scores"
    assert scores.is_monotonic_increasing
    recency = clv._score(pd.Series([3, 10, 200, 400, 900, 5, 6, 7, 8, 9]), higher_is_better=False)
    assert recency.iloc[0] > recency.iloc[4], "more recent customers must score higher on recency"
    assert clv._segment(5, 5, 5) == "Champions"
    assert clv._segment(3, 3, 3) == "Loyal Customers"
    assert clv._segment(5, 1, 2) == "Promising Customers"
    assert clv._segment(1, 5, 5) == "At Risk"
    assert clv._segment(1, 1, 1) == "Hibernating"


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_recommendation(frames, sid):
    df, c = frames[sid], SAMPLES[sid]["cols"]
    result = recommend.run(df, recommendation_params(c))
    assert_json_safe(result)
    bought = df.groupby(c["customer"])[c["pname"]].apply(set).to_dict()
    assert len(result["customers"]) == df[c["customer"]].nunique()
    for entry in result["customers"]:
        recs = entry["recommendations"]
        assert len(recs) <= 5
        assert len(recs) >= 1 or entry["products_bought"] == result["kpis"]["products"], "only a customer who owns everything may get nothing"
        names = [r["product"] for r in recs]
        assert len(set(names)) == len(names), "duplicate recommendation"
        assert not (set(names) & bought[entry["customer_id"]]), "recommended something already bought"
        assert entry["top_purchases"]
        for r in recs:
            assert r["match_pct"] is None or 0 <= r["match_pct"] <= 100
            assert r["reason"]


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_recommendation_is_validated_against_best_sellers(frames, sid):
    df, c = frames[sid], SAMPLES[sid]["cols"]
    v = recommend.run(df, recommendation_params(c))["validation"]
    assert v is not None
    assert v["customers_tested"] >= 30
    assert 0 <= v["model_hit_pct"] <= 100 and 0 <= v["bestseller_hit_pct"] <= 100
    assert v["verdict"] in {"better", "similar", "worse"}
    gap = v["model_hit_pct"] - v["bestseller_hit_pct"]
    assert (v["verdict"] == "better") == (gap >= recommend.VERDICT_MARGIN)


def test_recommendation_validation_is_repeatable(frames):
    c = SAMPLES["office-home-retail"]["cols"]
    df = frames["office-home-retail"]
    a = recommend.run(df, recommendation_params(c))["validation"]
    b = recommend.run(df, recommendation_params(c))["validation"]
    assert a == b


def test_recommendation_beats_best_sellers_where_buying_patterns_exist(frames):
    """Online electronics has strong product links; the model must clearly win there."""
    c = SAMPLES["online-electronics"]["cols"]
    v = recommend.run(frames["online-electronics"], recommendation_params(c))["validation"]
    assert v["verdict"] == "better"


def test_recommendation_validation_skipped_when_data_is_too_thin(frames):
    c = SAMPLES["office-home-retail"]["cols"]
    df = frames["office-home-retail"]
    few = df[df[c["customer"]].isin(df[c["customer"]].unique()[:12])]
    result = recommend.run(few, recommendation_params(c))
    assert result["validation"] is None
    assert result["customers"], "recommendations must still be produced"


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_basket(frames, sid):
    df, c = frames[sid], SAMPLES[sid]["cols"]
    result = basket.run(df, basket_params(c))
    assert_json_safe(result)
    assert result["rules"] and result["pairs"]
    for rule in result["rules"]:
        assert rule["lift"] >= 1.1 and 0 < rule["confidence"] <= 100 and rule["support"] > 0
    found = {frozenset((p["product_a"], p["product_b"])) for p in result["pairs"][:10]}
    assert frozenset(EXPECTED_PAIRS[sid]) in found, f"expected built in pair missing from top pairs: {found}"
    assert result["kpis"]["baskets"] > 1000


@pytest.mark.parametrize("sid", SAMPLE_IDS)
@pytest.mark.parametrize("variant", ["all", "filter", "filter_plus_additional"])
def test_forecast(frames, sid, variant):
    spec = SAMPLES[sid]
    df, c = frames[sid], spec["cols"]
    if variant == "all":
        params = forecast_params(c, periods=6)
    elif variant == "filter":
        params = forecast_params(c, spec["filter_value"], periods=9)
    else:
        params = forecast_params(c, spec["filter_value"], spec["additional_value"], periods=12, use_additional=True)
    result = forecast.run(df, params)
    assert_json_safe(result)
    fc = result["forecast"]
    assert len(fc) == params["periods"]
    assert fc[0]["month"] == "2026-10"
    months = [f["month"] for f in fc]
    assert months == sorted(set(months))
    for f in fc:
        assert 0 <= f["lower"] <= f["value"] <= f["upper"]
    assert result["history"][-1]["month"] == "2026-09"
    assert result["history"][0]["month"] in ("2023-10", "2023-11")
    assert result["model"]["name"] and result["insights"]
    assert result["accuracy"] is not None and 0 <= result["accuracy"]["accuracy_pct"] <= 100


def test_forecast_totals_match_data(frames):
    sid = "grocery-supermarket"
    df, c = frames[sid], SAMPLES[sid]["cols"]
    result = forecast.run(df, forecast_params(c, periods=3))
    # History for the total business equals the monthly sum of the sales column.
    dates = pd.to_datetime(df[c["date"]], format="%d/%m/%Y")
    monthly = pd.to_numeric(df[c["sales"]]).groupby(dates.dt.to_period("M")).sum()
    for point in result["history"]:
        assert point["value"] == pytest.approx(monthly[pd.Period(point["month"])], abs=0.02)


def test_seasonal_pattern_found_when_it_exists(frames):
    """The electronics store has a strong Nov and Dec peak. The forecast for those months must reflect it."""
    sid = "online-electronics"
    df, c = frames[sid], SAMPLES[sid]["cols"]
    result = forecast.run(df, forecast_params(c, periods=12))
    by_month = {f["month"]: f["value"] for f in result["forecast"]}
    assert by_month["2026-11"] > 1.3 * by_month["2027-02"]
    assert by_month["2026-12"] > 1.3 * by_month["2027-03"]


def test_forecast_uses_a_single_method_and_warns_beyond_tested_horizon(frames):
    spec = SAMPLES["online-electronics"]
    result = forecast.run(frames["online-electronics"], forecast_params(spec["cols"], periods=24))
    assert result["model"]["name"] == "Exponential smoothing with trend and yearly pattern"
    assert any("tested up to 12 months" in w for w in result["warnings"])
    short = forecast.run(frames["online-electronics"], forecast_params(spec["cols"], periods=6))
    assert not any("tested up to" in w for w in short["warnings"])


@pytest.mark.parametrize("sid", SAMPLE_IDS)
@pytest.mark.parametrize("periods", [1, 6, 12])
def test_forecast_error_measures_match_the_backtest_table(frames, sid, periods):
    """Every error measure must follow from the month by month table shown to the user."""
    spec = SAMPLES[sid]
    result = forecast.run(frames[sid], forecast_params(spec["cols"], periods=periods))
    acc, table = result["accuracy"], result["backtest"]
    assert acc and table and len(table) == acc["months_tested"] >= 6
    assert acc["horizon"] == min(periods, 12)
    actual = np.array([r["actual"] for r in table])
    predicted = np.array([r["forecast"] for r in table])
    error = predicted - actual
    total = np.abs(actual).sum()
    assert acc["wape_pct"] == pytest.approx(100 * np.abs(error).sum() / total, abs=0.1)
    assert acc["accuracy_pct"] == pytest.approx(100 - acc["wape_pct"], abs=0.1)
    assert set(acc) == {"accuracy_pct", "wape_pct", "bias_pct", "benchmark_wape_pct", "months_tested", "folds", "horizon"}
    assert acc["bias_pct"] == pytest.approx(100 * error.sum() / total, abs=0.1)
    assert acc["benchmark_wape_pct"] > 0


def test_forecast_benchmark_is_same_month_last_year(frames):
    """Recompute the benchmark independently: for each tested month, use the same month a year earlier."""
    spec = SAMPLES["online-electronics"]
    result = forecast.run(frames["online-electronics"], forecast_params(spec["cols"], periods=6))
    history = {h["month"]: h["value"] for h in result["history"]}
    table = result["backtest"]
    actual = np.array([r["actual"] for r in table])
    bench = np.array([history[(pd.Period(r["month"], "M") - 12).strftime("%Y-%m")] for r in table])
    assert result["accuracy"]["benchmark_wape_pct"] == pytest.approx(100 * np.abs(bench - actual).sum() / np.abs(actual).sum(), abs=0.1)
