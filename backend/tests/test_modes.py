"""Every sample dataset must work in every mode."""
import json

import pandas as pd
import pytest

from app import basket, clv, forecast, recommend
from app.common import read_table, to_jsonable
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
    assert [s["segment"] for s in segments] == ["Low Value", "Medium Value", "High Value"]
    assert all(s["customers"] > 0 for s in segments)
    assert sum(s["customers"] for s in segments) == df[c["customer"]].nunique() == result["kpis"]["customers"]
    assert abs(sum(s["pct_customers"] for s in segments) - 100) < 0.5
    assert abs(sum(s["pct_revenue"] for s in segments) - 100) < 0.5
    spends = [s["avg_spend"] for s in segments]
    assert spends == sorted(spends) and len(set(spends)) == 3
    # Segment boundaries must not overlap.
    assert segments[0]["max_spend"] <= segments[1]["min_spend"] <= segments[1]["max_spend"] <= segments[2]["min_spend"]
    expected_revenue = (pd.to_numeric(df[c["qty"]]) * pd.to_numeric(df[c["price"]])).sum()
    assert result["kpis"]["total_revenue"] == pytest.approx(expected_revenue, rel=1e-6)
    assert len(result["customers"]) == result["kpis"]["customers"]
    assert result["insights"]


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_recommendation(frames, sid):
    df, c = frames[sid], SAMPLES[sid]["cols"]
    result = recommend.run(df, recommendation_params(c))
    assert_json_safe(result)
    bought = df.groupby(c["customer"])[c["pname"]].apply(set).to_dict()
    assert len(result["customers"]) == df[c["customer"]].nunique()
    for entry in result["customers"]:
        recs = entry["recommendations"]
        assert 1 <= len(recs) <= 5
        names = [r["product"] for r in recs]
        assert len(set(names)) == len(names), "duplicate recommendation"
        assert not (set(names) & bought[entry["customer_id"]]), "recommended something already bought"
        assert entry["top_purchases"]
        for r in recs:
            assert r["match_pct"] is None or 0 <= r["match_pct"] <= 100
            assert r["reason"]
    assert result["top_products"] and result["category_mix"]


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
