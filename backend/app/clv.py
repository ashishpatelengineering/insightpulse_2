"""Customer value segments using RFM scoring (Recency, Frequency, Monetary value).

Each customer is ranked against all other customers on three simple measures:
how recently they bought, how often they buy, and how much they spend. Each rank
becomes a score from 1 (lowest) to 5 (highest). The scores place every customer in
one of five easy to understand segments. This describes past behavior. It is not a
prediction of future value.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import UserError, build_frame, money, select_columns

SPEC = [
    ("customer_id", "Customer ID Column"),
    ("invoice_date", "Date Column"),
    ("sales", "Sales Column"),
    ("quantity", "Quantity Column"),
    ("unit_price", "Unit Price Column"),
    ("invoice_id", "Order ID Column"),
]
OPTIONAL = ["sales", "quantity", "unit_price", "invoice_id"]

SEGMENTS = [
    ("Champions", "Bought recently, buy often and spend the most."),
    ("Loyal Customers", "Buy regularly and spend well."),
    ("Promising Customers", "Bought recently, with fewer orders or lower spend so far."),
    ("At Risk", "Used to buy often or spend well, with a long gap since their last purchase."),
    ("Hibernating", "Low spend and a long gap since their last purchase."),
]

MIN_CUSTOMERS = 10


def _pct(value: float) -> int:
    """Whole-number percent that rounds .5 upward, so text matches what the screen shows."""
    return int(np.floor(value + 0.5))
MAX_CUSTOMER_ROWS = 20000


def _score(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Rank customers against each other and turn the rank into a score from 1 to 5.

    Customers with the same value get the same score.
    """
    ranked = values.rank(pct=True, method="average", ascending=higher_is_better)
    return np.ceil(ranked * 5).clip(1, 5).astype(int)


def _segment(r: int, f: int, m: int) -> str:
    fm = (f + m) / 2
    if r >= 4 and fm >= 4:
        return "Champions"
    if r >= 3 and fm >= 3:
        return "Loyal Customers"
    if r >= 3:
        return "Promising Customers"
    if fm >= 3:
        return "At Risk"
    return "Hibernating"


