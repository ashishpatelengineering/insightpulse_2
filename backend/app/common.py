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
VIEW_ROWS = 20_000   # rows returned for the on-screen data table
MAX_FILTER_VALUES = 300


class UserError(Exception):
    """An error caused by the user's file or selections. The message is shown as is."""


# ---------------------------------------------------------------------------
# Reading files
#
# Uploads can be up to 25 MB, and the hosting plan has limited memory, so a file is
# read straight from the uploaded bytes (no extra copies of the text) and, when a mode
# only needs a few columns, only those columns are loaded.
# ---------------------------------------------------------------------------
def _detect_delimiter(data: bytes, encoding: str) -> str:
    prefix = data[:65536].decode(encoding, errors="replace")
    for line in prefix.splitlines():
        if line.strip():
            counts = {d: line.count(d) for d in (",", ";", "\t", "|")}
            best = max(counts, key=counts.get)
            return best if counts[best] > 0 else ","
    return ","


def _encodings(data: bytes) -> list[str]:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return ["utf-16"]
    return ["utf-8-sig", "cp1252", "latin-1"]


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    keep = [c for c in df.columns if c and not (c.lower().startswith("unnamed:") and df[c].isna().all())]
    return df.loc[:, keep].dropna(how="all")


def _check_name(filename: str) -> None:
    if (filename or "").lower().endswith((".xlsx", ".xls", ".xlsm")):
        raise UserError("Please upload a CSV file. In Excel, choose File > Save As > CSV.")


def _read_csv(data: bytes, **kwargs):
    """Try the common text encodings in turn. Calls pandas once per attempt, on the raw bytes."""
    last_error: Exception | None = None
    for encoding in _encodings(data):
        sep = _detect_delimiter(data, encoding)
        try:
            return pd.read_csv(
                io.BytesIO(data), sep=sep, dtype=str, skipinitialspace=True, on_bad_lines="skip", encoding=encoding, **kwargs
            )
        except UnicodeDecodeError as error:
            last_error = error
            continue
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            raise UserError("No table was found in this file. Please upload a CSV with a header row.")
    raise UserError("This file could not be read. Please save it as a CSV (UTF-8) and try again.") from last_error


def _too_many_rows(rows: int) -> UserError:
    return UserError(
        f"This file has {rows:,} rows. The limit is {MAX_ROWS:,} rows. "
        "Please upload a smaller extract, for example the most recent two or three years."
    )


def read_table(data: bytes, filename: str = "", wanted: Iterable[str] | None = None) -> pd.DataFrame:
    """Read an uploaded CSV into a DataFrame of strings.

    wanted: names of the only columns to load. Used by the analysis modes to keep memory low.
    """
    if not data:
        raise UserError("The uploaded file is empty.")
    _check_name(filename)
    kwargs = {}
    if wanted is not None:
        names = {str(w).strip() for w in wanted}
        kwargs["usecols"] = lambda column: str(column).strip() in names
    df = _read_csv(data, **kwargs)
    df = _clean_columns(df)
    if wanted is None and df.shape[1] < 2:
        raise UserError("At least two columns are needed. Please check that the file is a comma separated CSV.")
    if wanted is not None and df.shape[1] == 0:
        raise UserError(
            "The selected columns were not found in this file. "
            "Please check that it is a comma separated CSV with column names in the first row."
        )
    if df.empty:
        raise UserError("The file has a header row but no data rows.")
    if len(df) > MAX_ROWS:
        raise _too_many_rows(len(df))
    return df.reset_index(drop=True)


PROFILE_CHUNK_ROWS = 40_000
PROFILE_SAMPLE_ROWS = 2000


