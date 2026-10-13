"""API behaviour, messy input handling and friendly error messages."""
import io
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.samples import SAMPLES_DIR

from .mappings import (
    SAMPLES,
    basket_params,
    clv_params,
    forecast_params,
    recommendation_params,
)

client = TestClient(app, raise_server_exceptions=False)
RETAIL = SAMPLES["office-home-retail"]
RC = RETAIL["cols"]


def retail_bytes() -> bytes:
    return (SAMPLES_DIR / RETAIL["file"]).read_bytes()


def post(mode, params, data=None, name="data.csv"):
    return client.post(
        f"/api/analyze/{mode}",
        files={"file": (name, data if data is not None else retail_bytes(), "text/csv")},
        data={"params": json.dumps(params)},
    )


# --------------------------------------------------------------------------- basic API
def test_health_and_samples():
    assert client.get("/api/health").json() == {"status": "ok"}
    samples = client.get("/api/samples").json()
    assert len(samples) == 3
    for s in samples:
        assert s["rows"] > 1000
        download = client.get(f"/api/samples/{s['id']}")
        assert download.status_code == 200 and download.text.count("\n") > 1000
    assert client.get("/api/samples/unknown").status_code == 404


def test_inspect_returns_profile():
    res = client.post("/api/inspect", files={"file": ("a.csv", retail_bytes(), "text/csv")})
    assert res.status_code == 200
    body = res.json()
    kinds = {c["name"]: c["kind"] for c in body["columns"]}
    assert kinds["InvoiceDate"] == "date" and kinds["Quantity"] == "number" and kinds["Category"] == "text"
    category = next(c for c in body["columns"] if c["name"] == "Category")
    assert category["values"] == ["Furniture", "Home Decor", "Office Supplies", "Technology"]
    assert len(body["preview"]) == 8 and body["rows"] > 1000


@pytest.mark.parametrize(
    "mode,params",
    [
        ("clv", clv_params(RC)),
        ("recommendation", recommendation_params(RC)),
        ("basket", basket_params(RC)),
        ("forecast", forecast_params(RC, "Furniture", "North", periods=6, use_additional=True)),
    ],
)
def test_every_mode_over_http(mode, params):
    res = post(mode, params)
    assert res.status_code == 200, res.text
    assert res.json()["mode"] == mode
    assert res.json()["insights"]


def test_unknown_mode_and_bad_params():
    assert post("nope", {}).status_code == 404
    res = client.post(
        "/api/analyze/clv",
        files={"file": ("a.csv", retail_bytes(), "text/csv")},
        data={"params": "not json"},
    )
    assert res.status_code == 400 and "error" in res.json()


# --------------------------------------------------------------------------- friendly errors
def error_of(mode, params, data=None, name="data.csv"):
    res = post(mode, params, data, name)
    assert res.status_code == 400, f"expected a friendly 400, got {res.status_code}: {res.text[:200]}"
    return res.json()["error"]


def test_missing_selection():
    params = clv_params(RC)
    del params["quantity"]
    assert "select the Quantity Column" in error_of("clv", params)


def test_unknown_column():
    params = clv_params(RC)
    params["quantity"] = "Nope"
    assert "'Nope'" in error_of("clv", params) and "not found" in error_of("clv", params)


def test_same_column_twice():
    params = clv_params(RC)
    params["unit_price"] = params["quantity"]
    message = error_of("clv", params)
    assert "Quantity Column" in message and "Unit Price Column" in message and "different column" in message


def test_text_column_chosen_as_number():
    params = clv_params(RC)
    params["quantity"] = "ProductName"
    assert "does not look like numbers" in error_of("clv", params)


def test_text_column_chosen_as_date():
    params = clv_params(RC)
    params["invoice_date"] = "Region"
    assert "does not look like dates" in error_of("clv", params)


def test_excel_file_rejected_kindly():
    assert "Save As > CSV" in error_of("clv", clv_params(RC), data=b"PK\x03\x04", name="book.xlsx")


def test_empty_and_garbage_files():
    assert "empty" in error_of("clv", clv_params(RC), data=b"")
    assert "two columns" in error_of("clv", clv_params(RC), data=b"hello world")


