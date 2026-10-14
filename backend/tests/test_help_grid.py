"""The customer group grid shown on the Help page must match the rule the analysis applies."""
import re
from pathlib import Path

from app.clv import _segment

TEXT_JS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "content" / "text.js"


def _grid_rows():
    source = TEXT_JS.read_text(encoding="utf-8")
    block = source[source.index("export const GROUP_GRID"):]
    rows = re.findall(r"\[((?:\"[^\"]+\",?\s*){5})\]", block)
    return [re.findall(r"\"([^\"]+)\"", row) for row in rows]


def test_grid_matches_segment_rule():
    rows = _grid_rows()
    assert len(rows) == 3
    bands = [[4, 4.5, 5], [3, 3.5], [1, 1.5, 2, 2.5]]
    for row, band in zip(rows, bands):
        for r in range(1, 6):
            groups = {
                _segment(r, f, m)
                for f in range(1, 6)
                for m in range(1, 6)
                if (f + m) / 2 in band
            }
            assert groups == {row[r - 1]}, (r, band, groups)