def inspect_table(data: bytes, filename: str = "") -> dict:
    """Describe an uploaded file (rows, columns, a preview) without holding all of it in memory."""
    if not data:
        raise UserError("The uploaded file is empty.")
    _check_name(filename)
    last_error: Exception | None = None
    for encoding in _encodings(data):
        sep = _detect_delimiter(data, encoding)
        try:
            reader = pd.read_csv(
                io.BytesIO(data), sep=sep, dtype=str, skipinitialspace=True, on_bad_lines="skip", encoding=encoding, chunksize=PROFILE_CHUNK_ROWS
            )
            rows = 0
            sample = preview = None
            view_rows: list[list[str]] = []
            columns: list[str] = []
            missing: dict[str, int] = {}
            examples: dict[str, list[str]] = {}
            values: dict[str, set | None] = {}
            for chunk in reader:
                chunk = _clean_columns(chunk)
                if chunk.empty:
                    continue
                if sample is None:
                    columns = list(chunk.columns)
                    sample = chunk.head(PROFILE_SAMPLE_ROWS).copy()
                    preview = chunk.head(8).fillna("").to_dict("records")
                    missing = {c: 0 for c in columns}
                    examples = {c: [] for c in columns}
                    values = {c: set() for c in columns}
                elif len(sample) < PROFILE_SAMPLE_ROWS:
                    sample = pd.concat([sample, chunk.head(PROFILE_SAMPLE_ROWS - len(sample))], ignore_index=True)
                if len(view_rows) < VIEW_ROWS:
                    view_rows.extend(chunk[columns].head(VIEW_ROWS - len(view_rows)).fillna("").values.tolist())
                rows += len(chunk)
                if rows > MAX_ROWS:
                    raise _too_many_rows(rows)
                for column in columns:
                    series = chunk[column] if column in chunk else pd.Series(dtype=str)
                    missing[column] += int(len(chunk) - series.notna().sum())
                    non_null = series.dropna()
                    if len(examples[column]) < 3:
                        examples[column].extend(non_null.astype(str).head(3 - len(examples[column])).tolist())
                    if values[column] is not None:
                        values[column].update(non_null.astype(str).str.strip().unique().tolist())
                        if len(values[column]) > MAX_FILTER_VALUES:
                            values[column] = None
            break
        except UnicodeDecodeError as error:
            last_error = error
            continue
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            raise UserError("No table was found in this file. Please upload a CSV with a header row.")
    else:
        raise UserError("This file could not be read. Please save it as a CSV (UTF-8) and try again.") from last_error
    if sample is None:
        raise UserError("The file has a header row but no data rows.")
    if len(columns) < 2:
        raise UserError("At least two columns are needed. Please check that the file is a comma separated CSV.")
    return {
        "filename": filename,
        "rows": rows,
        "columns": profile_columns(sample, columns, missing, examples, values),
        "preview": preview,
        "view": view_rows,
    }


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
def _column_kind(sample_col: pd.Series) -> str:
    present = sample_col.notna()
    if not present.any():
        return "text"
    if to_number(sample_col)[present].notna().mean() >= 0.95:
        return "number"
    if parse_dates(sample_col)[present].notna().mean() >= 0.95:
        return "date"
    return "text"


def profile_columns(sample: pd.DataFrame, columns: list[str], missing: dict, examples: dict, values: dict) -> list[dict]:
    profile = []
    for col in columns:
        distinct = values[col]
        profile.append(
            {
                "name": col,
                "kind": _column_kind(sample[col]),
                "unique": len(distinct) if distinct is not None else MAX_FILTER_VALUES + 1,
                "missing": int(missing[col]),
                "examples": examples[col],
                "values": sorted(distinct, key=lambda v: (v.lower(), v)) if distinct else None,
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
            raise UserError(f"The column '{value}' chosen for the {label} was not found in the file. Please upload the file again or choose another column.")
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
        if kind == "label":
            # Descriptive text such as a category. Blank cells are kept and shown as "Not specified".
            out[name] = s.astype("string").str.strip().replace("", pd.NA).fillna("Not specified")
            continue
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
        raise UserError("No usable rows were found with the selected columns. Please check that each input is matched to the correct column.")
    for name, (_, kind, _) in spec.items():
        if kind in ("text", "label"):
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