def test_forecast_input_validation():
    base = forecast_params(RC, "Furniture", periods=6)
    assert "whole number" in error_of("forecast", {**base, "periods": "abc"})
    assert "between 1 and 36" in error_of("forecast", {**base, "periods": 0})
    assert "between 1 and 36" in error_of("forecast", {**base, "periods": 99})
    assert "choose a value for the Filter Column" in error_of("forecast", {**base, "filter_value": ""})
    assert "No sales were found" in error_of("forecast", {**base, "filter_value": "Nonexistent"})
    extra = forecast_params(RC, "Furniture", periods=6, use_additional=True)
    assert "Additional Filter Column" in error_of("forecast", {**extra, "additional_value": ""})
    same = {**base, "additional_column": base["filter_column"], "additional_value": "x"}
    assert "different column" in error_of("forecast", same)


def test_forecast_needs_enough_history():
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    short = df[(df["InvoiceDate"] >= "2026-06-01") & (df["InvoiceDate"] <= "2026-08-31")]
    message = error_of("forecast", forecast_params(RC, periods=3), data=short.to_csv(index=False).encode())
    assert "At least 6 months" in message


def test_basket_with_single_item_baskets():
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    one_per_invoice = df.drop_duplicates("InvoiceNo").copy()
    one_per_invoice["CustomerID"] = [f"X{i}" for i in range(len(one_per_invoice))]
    message = error_of("basket", basket_params(RC), data=one_per_invoice.to_csv(index=False).encode())
    assert "single product" in message


def test_too_few_customers_for_segments():
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    two = df[df["CustomerID"].isin(df["CustomerID"].unique()[:2])]
    assert "At least 3 different customers" in error_of("clv", clv_params(RC), data=two.to_csv(index=False).encode())


# --------------------------------------------------------------------------- messy but valid data
def test_returns_are_excluded_with_a_warning():
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    df.loc[df.index[:25], "Quantity"] = -1
    res = post("clv", clv_params(RC), data=df.to_csv(index=False).encode())
    assert res.status_code == 200
    assert any("zero or negative" in w for w in res.json()["warnings"])


def test_blank_rows_and_missing_values_are_skipped_with_a_warning():
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    df.loc[df.index[:30], "UnitPrice"] = None
    res = post("clv", clv_params(RC), data=df.to_csv(index=False).encode())
    assert res.status_code == 200
    assert any("Skipped 30" in w for w in res.json()["warnings"])


def test_other_file_layouts_give_the_same_answer():
    """Semicolons, decimal commas, currency symbols and a different date layout must not change results."""
    baseline = post("clv", clv_params(RC)).json()
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"]).dt.strftime("%d.%m.%Y")
    df["UnitPrice"] = df["UnitPrice"].map(lambda v: f"{v:.2f}".replace(".", ",") + " €")
    raw = df.to_csv(index=False, sep=";").encode("cp1252")
    res = post("clv", clv_params(RC), data=raw)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["kpis"]["total_revenue"] == pytest.approx(baseline["kpis"]["total_revenue"], rel=1e-9)
    assert [s["customers"] for s in body["segments"]] == [s["customers"] for s in baseline["segments"]]


def test_forecast_drops_a_partial_last_month():
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    trimmed = df[df["InvoiceDate"] <= "2026-09-12"]
    res = post("forecast", forecast_params(RC, periods=3), data=trimmed.to_csv(index=False).encode())
    body = res.json()
    assert body["history"][-1]["month"] == "2026-08"
    assert any("not a complete month" in w for w in body["warnings"])


def test_forecast_zero_months_are_filled():
    df = pd.read_csv(io.BytesIO(retail_bytes()))
    gap = df[~df["InvoiceDate"].str.startswith("2025-03")]
    res = post("forecast", forecast_params(RC, periods=3), data=gap.to_csv(index=False).encode())
    assert res.status_code == 200
    history = {h["month"]: h["value"] for h in res.json()["history"]}
    assert history["2025-03"] == 0 and len(history) == 36
