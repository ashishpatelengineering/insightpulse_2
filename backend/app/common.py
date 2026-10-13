"""Shared helpers: reading uploads, robust date and number parsing, validation."""
from __future__ import annotations

import io
import math
import re
from typing import Any, Iterable

import numpy as np
import pandas as pd

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_ROWS = 300_000
MAX_FILTER_VALUES = 300


class UserError(Exception):
    """An error caused by the user's file or selections. The message is shown as is."""


# ---------------------------------------------------------------------------
# Reading files
# ---------------------------------------------------------------------------
def _decode(data: bytes) -> str:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise UserError("We could not read this file. Please save it as a CSV (UTF-8) and try again.")


def _detect_delimiter(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            counts = {d: line.count(d) for d in (",", ";", "\t", "|")}
            best = max(counts, key=counts.get)
            return best if counts[best] > 0 else ","
    return ","


def read_table(data: bytes, filename: str = "") -> pd.DataFrame:
    """Read an uploaded CSV into a DataFrame of strings."""
    if not data:
        raise UserError("The uploaded file is empty.")
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        raise UserError("Please upload a CSV file. In Excel, choose File > Save As > CSV.")
    text = _decode(data)
    sep = _detect_delimiter(text)
    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=sep,
            dtype=str,
            skipinitialspace=True,
            on_bad_lines="skip",
        )
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        raise UserError("We could not find a table in this file. Please upload a CSV with a header row.")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, [c for c in df.columns if c and not (c.lower().startswith("unnamed:") and df[c].isna().all())]]
    df = df.dropna(how="all")
    if df.shape[1] < 2:
        raise UserError("We could not find at least two columns. Please check that the file is a comma separated CSV.")
    if df.empty:
        raise UserError("The file has a header row but no data rows.")
    if len(df) > MAX_ROWS:
        raise UserError(
            f"This file has {len(df):,} rows. The limit is {MAX_ROWS:,} rows. "
            "Please upload a smaller extract, for example the most recent two or three years."
        )
    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Number parsing
# ---------------------------------------------------------------------------
_CURRENCY = re.compile(r"[$€£¥₹%\s]")
_NUMBER = re.compile(r"[-+]?(\d+[.,]?\d*|[.,]\d+)([eE][-+]?\d+)?")


def _parse_number(text: Any) -> float:
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return math.nan
    t = str(text).strip()
    if not t:
        return math.nan
    negative = False
    if t.startswith("(") and t.endswith(")"):
        negative, t = True, t[1:-1]
    if t.endswith("-") and t[:-1].replace(".", "", 1).replace(",", "").isdigit():
        negative, t = True, t[:-1]
    t = _CURRENCY.sub("", t)
    if not t or not re.search(r"\d", t):
        return math.nan
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+", t):
            t = t.replace(",", "")
        else:
            t = t.replace(",", ".")
    if not re.fullmatch(r"[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?", t):
        return math.nan
    try:
        value = float(t)
    except ValueError:
        return math.nan
    if not math.isfinite(value):
        return math.nan
    return -value if negative else value


def to_number(series: pd.Series) -> pd.Series:
    """Convert text such as '$1,234.50' or '1.234,50' to floats. Unreadable values become NaN."""
    if pd.api.types.is_bool_dtype(series):
        return pd.Series(np.nan, index=series.index)
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    raw = series.astype("string").str.strip()
    uniques = raw.dropna().unique()
    lookup = {u: _parse_number(u) for u in uniques}
    return pd.to_numeric(raw.map(lookup), errors="coerce").astype(float)


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y/%m/%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%m/%d/%Y",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%y",
    "%d/%m/%Y",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%y",
    "%m-%d-%Y",
    "%m-%d-%Y %H:%M:%S",
    "%d-%m-%Y",
    "%d-%m-%Y %H:%M",
    "%d-%m-%Y %H:%M:%S",
    "%d.%m.%Y",
    "%d.%m.%Y %H:%M",
    "%d-%b-%Y",
    "%d-%b-%y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%b %d %Y",
    "%Y%m%d",
]


