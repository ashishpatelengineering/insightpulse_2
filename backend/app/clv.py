"""Customer Lifetime Value: group customers into three value segments."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from .common import UserError, build_frame, money, select_columns

SPEC = [
    ("customer_id", "Customer ID Column"),
    ("invoice_id", "Invoice ID Column"),
    ("invoice_date", "Invoice Date Column"),
    ("quantity", "Quantity Column"),
    ("unit_price", "Unit Price Column"),
]

SEGMENTS = [
    {
        "name": "Low Value",
        "description": "Smaller or occasional buyers.",
        "action": "Encourage a second purchase with a welcome offer, reminders and low cost product suggestions.",
    },
    {
        "name": "Medium Value",
        "description": "Steady customers with room to grow.",
        "action": "Increase spend with bundles, loyalty rewards and recommendations from related categories.",
    },
    {
        "name": "High Value",
        "description": "Your most valuable customers.",
        "action": "Protect this group with VIP service, early access to new products and personal outreach.",
    },
]

MAX_CUSTOMER_ROWS = 20000
AT_RISK_DAYS = 90


def run(df: pd.DataFrame, params: dict) -> dict:
    cols = select_columns(df, params, SPEC)
    frame, warnings = build_frame(
        df,
        {
            "customer": (cols["customer_id"], "text", "Customer ID Column"),
            "invoice": (cols["invoice_id"], "text", "Invoice ID Column"),
            "date": (cols["invoice_date"], "date", "Invoice Date Column"),
            "qty": (cols["quantity"], "number", "Quantity Column"),
            "price": (cols["unit_price"], "number", "Unit Price Column"),
        },
    )

    valid = (frame["qty"] > 0) & (frame["price"] > 0)
    removed = int((~valid).sum())
    if removed:
        warnings.append(
            f"Excluded {removed:,} rows with a zero or negative quantity or price, for example returns or cancellations."
        )
    frame = frame[valid].copy()
    if frame.empty:
        raise UserError("No rows with a positive quantity and unit price were found. Please check the Quantity and Unit Price columns.")

    frame["amount"] = frame["qty"] * frame["price"]
    reference = frame["date"].max().normalize() + pd.Timedelta(days=1)

    customers = frame.groupby("customer").agg(
        total_spend=("amount", "sum"),
        orders=("invoice", "nunique"),
        units=("qty", "sum"),
        first_purchase=("date", "min"),
        last_purchase=("date", "max"),
    )
    if len(customers) < 3:
        raise UserError("At least 3 different customers are needed to create three segments. Your file has " f"{len(customers)}.")
    if customers["total_spend"].round(2).nunique() < 3:
        raise UserError("Customers need at least three different spend amounts to be grouped into three segments.")

    customers["avg_order_value"] = customers["total_spend"] / customers["orders"]
    customers["days_since_last"] = (reference - customers["last_purchase"].dt.normalize()).dt.days

    # Segmenting on a log scale keeps a few very large customers from squeezing everyone else into one group.
    features = np.log1p(customers["total_spend"].to_numpy()).reshape(-1, 1)
    model = KMeans(n_clusters=3, n_init=10, random_state=42).fit(features)
    order = np.argsort(model.cluster_centers_.ravel())
    rank = {int(old): new for new, old in enumerate(order)}
    customers["segment_index"] = [rank[int(label)] for label in model.labels_]

    total_revenue = float(customers["total_spend"].sum())
    n_customers = len(customers)
    segments = []
    for idx, meta in enumerate(SEGMENTS):
        part = customers[customers["segment_index"] == idx]
        segments.append(
            {
                "segment": meta["name"],
                "description": meta["description"],
                "action": meta["action"],
                "customers": int(len(part)),
                "pct_customers": round(100 * len(part) / n_customers, 1),
                "revenue": money(part["total_spend"].sum()),
                "pct_revenue": round(100 * part["total_spend"].sum() / total_revenue, 1) if total_revenue else 0.0,
                "avg_spend": money(part["total_spend"].mean()),
                "min_spend": money(part["total_spend"].min()),
                "max_spend": money(part["total_spend"].max()),
                "avg_orders": round(float(part["orders"].mean()), 1),
                "avg_order_value": money(part["avg_order_value"].mean()),
                "avg_days_since_last": int(round(part["days_since_last"].mean())),
            }
        )

    high, medium, low = segments[2], segments[1], segments[0]
    insights = [
        f"{high['pct_customers']:.0f}% of your customers ({high['customers']:,} High Value customers) generate {high['pct_revenue']:.0f}% of total revenue.",
        f"Medium Value customers make up {medium['pct_customers']:.0f}% of customers and {medium['pct_revenue']:.0f}% of revenue. Moving some of them up is the biggest growth opportunity.",
        f"Low Value customers are {low['pct_customers']:.0f}% of customers but only {low['pct_revenue']:.0f}% of revenue. A simple second purchase campaign can help here.",
    ]
    at_risk = int(((customers["segment_index"] == 2) & (customers["days_since_last"] > AT_RISK_DAYS)).sum())
    if at_risk:
        insights.append(
            f"{at_risk:,} High Value customers have not purchased in over {AT_RISK_DAYS} days. A personal win back message is worth considering."
        )

    table = customers.sort_values("total_spend", ascending=False)
    truncated = len(table) > MAX_CUSTOMER_ROWS
    if truncated:
        table = table.head(MAX_CUSTOMER_ROWS)
        warnings.append(f"The customer list shows the top {MAX_CUSTOMER_ROWS:,} customers by spend. Segment totals include everyone.")
    rows = [
        {
            "customer_id": str(cid),
            "segment": SEGMENTS[int(r.segment_index)]["name"],
            "total_spend": money(r.total_spend),
            "orders": int(r.orders),
            "units": int(r.units),
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
            "period_start": frame["date"].min().strftime("%Y-%m-%d"),
            "period_end": frame["date"].max().strftime("%Y-%m-%d"),
        },
        "segments": segments,
        "customers": rows,
        "insights": insights,
        "warnings": warnings,
    }
