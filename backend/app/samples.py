"""Registry of the bundled sample datasets."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"

SAMPLES = [
    {
        "id": "office-home-retail",
        "file": "sample_office_home_retail.csv",
        "name": "Office and Home Retail",
        "description": "Three years of store sales across four regions.",
    },
    {
        "id": "grocery-supermarket",
        "file": "sample_grocery_supermarket.csv",
        "name": "Grocery and Daily Essentials",
        "description": "Three years of supermarket purchases across four stores.",
    },
    {
        "id": "online-electronics",
        "file": "sample_online_electronics.csv",
        "name": "Online Electronics Store",
        "description": "Three years of online orders across four sales channels.",
    },
    {
        "id": "online-fashion",
        "file": "sample_online_fashion.csv",
        "name": "Online Fashion Store",
        "description": "Three years of fashion orders across five countries.",
    },
    {
        "id": "wholesale-cafe-supplies",
        "file": "sample_wholesale_cafe_supplies.csv",
        "name": "Cafe Supplies Wholesaler",
        "description": "Three years of supply orders from cafes and restaurants.",
    },
]


@lru_cache(maxsize=None)
def _row_count(path: str) -> int:
    with open(path, "rb") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def list_samples() -> list[dict]:
    out = []
    for sample in SAMPLES:
        path = SAMPLES_DIR / sample["file"]
        if not path.exists():
            continue
        out.append(
            {
                "id": sample["id"],
                "name": sample["name"],
                "description": sample["description"],
                "filename": sample["file"],
                "rows": _row_count(str(path)),
            }
        )
    return out


def sample_path(sample_id: str) -> Path | None:
    for sample in SAMPLES:
        if sample["id"] == sample_id:
            path = SAMPLES_DIR / sample["file"]
            return path if path.exists() else None
    return None