def run(df: pd.DataFrame, params: dict) -> dict:
    cols = select_columns(df, params, SPEC, optional=OPTIONAL)
    has_sales = "sales" in cols
    if not has_sales and not ("quantity" in cols and "unit_price" in cols):
        raise UserError("Please choose a Sales Column, or choose both a Quantity Column and a Unit Price Column, so that spending can be calculated.")
    spec = {
        "customer": (cols["customer_id"], "text", "Customer ID Column"),
        "date": (cols["invoice_date"], "date", "Date Column"),
    }
    if has_sales:
        spec["amount"] = (cols["sales"], "number", "Sales Column")
    else:
        spec["qty"] = (cols["quantity"], "number", "Quantity Column")
        spec["price"] = (cols["unit_price"], "number", "Unit Price Column")
    if "invoice_id" in cols:
        spec["invoice"] = (cols["invoice_id"], "text", "Order ID Column")
    frame, warnings = build_frame(df, spec)

    if not has_sales:
        frame["amount"] = frame["qty"] * frame["price"]
    # A positive amount is a purchase. A negative amount is a return or cancellation.
    zero_rows = int((frame["amount"] == 0).sum())
    if zero_rows:
        warnings.append(f"Excluded {zero_rows:,} rows with an amount of zero.")
    returns = frame[frame["amount"] < 0]
    frame = frame[frame["amount"] > 0].copy()
    if frame.empty:
        raise UserError("No purchases with a positive amount were found. Please check the Sales, Quantity and Unit Price columns.")

    if "invoice" not in frame:
        # No order ID: one order is all of a customer's purchases on one day.
        frame["invoice"] = frame["customer"] + "|" + frame["date"].dt.strftime("%Y-%m-%d")
        warnings.append("No Order ID Column was chosen, so all purchases by one customer on one day are counted as one order.")
    reference = frame["date"].max().normalize() + pd.Timedelta(days=1)

    customers = frame.groupby("customer").agg(
        gross_spend=("amount", "sum"),
        orders=("invoice", "nunique"),
        first_purchase=("date", "min"),
        last_purchase=("date", "max"),
    )
    # Spend is net of returns. Returns are not orders and do not count as a purchase date.
    returned = (-returns.groupby("customer")["amount"].sum()).reindex(customers.index).fillna(0.0)
    customers["total_spend"] = customers["gross_spend"] - returned
    if len(returns):
        warnings.append(
            f"{len(returns):,} return or cancellation rows (worth {float(-returns['amount'].sum()):,.0f}) were subtracted from customer spend. "
            "Returns are not counted as orders."
        )
    if len(customers) < MIN_CUSTOMERS:
        raise UserError(
            f"At least {MIN_CUSTOMERS} different customers are needed to rank customers fairly. Your file has {len(customers)}."
        )

    customers["avg_order_value"] = customers["gross_spend"] / customers["orders"]
    customers["days_since_last"] = (reference - customers["last_purchase"].dt.normalize()).dt.days

    customers["r"] = _score(customers["days_since_last"], higher_is_better=False)
    customers["f"] = _score(customers["orders"])
    customers["m"] = _score(customers["total_spend"])
    customers["segment"] = [_segment(r, f, m) for r, f, m in zip(customers["r"], customers["f"], customers["m"])]

    total_revenue = float(customers["total_spend"].sum())
    n_customers = len(customers)
    segments = []
    for name, description in SEGMENTS:
        part = customers[customers["segment"] == name]
        if part.empty:
            continue
        segments.append(
            {
                "segment": name,
                "description": description,
                "customers": int(len(part)),
                "pct_customers": round(100 * len(part) / n_customers, 1),
                "revenue": money(part["total_spend"].sum()),
                "pct_revenue": round(100 * part["total_spend"].sum() / total_revenue, 1) if total_revenue else 0.0,
                "avg_spend": money(part["total_spend"].mean()),
                "avg_orders": round(float(part["orders"].mean()), 1),
                "avg_order_value": money(part["avg_order_value"].mean()),
                "avg_days_since_last": int(round(part["days_since_last"].mean())),
            }
        )
    by_name = {s_["segment"]: s_ for s_ in segments}

    insights = []
    champions = by_name.get("Champions")
    if champions:
        insights.append(
            f"{_pct(champions['pct_customers'])}% of your customers ({champions['customers']:,} Champions) generate {_pct(champions['pct_revenue'])}% of revenue."
        )
    at_risk = by_name.get("At Risk")
    if at_risk:
        insights.append(
            f"{at_risk['customers']:,} At Risk customers account for {_pct(at_risk['pct_revenue'])}% of revenue and last bought {at_risk['avg_days_since_last']:,} days ago on average."
        )

    table = customers.sort_values("total_spend", ascending=False)
    if len(table) > MAX_CUSTOMER_ROWS:
        table = table.head(MAX_CUSTOMER_ROWS)
        warnings.append(f"The customer list shows the top {MAX_CUSTOMER_ROWS:,} customers by spend. Segment totals include everyone.")
    rows = [
        {
            "customer_id": str(cid),
            "segment": r.segment,
            "rfm": f"{int(r.r)}-{int(r.f)}-{int(r.m)}",
            "total_spend": money(r.total_spend),
            "orders": int(r.orders),
            "avg_order_value": money(r.avg_order_value),
            "first_purchase": r.first_purchase.strftime("%Y-%m-%d"),
            "last_purchase": r.last_purchase.strftime("%Y-%m-%d"),
            "days_since_last": int(r.days_since_last),
        }
        for cid, r in table.iterrows()
    ]

    return {
        "mode": "clv",
        "kpis": {
            "customers": n_customers,
            "total_revenue": money(total_revenue),
            "avg_spend": money(customers["total_spend"].mean()),
            "avg_order_value": money(frame["amount"].sum() / frame["invoice"].nunique()),
            "orders": int(frame["invoice"].nunique()),
            "orders_per_customer": round(float(customers["orders"].mean()), 1),
            "repeat_rate": round(100 * float((customers["orders"] >= 2).mean()), 1),
            "period_start": frame["date"].min().strftime("%Y-%m-%d"),
            "period_end": frame["date"].max().strftime("%Y-%m-%d"),
        },
        "segments": segments,
        "customers": rows,
        "insights": insights,
        "warnings": warnings,
    }
