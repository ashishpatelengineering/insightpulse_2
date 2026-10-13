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
    ("customer_id", "Customer ID Column"),
    ("product_id", "Product ID Column"),
    ("product_name", "Product Name Column"),
    ("sales", "Sales Column"),
    ("quantity", "Quantity Column"),
    ("category", "Category Column"),
    ("sub_category", "Sub Category Column"),
]
OPTIONAL = ["product_id", "product_name", "sales", "quantity", "category", "sub_category"]

TOP_N = 5
MAX_CUSTOMERS = 2000
MAX_PRODUCTS = 2000

MIN_PRODUCTS_FOR_TEST = 3     # a customer needs this many different products to be tested
MAX_TEST_CUSTOMERS = 1500
TEST_ROUNDS = 3
VERDICT_MARGIN = 3.0          # percentage points


def _similarity(matrix: sparse.csr_matrix) -> np.ndarray:
    """Cosine similarity between products: similar when the same customers buy both."""
    norms = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=0)).ravel())
    norms[norms == 0] = 1.0
    normalized = matrix.multiply(1.0 / norms).tocsr()
    similarity = (normalized.T @ normalized).toarray().astype(np.float32)
    np.fill_diagonal(similarity, 0.0)
    return similarity


def _top_n_for(owned: np.ndarray, owned_w: np.ndarray, similarity: np.ndarray, popularity_order: np.ndarray) -> list[int]:
    """Same logic as the real recommendations: similar products first, the most popular products fill any gap."""
    scores = (owned_w @ similarity[owned]) / float(owned_w.sum())
    scores[owned] = -1.0
    picks = [int(p) for p in np.argsort(scores)[::-1][:TOP_N] if scores[p] > 0]
    if len(picks) < TOP_N:
        owned_set = set(owned.tolist())
        for p in popularity_order:
            if len(picks) >= TOP_N:
                break
            if int(p) not in owned_set and int(p) not in picks:
                picks.append(int(p))
    return picks


def validate(matrix: sparse.csr_matrix, seed: int = 7) -> dict | None:
    """Hide one purchased product per customer and see whether the model brings it back.

    Compared with the simplest alternative, recommending the most popular products to everyone.
    Returns None when there are too few customers with enough history to test fairly.
    """
    n_products = matrix.shape[1]
    counts = np.diff(matrix.indptr)
    eligible = np.where(counts >= MIN_PRODUCTS_FOR_TEST)[0]
    if len(eligible) < 30:
        return None
    rng = np.random.default_rng(seed)
    coo = matrix.tocoo()
    keys = coo.row.astype(np.int64) * n_products + coo.col
    hits_model = hits_pop = tested = 0
    for _ in range(TEST_ROUNDS):
        chosen = eligible if len(eligible) <= MAX_TEST_CUSTOMERS else rng.choice(eligible, MAX_TEST_CUSTOMERS, replace=False)
        hidden = {}
        for c in chosen:
            owned = matrix.indices[matrix.indptr[c]:matrix.indptr[c + 1]]
            hidden[int(c)] = int(rng.choice(owned))
        hidden_keys = np.array([c * n_products + p for c, p in hidden.items()], dtype=np.int64)
        keep = ~np.isin(keys, hidden_keys)
        train = sparse.csr_matrix((coo.data[keep], (coo.row[keep], coo.col[keep])), shape=matrix.shape)
        similarity = _similarity(train)
        buyers = np.diff(train.tocsc().indptr)
        popularity_order = buyers.argsort()[::-1]
        for c, target in hidden.items():
            row = train.getrow(c)
            owned, owned_w = row.indices, row.data.astype(np.float32)
            if len(owned) == 0:
                continue
            tested += 1
            if target in _top_n_for(owned, owned_w, similarity, popularity_order):
                hits_model += 1
            owned_set = set(owned.tolist())
            if target in [int(p) for p in popularity_order if int(p) not in owned_set][:TOP_N]:
                hits_pop += 1
    if tested == 0:
        return None
    model_pct = 100 * hits_model / tested
    pop_pct = 100 * hits_pop / tested
    gap = model_pct - pop_pct
    # With a few hundred customers the result moves by a couple of points between runs,
    # so only a clear gap is called better or worse.
    verdict = "better" if gap >= VERDICT_MARGIN else "worse" if gap <= -VERDICT_MARGIN else "similar"
    return {
        "customers_tested": int(min(len(eligible), MAX_TEST_CUSTOMERS)),
        "model_hit_pct": round(model_pct, 1),
        "bestseller_hit_pct": round(pop_pct, 1),
        "verdict": verdict,
    }