def _parse_unique_dates(uniques: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(uniques, errors="coerce")
    if numeric.notna().mean() > 0.95 and numeric.between(20000, 80000).mean() > 0.95:
        return pd.to_datetime(numeric, unit="D", origin="1899-12-30", errors="coerce")
    best_share, best = -1.0, None
    for fmt in DATE_FORMATS:
        parsed = pd.to_datetime(uniques, format=fmt, errors="coerce")
        share = float(parsed.notna().mean())
        if share > best_share + 1e-9:
            best_share, best = share, parsed
        if share >= 0.999999:
            break
    if best_share < 0.9:
        try:
            mixed = pd.to_datetime(uniques, format="mixed", errors="coerce")
            if float(mixed.notna().mean()) > best_share:
                best = mixed
        except (ValueError, TypeError):
            pass
    return best


def parse_dates(series: pd.Series) -> pd.Series:
    """Parse dates in many common layouts. Unreadable values become NaT."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    raw = series.astype("string").str.strip()
    uniques = pd.Series(raw.dropna().unique(), dtype="string")
    if len(uniques) == 0:
        return pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    parsed = _parse_unique_dates(uniques)
    lookup = dict(zip(uniques.tolist(), pd.to_datetime(parsed).tolist()))
    out = raw.map(lookup)
    return pd.to_datetime(out, errors="coerce")


# ---------------------------------------------------------------------------
# Column profiling for the front end
# ---------------------------------------------------------------------------
def profile_table(df: pd.DataFrame) -> list[dict]:
    sample = df.head(2000)
    profile = []
    for col in df.columns:
        s = df[col]
        non_null = s.dropna()
        sample_col = sample[col]
        kind = "text"
        if sample_col.notna().any():
            if to_number(sample_col)[sample_col.notna()].notna().mean() >= 0.95:
                kind = "number"
            else:
                parsed = parse_dates(sample_col)
                if parsed[sample_col.notna()].notna().mean() >= 0.95:
                    kind = "date"
        n_unique = int(non_null.nunique())
        values: list[str] | None = None
        if 0 < n_unique <= MAX_FILTER_VALUES:
            values = sorted(non_null.astype(str).str.strip().unique().tolist(), key=lambda v: (v.lower(), v))
        profile.append(
            {
                "name": col,
                "kind": kind,
                "unique": n_unique,
                "missing": int(s.isna().sum()),
                "examples": non_null.astype(str).head(3).tolist(),
                "values": values,
            }
        )
    return profile


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def select_columns(df: pd.DataFrame, params: dict, spec: Iterable[tuple[str, str]], optional: Iterable[str] = ()) -> dict[str, str]:
    """Check that every required input is chosen, exists in the file and is used only once."""
    optional = set(optional)
    labels = dict(spec)
    chosen: dict[str, str] = {}
    for key, label in spec:
        value = params.get(key)
        value = value.strip() if isinstance(value, str) else value
        if not value:
            if key in optional:
                continue
            raise UserError(f"Please select the {label}.")
        if value not in df.columns:
            raise UserError(f"The column '{value}' chosen for the {label} was not found in your file. Please upload the file again or choose another column.")
        chosen[key] = value
    seen: dict[str, str] = {}
    for key, col in chosen.items():
        if col in seen:
            raise UserError(
                f"The {labels[seen[col]]} and the {labels[key]} both use the column '{col}'. "
                "Please choose a different column for each input."
            )
        seen[col] = key
    return chosen


def build_frame(df: pd.DataFrame, spec: dict[str, tuple[str, str, str]]) -> tuple[pd.DataFrame, list[str]]:
    """Build a clean frame. spec maps name -> (column, kind, label), where kind is text, number or date."""
    out: dict[str, pd.Series] = {}
    for name, (col, kind, label) in spec.items():
        s = df[col]
        present = s.notna() & (s.astype("string").str.strip() != "")
        if not present.any():
            raise UserError(f"The {label} ('{col}') is empty. Please choose a different column.")
        if kind == "number":
            values = to_number(s)
            share = float(values[present].notna().mean())
            if share < 0.8:
                raise UserError(f"The {label} ('{col}') does not look like numbers. Please choose a column that holds numeric values.")
        elif kind == "date":
            values = parse_dates(s)
            share = float(values[present].notna().mean())
            if share < 0.8:
                raise UserError(f"The {label} ('{col}') does not look like dates. Please choose a column that holds dates.")
        else:
            values = s.astype("string").str.strip().replace("", pd.NA)
        out[name] = values
    frame = pd.DataFrame(out)
    before = len(frame)
    frame = frame.dropna().reset_index(drop=True)
    warnings: list[str] = []
    if len(frame) < before:
        warnings.append(f"Skipped {before - len(frame):,} of {before:,} rows that had missing or unreadable values in the selected columns.")
    if frame.empty:
        raise UserError("No usable rows were found with the selected columns. Please check that you matched each input to the right column.")
    for name, (_, kind, _) in spec.items():
        if kind == "text":
            frame[name] = frame[name].astype(str)
    return frame, warnings


def mode_of(series: pd.Series) -> Any:
    counts = series.value_counts()
    return counts.index[0] if len(counts) else None


def to_jsonable(obj: Any) -> Any:
    """Recursively convert numpy and pandas values into plain JSON safe values."""
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        value = float(obj)
        return value if math.isfinite(value) else None
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return None if pd.isna(obj) else obj.strftime("%Y-%m-%d")
    if obj is pd.NaT or obj is pd.NA:
        return None
    if isinstance(obj, np.ndarray):
        return to_jsonable(obj.tolist())
    return obj


def money(value: float) -> float:
    return round(float(value), 2)
