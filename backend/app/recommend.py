"""Product Recommendation: suggest the next products for each customer.

Method: item based collaborative filtering. Two products are similar when the same
customers buy both (cosine similarity). A customer's suggestions are the products
most similar to what they already bought and have not bought yet.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse

from .common import UserError, build_frame, mode_of, money, select_columns

SPEC = [
    ("product_id", "Product ID Column"),
    ("product_name", "Product Name Column"),
    ("sales", "Sales Column"),
    ("category", "Category Column"),
    ("sub_category", "Sub Category Column"),
    ("quantity", "Quantity Column"),
    ("customer_id", "Customer ID Column"),
]

TOP_N = 5
MAX_CUSTOMERS = 2000
MAX_PRODUCTS = 3000


def run(df: pd.DataFrame, params: dict) -> dict:
    cols = select_columns(df, params, SPEC)
    frame, warnings = build_frame(
        df,
        {
            "pid": (cols["product_id"], "text", "Product ID Column"),
            "pname": (cols["product_name"], "text", "Product Name Column"),
            "sales": (cols["sales"], "number", "Sales Column"),
            "cat": (cols["category"], "text", "Category Column"),
            "sub": (cols["sub_category"], "text", "Sub Category Column"),
            "qty": (cols["quantity"], "number", "Quantity Column"),
            "customer": (cols["customer_id"], "text", "Customer ID Column"),
        },
    )
    keep = frame["qty"] > 0
    if int((~keep).sum()):
        warnings.append(f"Excluded {int((~keep).sum()):,} rows with a zero or negative quantity, for example returns.")
    frame = frame[keep].copy()
    if frame.empty:
        raise UserError("No rows with a positive quantity were found. Please check the Quantity Column.")

    # One row per product with its most common name and category.
    products = frame.groupby("pid").agg(
        name=("pname", mode_of),
        category=("cat", mode_of),
        sub_category=("sub", mode_of),
        revenue=("sales", "sum"),
        units=("qty", "sum"),
        buyers=("customer", "nunique"),
    )
    if len(products) < 2:
        raise UserError("At least 2 different products are needed to make recommendations.")
    if frame["customer"].nunique() < 2:
        raise UserError("At least 2 different customers are needed to make recommendations.")

    if len(products) > MAX_PRODUCTS:
        products = products.sort_values("buyers", ascending=False).head(MAX_PRODUCTS)
        frame = frame[frame["pid"].isin(products.index)]
        warnings.append(f"Recommendations use the {MAX_PRODUCTS:,} most purchased products.")

    product_ids = products.index.tolist()
    product_pos = {p: i for i, p in enumerate(product_ids)}

    spend = frame.groupby("customer")["sales"].sum().sort_values(ascending=False)
    customer_ids = spend.index.tolist()
    customer_pos = {c: i for i, c in enumerate(customer_ids)}

    pairs = frame.groupby(["customer", "pid"])["qty"].sum().reset_index()
    rows_idx = pairs["customer"].map(customer_pos).to_numpy()
    cols_idx = pairs["pid"].map(product_pos).to_numpy()
    weights = np.log1p(pairs["qty"].to_numpy()).astype(np.float32)
    matrix = sparse.csr_matrix((weights, (rows_idx, cols_idx)), shape=(len(customer_ids), len(product_ids)))

    # Cosine similarity between products.
    norms = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=0)).ravel())
    norms[norms == 0] = 1.0
    normalized = matrix.multiply(1.0 / norms).tocsr()
    similarity = (normalized.T @ normalized).toarray().astype(np.float32)
    np.fill_diagonal(similarity, 0.0)

    popularity_order = products["buyers"].to_numpy().argsort()[::-1]

    names = products["name"].tolist()
    cats = products["category"].tolist()
    subs = products["sub_category"].tolist()

    results = []
    for c_idx, cid in enumerate(customer_ids[:MAX_CUSTOMERS]):
        row = matrix.getrow(c_idx)
        owned = row.indices
        owned_w = row.data.astype(np.float32)
        scores = (owned_w @ similarity[owned]) / float(owned_w.sum())
        scores[owned] = -1.0
        candidates = np.argsort(scores)[::-1][:TOP_N]
        recs = []
        for p in candidates:
            if scores[p] <= 0:
                continue
            contribution = owned_w * similarity[owned, p]
            because = owned[int(np.argmax(contribution))]
            recs.append(
                {
                    "product_id": product_ids[p],
                    "product": names[p],
                    "category": cats[p],
                    "sub_category": subs[p],
                    "match_pct": int(round(min(100.0, float(scores[p]) * 100))),
                    "reason": f"Customers who buy {names[because]} often buy this too",
                }
            )
        if len(recs) < TOP_N:
            have = {r["product_id"] for r in recs}
            owned_set = set(owned.tolist())
            for p in popularity_order:
                if len(recs) >= TOP_N:
                    break
                if int(p) in owned_set or product_ids[p] in have:
                    continue
                recs.append(
                    {
                        "product_id": product_ids[p],
                        "product": names[p],
                        "category": cats[p],
                        "sub_category": subs[p],
                        "match_pct": None,
                        "reason": "Popular with other customers",
                    }
                )
        order = np.argsort(owned_w)[::-1][:TOP_N]
        history = [
            {
                "product": names[int(owned[i])],
                "category": cats[int(owned[i])],
                "sub_category": subs[int(owned[i])],
            }
            for i in order
        ]
        results.append(
            {
                "customer_id": str(cid),
                "total_spend": money(spend.iloc[c_idx]),
                "products_bought": int(len(owned)),
                "top_purchases": history,
                "recommendations": recs,
            }
        )

    if len(customer_ids) > MAX_CUSTOMERS:
        warnings.append(f"Recommendations are shown for the top {MAX_CUSTOMERS:,} customers by spend.")

    top_products = (
        products.sort_values("revenue", ascending=False)
        .head(10)
        .reset_index()
        .apply(
            lambda r: {
                "product": r["name"],
                "category": r["category"],
                "revenue": money(r["revenue"]),
                "units": int(r["units"]),
                "customers": int(r["buyers"]),
            },
            axis=1,
        )
        .tolist()
    )
    category_mix = (
        frame.groupby("cat")["sales"].sum().sort_values(ascending=False).round(2).reset_index().rename(columns={"cat": "category", "sales": "revenue"})
    ).to_dict("records")

    avg_products = float(pairs.groupby("customer")["pid"].nunique().mean())
    insights = [
        f"Recommendations were created for {len(results):,} customers across {len(product_ids):,} products.",
        f"On average each customer has bought {avg_products:.1f} different products, so there is room to suggest more.",
    ]
    best = max(results, key=lambda r: r["recommendations"][0]["match_pct"] or 0) if results and results[0]["recommendations"] else None
    if best and best["recommendations"][0]["match_pct"]:
        insights.append(
            f"Strongest match: customer {best['customer_id']} and {best['recommendations'][0]['product']} ({best['recommendations'][0]['match_pct']}% match)."
        )

    return {
        "mode": "recommendation",
        "kpis": {
            "customers": int(len(customer_ids)),
            "products": int(len(product_ids)),
            "avg_products_per_customer": round(avg_products, 1),
            "total_revenue": money(frame["sales"].sum()),
        },
        "customers": results,
        "top_products": top_products,
        "category_mix": category_mix,
        "insights": insights,
        "warnings": warnings,
    }
