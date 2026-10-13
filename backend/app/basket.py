"""Market Basket Analysis: which products are bought together.

A basket is one order: all products with the same order ID. Without an order ID, a basket is all
products one customer bought on the same date. For every pair of products the
analysis counts how many baskets contain both, then reports the standard association measures:

  support      share of all baskets that contain both products
  confidence   how often the second product is in the basket when the first one is
  lift         how much more often the two are bought together than chance alone would give

Pairs are counted exactly with a sparse matrix product, so large files stay fast and light.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import sparse

from .common import UserError, build_frame, select_columns

SPEC = [
    ("product_name", "Product Column"),
    ("transaction_id", "Order ID Column"),
    ("member_number", "Customer Column"),
    ("date", "Date Column"),
]
OPTIONAL = ["transaction_id", "member_number", "date"]

SUPPORT_LADDER = [0.02, 0.01, 0.005, 0.0025]   # tried in turn until enough pairs are found
MIN_BASKETS_FOR_PATTERN = 5                    # a pair must appear in at least this many baskets
MAX_ITEMS = 1000
MIN_LIFT = 1.1
MAX_RULES = 100
MAX_PAIRS = 40
TARGET_PAIRS = 6


def _pairs(matrix: sparse.csr_matrix, item_counts: np.ndarray, n_baskets: int, min_count: int):
    """All product pairs bought together in at least min_count baskets with lift of at least MIN_LIFT."""
    keep = np.where(item_counts >= min_count)[0]
    if len(keep) > MAX_ITEMS:
        keep = keep[np.argsort(-item_counts[keep], kind="stable")[:MAX_ITEMS]]
    if len(keep) < 2:
        return []
    sub = matrix[:, keep]
    co = sparse.triu(sub.T @ sub, k=1).tocoo()
    together = co.data.astype(np.int64)
    first, second = keep[co.row], keep[co.col]
    lift = together * n_baskets / (item_counts[first].astype(np.float64) * item_counts[second])
    ok = (together >= min_count) & (lift >= MIN_LIFT)
    return list(zip(first[ok], second[ok], together[ok], lift[ok]))


def run(df: pd.DataFrame, params: dict) -> dict:
    cols = select_columns(df, params, SPEC, optional=OPTIONAL)
    by_order = "transaction_id" in cols
    if not by_order and not ("member_number" in cols and "date" in cols):
        raise UserError("Please choose an Order ID Column, or choose both a Customer Column and a Date Column, so that the products in each basket can be grouped.")
    spec = {"product": (cols["product_name"], "text", "Product Column")}
    if by_order:
        spec["order"] = (cols["transaction_id"], "text", "Order ID Column")
    else:
        spec["customer"] = (cols["member_number"], "text", "Customer Column")
        spec["date"] = (cols["date"], "date", "Date Column")
    frame, warnings = build_frame(df, spec)
    key = frame["order"] if by_order else frame["customer"] + "|" + frame["date"].dt.strftime("%Y-%m-%d")
    basket_codes, _ = pd.factorize(key)
    item_codes, item_names = pd.factorize(frame["product"])
    n_baskets = int(basket_codes.max()) + 1
    del frame

    if n_baskets < 30:
        raise UserError(f"Only {n_baskets} baskets were found. At least 30 are needed to find reliable product combinations.")
    matrix = sparse.csr_matrix(
        (np.ones(len(basket_codes), dtype=np.int32), (basket_codes, item_codes)), shape=(n_baskets, len(item_names))
    )
    matrix.data[:] = 1   # a product counts once per basket, however many lines it appears on
    sizes = np.asarray(matrix.sum(axis=1)).ravel()
    multi_share = float((sizes > 1).mean())
    if (sizes > 1).sum() < 10:
        raise UserError(
            "Almost every basket contains a single product, so there are no combinations to analyze. "
            "A basket is one order: all products with the same order ID, or all products one customer bought on the same date. "
            "Please check the Order ID, or the Customer and Date columns."
        )
    item_counts = np.asarray(matrix.sum(axis=0)).ravel().astype(np.int64)
    n_products = int(len(item_names))
    if n_products < 2:
        raise UserError("At least 2 different products are needed for market basket analysis.")

    found: list = []
    used_support, used_min_count = SUPPORT_LADDER[0], 0
    for ladder_support in SUPPORT_LADDER:
        min_support = max(ladder_support, MIN_BASKETS_FOR_PATTERN / n_baskets)
        min_count = int(math.ceil(min_support * n_baskets - 1e-9))
        found = _pairs(matrix, item_counts, n_baskets, min_count)
        used_support, used_min_count = min_support, min_count
        if len(found) >= TARGET_PAIRS:
            break

    if not found:
        raise UserError(
            "No clear product combinations were found in this data. "
            "This usually means customers rarely buy the same products together. A file with more purchases per customer may help."
        )

    pair_rows = []
    rule_rows = []
    for i, j, together, lift in found:
        a, b = sorted((str(item_names[i]), str(item_names[j])))
        count_a = item_counts[i] if a == item_names[i] else item_counts[j]
        count_b = item_counts[j] if a == item_names[i] else item_counts[i]
        support = together / n_baskets
        pair_rows.append(
            {
                "product_a": a,
                "product_b": b,
                "baskets": int(together),
                "support": round(100 * support, 2),
                "lift": round(float(lift), 2),
                "confidence_a_to_b": round(100 * together / count_a, 1),
                "confidence_b_to_a": round(100 * together / count_b, 1),
            }
        )
        for x, y, count_x in ((a, b, count_a), (b, a, count_b)):
            rule_rows.append(
                {
                    "if_buy": [x],
                    "also_buy": y,
                    "baskets": int(together),
                    "support": round(100 * support, 2),
                    "confidence": round(100 * together / count_x, 1),
                    "lift": round(float(lift), 2),
                }
            )
    pair_rows.sort(key=lambda r: (r["lift"], r["baskets"]), reverse=True)
    pair_rows = pair_rows[:MAX_PAIRS]
    rule_rows.sort(key=lambda r: (r["lift"], r["confidence"]), reverse=True)
    rule_rows = rule_rows[:MAX_RULES]

    order = np.argsort(-item_counts, kind="stable")[:10]
    top_products = [
        {"product": str(item_names[k]), "baskets": int(item_counts[k]), "pct_baskets": round(100 * item_counts[k] / n_baskets, 1)}
        for k in order
    ]

    insights = []
    p = pair_rows[0]
    insights.append(
        f"{p['product_a']} and {p['product_b']} are the most closely linked pair. They appear together in {p['baskets']:,} baskets, "
        f"{p['lift']:.1f} times more often than chance would suggest."
    )
    top_conf = max(rule_rows, key=lambda r: r["confidence"])
    insights.append(
        f"When customers buy {top_conf['if_buy'][0]}, they also buy {top_conf['also_buy']} in {top_conf['confidence']:.0f}% of baskets. "
        "This pair is a candidate for a bundle or a 'frequently bought together' prompt."
    )

    return {
        "mode": "basket",
        "kpis": {
            "baskets": n_baskets,
            "basket_by": "order" if by_order else "customer_day",
            "products": n_products,
            "avg_basket_size": round(float(sizes.mean()), 2),
            "rules_found": int(len(rule_rows)),
            "min_baskets": used_min_count,
            "min_support_pct": round(used_support * 100, 2),
        },
        "rules": rule_rows,
        "pairs": pair_rows,
        "top_products": top_products,
        "insights": insights,
        "warnings": warnings,
    }