def run(df: pd.DataFrame, params: dict) -> dict:
    cols = select_columns(df, params, SPEC, optional=OPTIONAL)
    if "product_id" not in cols and "product_name" not in cols:
        raise UserError("Please choose a Product ID Column or a Product Name Column, so that products can be told apart.")
    spec = {"customer": (cols["customer_id"], "text", "Customer ID Column")}
    # Products are told apart by ID when there is one, otherwise by name.
    if "product_id" in cols:
        spec["pid"] = (cols["product_id"], "text", "Product ID Column")
    if "product_name" in cols:
        spec["pname"] = (cols["product_name"], "text" if "product_id" not in cols else "label", "Product Name Column")
    if "sales" in cols:
        spec["sales"] = (cols["sales"], "number", "Sales Column")
    if "quantity" in cols:
        spec["qty"] = (cols["quantity"], "number", "Quantity Column")
    if "category" in cols:
        spec["cat"] = (cols["category"], "label", "Category Column")
    if "sub_category" in cols:
        spec["sub"] = (cols["sub_category"], "label", "Sub Category Column")
    frame, warnings = build_frame(df, spec)
    if "pid" not in frame:
        frame["pid"] = frame["pname"]
    if "pname" not in frame:
        frame["pname"] = frame["pid"]
    has_sales, has_category, has_sub = "sales" in frame, "cat" in frame, "sub" in frame
    for missing, default in (("cat", ""), ("sub", "")):
        if missing not in frame:
            frame[missing] = default

    # Returns and cancellations are not purchases.
    if "qty" in frame:
        keep = frame["qty"] > 0
    elif has_sales:
        keep = frame["sales"] > 0
    else:
        keep = pd.Series(True, index=frame.index)
    if int((~keep).sum()):
        warnings.append(f"Excluded {int((~keep).sum()):,} rows with a zero or negative quantity or sales value, for example returns.")
    frame = frame[keep].copy()
    if frame.empty:
        raise UserError("No rows with a positive quantity or sales value were found. Please check the Quantity and Sales columns.")
    if "qty" not in frame:
        frame["qty"] = 1.0
    if not has_sales:
        frame["sales"] = 0.0

    # One row per product with its most common name and category.
    products = frame.groupby("pid").agg(
        name=("pname", mode_of),
        category=("cat", mode_of),
        sub_category=("sub", mode_of),
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

    if has_sales:
        spend = frame.groupby("customer")["sales"].sum().sort_values(ascending=False)
    else:
        # No sales values: show the customers with the richest purchase history first.
        spend = frame.groupby("customer")["pid"].nunique().sort_values(ascending=False).astype(float)
    customer_ids = spend.index.tolist()
    customer_pos = {c: i for i, c in enumerate(customer_ids)}

    pairs = frame.groupby(["customer", "pid"])["qty"].sum().reset_index()
    rows_idx = pairs["customer"].map(customer_pos).to_numpy()
    cols_idx = pairs["pid"].map(product_pos).to_numpy()
    weights = np.log1p(pairs["qty"].to_numpy()).astype(np.float32)
    matrix = sparse.csr_matrix((weights, (rows_idx, cols_idx)), shape=(len(customer_ids), len(product_ids)))

    similarity = _similarity(matrix)

    popularity_order = products["buyers"].to_numpy().argsort()[::-1]
    validation = validate(matrix)

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
                "total_spend": money(spend.iloc[c_idx]) if has_sales else None,
                "products_bought": int(len(owned)),
                "top_purchases": history,
                "recommendations": recs,
            }
        )

    if len(customer_ids) > MAX_CUSTOMERS:
        warnings.append(f"Recommendations are shown for the top {MAX_CUSTOMERS:,} customers by spend.")

    avg_products = float(pairs.groupby("customer")["pid"].nunique().mean())
    return {
        "mode": "recommendation",
        "kpis": {
            "customers": int(len(customer_ids)),
            "products": int(len(product_ids)),
            "avg_products_per_customer": round(avg_products, 1),
            "total_revenue": money(frame["sales"].sum()) if has_sales else None,
            "has_category": has_category,
            "has_sub_category": has_sub,
        },
        "validation": validation,
        "customers": results,
        "warnings": warnings,
    }
