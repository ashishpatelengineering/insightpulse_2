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
        "description": "Three years of store sales across furniture, office supplies, technology and home decor in four regions.",
    },
    {
        "id": "grocery-supermarket",
        "file": "sample_grocery_supermarket.csv",
        "name": "Grocery and Daily Essentials",
        "description": "Three years of supermarket purchases with frequent, larger baskets across four stores.",
    },
    {
        "id": "online-electronics",
        "file": "sample_online_electronics.csv",
        "name": "Online Electronics Store",
        "description": "Three years of online orders for computing, mobile, audio, smart home and gaming across four sales channels.",
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
