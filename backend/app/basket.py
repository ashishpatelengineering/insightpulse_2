"""Market Basket Analysis: which products are bought together (Apriori algorithm)."""
from __future__ import annotations

import inspect
import math
import warnings as py_warnings

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

from .common import UserError, build_frame, select_columns

SPEC = [
    ("member_number", "Member Number Column"),
    ("date", "Date Column"),
    ("product_name", "Product Name Column"),
]

SUPPORT_LADDER = [0.02, 0.01, 0.005, 0.0025]
MIN_BASKETS_FOR_PATTERN = 5
MAX_ITEMS = 150
MIN_LIFT = 1.1
MAX_RULES = 100
MAX_PAIRS = 40
TARGET_RULES = 12


def _rules_from(frequent: pd.DataFrame, n_baskets: int) -> pd.DataFrame:
    kwargs = {}
    if "num_itemsets" in inspect.signature(association_rules).parameters:
        kwargs["num_itemsets"] = n_baskets
    multi = frequent[frequent["itemsets"].apply(len) >= 2]
    if multi.empty:
        return pd.DataFrame()
    with py_warnings.catch_warnings():
        py_warnings.simplefilter("ignore")
        rules = association_rules(frequent, metric="lift", min_threshold=MIN_LIFT, **kwargs)
    if rules.empty:
        return rules
    rules = rules[(rules["consequents"].apply(len) == 1) & (rules["antecedents"].apply(len) <= 2)]
    return rules


def run(df: pd.DataFrame, params: dict) -> dict:
    cols = select_columns(df, params, SPEC)
    frame, warnings = build_frame(
        df,
        {
            "customer": (cols["member_number"], "text", "Member Number Column"),
            "date": (cols["date"], "date", "Date Column"),
            "product": (cols["product_name"], "text", "Product Name Column"),
        },
    )
    frame["day"] = frame["date"].dt.strftime("%Y-%m-%d")
    frame["basket"] = frame["customer"] + "|" + frame["day"]

    baskets = frame.groupby("basket")["product"].apply(lambda s: sorted(set(s))).tolist()
    n_baskets = len(baskets)
    if n_baskets < 30:
        raise UserError(f"Only {n_baskets} baskets were found. At least 30 are needed to find reliable product combinations.")
    sizes = pd.Series([len(b) for b in baskets])
    multi_share = float((sizes > 1).mean())
    if (sizes > 1).sum() < 10:
        raise UserError(
            "Almost every basket contains a single product, so there are no combinations to analyze. "
            "A basket is all products one member bought on the same date. Please check the Member Number and Date columns."
        )

    item_counts = pd.Series([i for b in baskets for i in b]).value_counts()
    n_products = int(len(item_counts))
    if n_products < 2:
        raise UserError("At least 2 different products are needed for market basket analysis.")

    rules = pd.DataFrame()
    frequent = pd.DataFrame()
    used_support = SUPPORT_LADDER[0]
    used_min_count = 0
    for ladder_support in SUPPORT_LADDER:
        min_support = max(ladder_support, MIN_BASKETS_FOR_PATTERN / n_baskets)
        keep_items = item_counts[item_counts >= min_support * n_baskets].head(MAX_ITEMS).index
        if len(keep_items) < 2:
            continue
        keep = set(keep_items)
        filtered = [[i for i in b if i in keep] for b in baskets]
        encoder = TransactionEncoder()
        onehot = pd.DataFrame(encoder.fit(filtered).transform(filtered), columns=encoder.columns_)
        with py_warnings.catch_warnings():
            py_warnings.simplefilter("ignore")
            frequent = apriori(onehot, min_support=min_support, use_colnames=True, max_len=3)
        rules = _rules_from(frequent, n_baskets)
        used_support = min_support
        used_min_count = int(math.ceil(min_support * n_baskets))
        if len(rules) >= TARGET_RULES:
            break

    if rules.empty:
        raise UserError(
            "No clear product combinations were found in this data. "
            "This usually means customers rarely buy the same products together. A file with more purchases per member may help."
        )

    rules = rules.sort_values(["lift", "confidence"], ascending=False).head(MAX_RULES)
    rule_rows = [
        {
            "if_buy": sorted(r.antecedents),
            "also_buy": next(iter(r.consequents)),
            "baskets": int(round(r.support * n_baskets)),
            "support": round(float(r.support) * 100, 2),
            "confidence": round(float(r.confidence) * 100, 1),
            "lift": round(float(r.lift), 2),
        }
        for r in rules.itertuples()
    ]

    # Unique product pairs, strongest links first.
    single = {next(iter(s)): sup for s, sup in zip(frequent["itemsets"], frequent["support"]) if len(s) == 1}
    pair_rows = []
    for itemset, support in zip(frequent["itemsets"], frequent["support"]):
        if len(itemset) != 2:
            continue
        a, b = sorted(itemset)
        lift = support / (single[a] * single[b])
        if lift < MIN_LIFT:
            continue
        pair_rows.append(
            {
                "product_a": a,
                "product_b": b,
                "baskets": int(round(support * n_baskets)),
                "support": round(float(support) * 100, 2),
                "lift": round(float(lift), 2),
                "confidence_a_to_b": round(float(support / single[a]) * 100, 1),
                "confidence_b_to_a": round(float(support / single[b]) * 100, 1),
            }
        )
    pair_rows.sort(key=lambda r: (r["lift"], r["baskets"]), reverse=True)
    pair_rows = pair_rows[:MAX_PAIRS]

    top_products = [
        {"product": str(name), "baskets": int(count), "pct_baskets": round(100 * count / n_baskets, 1)}
        for name, count in item_counts.head(10).items()
    ]

    insights = []
    if pair_rows:
        p = pair_rows[0]
        insights.append(
            f"{p['product_a']} and {p['product_b']} are the most closely linked pair. They appear together in {p['baskets']:,} baskets, "
            f"{p['lift']:.1f} times more often than chance would suggest."
        )
    if rule_rows:
        top_conf = max(rule_rows, key=lambda r: (r["confidence"] if len(r["if_buy"]) == 1 else 0))
        insights.append(
            f"When customers buy {' and '.join(top_conf['if_buy'])}, they also buy {top_conf['also_buy']} in {top_conf['confidence']:.0f}% of baskets. "
            "This is a strong candidate for a bundle or a 'frequently bought together' prompt."
        )
    insights.append(
        f"{multi_share:.0%} of baskets contain more than one product, and the average basket holds {sizes.mean():.1f} products."
    )

    return {
        "mode": "basket",
        "kpis": {
            "baskets": n_baskets,
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
