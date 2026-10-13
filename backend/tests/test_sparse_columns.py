"""Files rarely have every column. Each mode must run on the few columns it truly needs, and say clearly what is missing."""
import pytest

from app import basket, clv, recommend
from app.common import UserError, read_table
from app.samples import SAMPLES_DIR

from .mappings import SAMPLES, clv_params

SAMPLE_IDS = list(SAMPLES)


@pytest.fixture(scope="module")
def frames():
    return {sid: read_table((SAMPLES_DIR / s["file"]).read_bytes(), s["file"]) for sid, s in SAMPLES.items()}


def message(fn, df, params):
    with pytest.raises(UserError) as info:
        fn(df, params)
    return str(info.value)


# ------------------------------------------------------------------ customer value
@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_clv_with_sales_column_matches_quantity_times_price(frames, sid):
    c = SAMPLES[sid]["cols"]
    by_price = clv.run(frames[sid], clv_params(c))
    by_sales = clv.run(frames[sid], {"customer_id": c["customer"], "invoice_date": c["date"], "sales": c["sales"], "invoice_id": c["invoice"]})
    assert by_sales["kpis"]["total_revenue"] == pytest.approx(by_price["kpis"]["total_revenue"], abs=1)
    assert [s["customers"] for s in by_sales["segments"]] == [s["customers"] for s in by_price["segments"]]


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_clv_with_only_customer_date_and_sales(frames, sid):
    c = SAMPLES[sid]["cols"]
    result = clv.run(frames[sid], {"customer_id": c["customer"], "invoice_date": c["date"], "sales": c["sales"]})
    assert result["kpis"]["customers"] > 100
    assert any("one order" in w for w in result["warnings"])


def test_clv_needs_an_amount(frames):
    c = SAMPLES["office-home-retail"]["cols"]
    text = message(clv.run, frames["office-home-retail"], {"customer_id": c["customer"], "invoice_date": c["date"], "quantity": c["qty"]})
    assert "Sales Column" in text and "Unit Price" in text


# ------------------------------------------------------------------ recommendation
@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_recommendation_with_only_customer_and_product_name(frames, sid):
    c = SAMPLES[sid]["cols"]
    result = recommend.run(frames[sid], {"customer_id": c["customer"], "product_name": c["pname"]})
    assert result["kpis"]["total_revenue"] is None
    assert result["kpis"]["has_category"] is False and result["kpis"]["has_sub_category"] is False
    assert all(len(e["recommendations"]) <= 5 for e in result["customers"][:50])
    assert all(e["recommendations"] or e["products_bought"] == result["kpis"]["products"] for e in result["customers"])
    assert all(e["total_spend"] is None for e in result["customers"][:20])
    for e in result["customers"][:50]:
        owned = {p["product"] for p in e["top_purchases"]}
        assert not owned & {r["product"] for r in e["recommendations"]}
    assert result["validation"] is not None


@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_recommendation_with_only_customer_and_product_id(frames, sid):
    c = SAMPLES[sid]["cols"]
    result = recommend.run(frames[sid], {"customer_id": c["customer"], "product_id": c["pid"]})
    assert result["customers"] and any(e["recommendations"] for e in result["customers"])


def test_recommendation_needs_a_product(frames):
    c = SAMPLES["office-home-retail"]["cols"]
    assert "Product ID Column or a Product Name Column" in message(recommend.run, frames["office-home-retail"], {"customer_id": c["customer"]})


def test_recommendation_blank_category_cells_do_not_drop_rows(frames):
    c = SAMPLES["office-home-retail"]["cols"]
    df = frames["office-home-retail"].copy()
    df.loc[df.index[::7], c["cat"]] = ""
    result = recommend.run(df, {"customer_id": c["customer"], "product_id": c["pid"], "product_name": c["pname"], "category": c["cat"]})
    assert not any("Skipped" in w for w in result["warnings"])
    assert result["kpis"]["has_category"] is True


# ------------------------------------------------------------------ market basket
@pytest.mark.parametrize("sid", SAMPLE_IDS)
def test_basket_by_order_id_and_by_customer_and_date(frames, sid):
    c = SAMPLES[sid]["cols"]
    by_order = basket.run(frames[sid], {"product_name": c["pname"], "transaction_id": c["invoice"]})
    by_customer = basket.run(frames[sid], {"product_name": c["pname"], "member_number": c["customer"], "date": c["date"]})
    assert by_order["pairs"] and by_customer["pairs"]
    assert by_order["kpis"]["baskets"] >= by_customer["kpis"]["baskets"]


def test_basket_needs_a_way_to_form_baskets(frames):
    c = SAMPLES["office-home-retail"]["cols"]
    text = message(basket.run, frames["office-home-retail"], {"product_name": c["pname"], "member_number": c["customer"]})
    assert "Order ID" in text and "Customer" in text and "Date" in text

