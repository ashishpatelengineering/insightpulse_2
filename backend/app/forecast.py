"""Sales Forecasting with ETS (exponential smoothing) and STL seasonal adjustment.

Two standard, well known approaches are tried and the more accurate one is kept:

  1. ETS: exponential smoothing with an optional damped trend, chosen by AICc.
  2. STL + ETS: remove the yearly seasonal pattern (STL decomposition), forecast the
     smoothed series with ETS, then add the seasonal pattern back.

"More accurate" is decided by a back test on the most recent months of the user's own
data, so the choice adapts to each dataset and each filter selection.
"""
from __future__ import annotations

import calendar
import warnings as py_warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.seasonal import STL

from .common import UserError, build_frame, money, select_columns

SPEC = [
    ("sales", "Sales Column"),
    ("date", "Date Column"),
    ("filter_column", "Filter Column"),
    ("additional_column", "Additional Filter Column"),
]
ALL_VALUE = "__ALL__"
MIN_MONTHS = 6
MAX_PERIODS = 36
MIN_SEASONAL_MONTHS = 30  # 24 months to learn the pattern plus at least 6 months to test it
SEASONAL_MUST_BEAT = 0.85  # seasonal model must be at least 15% more accurate on the back test to be used


# ---------------------------------------------------------------------------
# Model building blocks. Each forecaster returns (mean, lower, upper, info).
# ---------------------------------------------------------------------------
def _fit_ets(y: pd.Series, trend: bool):
    model = ETSModel(y, error="add", trend="add" if trend else None, damped_trend=trend)
    with py_warnings.catch_warnings():
        py_warnings.simplefilter("ignore")
        return model.fit(disp=False, maxiter=300)


def _best_ets(y: pd.Series):
    best = None
    for trend in (False, True):
        try:
            result = _fit_ets(y, trend)
            score = float(result.aicc)
        except Exception:
            continue
        if np.isfinite(score) and (best is None or score < best[0]):
            best = (score, trend, result)
    if best is None:
        raise ValueError("no ETS model could be fitted")
    return best[1], best[2]


def _interval(result, y: pd.Series, horizon: int):
    with py_warnings.catch_warnings():
        py_warnings.simplefilter("ignore")
        frame = result.get_prediction(start=len(y), end=len(y) + horizon - 1).summary_frame(alpha=0.05)
    mean = frame["mean"].to_numpy(dtype=float)
    lower = frame["pi_lower"].to_numpy(dtype=float)
    upper = frame["pi_upper"].to_numpy(dtype=float)
    if not (np.isfinite(lower).all() and np.isfinite(upper).all()):
        sigma = float(np.nanstd(np.asarray(result.resid, dtype=float))) or 0.1 * float(np.nanstd(y.to_numpy())) or 1.0
        steps = np.sqrt(np.arange(1, horizon + 1))
        lower, upper = mean - 1.96 * sigma * steps, mean + 1.96 * sigma * steps
    return mean, lower, upper


def _forecast_ets(y: pd.Series, horizon: int):
    trend, result = _best_ets(y)
    mean, lower, upper = _interval(result, y, horizon)
    return mean, lower, upper, {"trend": trend, "seasonal": False}


def _forecast_stl(y: pd.Series, horizon: int):
    values = y.to_numpy(dtype=float)
    use_log = float(values.min()) > 0
    z = pd.Series(np.log(values) if use_log else values)
    stl = STL(z, period=12, robust=True).fit()
    seasonal = np.asarray(stl.seasonal, dtype=float)
    adjusted = pd.Series(z.to_numpy() - seasonal)
    trend, result = _best_ets(adjusted)
    mean, lower, upper = _interval(result, adjusted, horizon)
    pattern = np.array([seasonal[len(values) - 12 + (i % 12)] for i in range(horizon)])
    mean, lower, upper = mean + pattern, lower + pattern, upper + pattern
    if use_log:
        mean, lower, upper = np.exp(mean), np.exp(lower), np.exp(upper)
    # Month by month effect of the last full year, used for plain language insights.
    last_year = seasonal[-12:]
    if use_log:
        effects = np.exp(last_year) - 1.0
    else:
        level = float(np.mean(values[-12:])) or 1.0
        effects = last_year / abs(level)
    return mean, lower, upper, {"trend": trend, "seasonal": True, "effects": effects}


def _wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    denominator = float(np.abs(actual).sum())
    if denominator == 0 or not np.isfinite(predicted).all():
        return float("inf")
    return float(np.abs(actual - predicted).sum() / denominator)


def _range_from_backtest(mean: np.ndarray, actual: np.ndarray, predicted: np.ndarray):
    """95% range sized from how far off the model was on the back test (used for the seasonal model).

    STL removes the seasonal pattern before smoothing, which hides some of the real month to month
    variation, so the ETS range alone is too narrow. The back test error is an honest measure.
    """
    if float(np.min(actual)) > 0 and float(np.min(predicted)) > 0 and float(np.min(mean)) > 0:
        sigma = float(np.sqrt(np.mean(np.log(actual / predicted) ** 2)))
        sigma = max(sigma, 0.05)
        return mean * np.exp(-1.96 * sigma), mean * np.exp(1.96 * sigma)
    sigma = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    sigma = max(sigma, 0.05 * float(np.mean(np.abs(actual))) or 1.0)
    return mean - 1.96 * sigma, mean + 1.96 * sigma


def _choose_and_forecast(y: pd.Series, horizon: int, floor_zero: bool):
    """Return the chosen forecast plus accuracy details from a back test."""
    n = len(y)
    series = pd.Series(y.to_numpy(dtype=float))
    can_test_seasonal = n >= MIN_SEASONAL_MONTHS

    def clip(arr):
        return np.maximum(arr, 0.0) if floor_zero else arr

    accuracy = None
    backtest = None
    bt_actual = bt_predicted = None
    chosen = "ets"
    hold = min(12, n - 24) if can_test_seasonal else (min(6, n // 4) if n >= 18 else 0)
    if hold >= 3:
        train, actual = series.iloc[:-hold].reset_index(drop=True), series.iloc[-hold:].to_numpy()
        results = {}
        for name, fn in (("ets", _forecast_ets), ("stl", _forecast_stl)):
            if name == "stl" and not can_test_seasonal:
                continue
            try:
                predicted = clip(fn(train, hold)[0])
                results[name] = (_wape(actual, predicted), predicted)
            except Exception:
                continue
        if results:
            if "stl" in results and "ets" in results:
                chosen = "stl" if results["stl"][0] < results["ets"][0] * SEASONAL_MUST_BEAT else "ets"
            elif "stl" in results:
                chosen = "stl"
            else:
                chosen = "ets"
            error, predicted = results[chosen]
            if np.isfinite(error):
                bt_actual, bt_predicted = actual, predicted
                accuracy = {
                    "accuracy_pct": round(max(0.0, 100 * (1 - error)), 1),
                    "typical_error_pct": round(100 * error, 1),
                    "months_tested": int(hold),
                }
                backtest = [
                    {"month": _month_label(p), "actual": money(a), "forecast": money(f)}
                    for p, a, f in zip(y.index[-hold:], actual, predicted)
                ]

    order = ["stl", "ets"] if chosen == "stl" else ["ets"]
    for name in order:
        try:
            fn = _forecast_stl if name == "stl" else _forecast_ets
            mean, lower, upper, info = fn(series, horizon)
            if np.isfinite(mean).all():
                if name == "stl" and bt_actual is not None:
                    lower, upper = _range_from_backtest(mean, bt_actual, bt_predicted)
                return name, mean, lower, upper, info, accuracy, backtest
        except Exception:
            continue

    # Last resort for unusual data: average of the most recent months.
    recent = series.tail(min(6, n))
    mean = np.repeat(float(recent.mean()), horizon)
    sigma = float(recent.std(ddof=0)) or abs(float(recent.mean())) * 0.1 or 1.0
    return "average", mean, mean - 1.96 * sigma, mean + 1.96 * sigma, {"trend": False, "seasonal": False}, None, None


MODEL_TEXT = {
    "level": ("Level model (ETS)", "Uses a smoothed average of recent months, which suits steady sales."),
    "trend": ("Trend model (ETS)", "Follows the recent direction of sales, with growth or decline gradually leveling off."),
    "seasonal": ("Seasonal trend model (STL + ETS)", "Combines the recent direction of sales with the yearly seasonal pattern in your history."),
    "average": ("Recent average", "Uses the average of the most recent months because the data did not fit a standard forecasting model."),
}


def _month_label(period: pd.Period) -> str:
    return period.strftime("%Y-%m")


def _complete_month_range(dates: pd.Series) -> tuple[pd.Period, pd.Period, list[str]]:
    notes = []
    first, last = dates.min(), dates.max()
    start = first.to_period("M")
    end = last.to_period("M")
    if (end - start).n >= 6:
        if first.day > 5:
            notes.append(f"{calendar.month_name[first.month]} {first.year} was left out because your data starts part way through that month.")
            start = start + 1
        days_in_last = calendar.monthrange(last.year, last.month)[1]
        if last.day < days_in_last - 4:
            notes.append(f"{calendar.month_name[last.month]} {last.year} was left out because it is not a complete month yet.")
            end = end - 1
    return start, end, notes


def _seasonal_sentence(effects: np.ndarray, last_period: pd.Period) -> str | None:
    months = [(last_period - 11 + i).month for i in range(12)]
    by_month = dict(zip(months, effects))
    peak = max(by_month, key=by_month.get)
    low = min(by_month, key=by_month.get)
    if by_month[peak] - by_month[low] < 0.10:
        return None
    return (
        f"Sales usually peak in {calendar.month_name[peak]} (about {100 * by_month[peak]:.0f}% above a typical month) "
        f"and are lowest in {calendar.month_name[low]} (about {abs(100 * by_month[low]):.0f}% below a typical month)."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run(df: pd.DataFrame, params: dict) -> dict:
    cols = select_columns(df, params, SPEC, optional=["additional_column"])

    try:
        periods = int(float(str(params.get("periods", "")).strip()))
    except ValueError:
        raise UserError("Please enter the Forecasting Period as a whole number of months, for example 6.")
    if periods < 1 or periods > MAX_PERIODS:
        raise UserError(f"The Forecasting Period must be between 1 and {MAX_PERIODS} months.")

    filter_value = params.get("filter_value")
    if filter_value in (None, ""):
        raise UserError("Please choose a value for the Filter Column, or choose All to forecast your total sales.")
    additional_col = cols.get("additional_column")
    additional_value = params.get("additional_value")
    if additional_col and additional_value in (None, ""):
        raise UserError("Please choose a value for the Additional Filter Column, or choose All.")

    spec = {
        "sales": (cols["sales"], "number", "Sales Column"),
        "date": (cols["date"], "date", "Date Column"),
        "f1": (cols["filter_column"], "text", "Filter Column"),
    }
    if additional_col:
        spec["f2"] = (additional_col, "text", "Additional Filter Column")
    frame, warnings = build_frame(df, spec)

    start, end, notes = _complete_month_range(frame["date"])
    warnings.extend(notes)
    months = frame["date"].dt.to_period("M")
    frame = frame[(months >= start) & (months <= end)]

    filters = []
    if filter_value != ALL_VALUE:
        frame = frame[frame["f1"] == str(filter_value).strip()]
        filters.append(f"{cols['filter_column']}: {filter_value}")
    if additional_col and additional_value != ALL_VALUE:
        frame = frame[frame["f2"] == str(additional_value).strip()]
        filters.append(f"{additional_col}: {additional_value}")
    if frame.empty:
        raise UserError("No sales were found for the selected filters. Please choose a different filter value.")

    monthly = frame.groupby(frame["date"].dt.to_period("M"))["sales"].sum()
    full_index = pd.period_range(start=monthly.index.min(), end=end, freq="M")
    monthly = monthly.reindex(full_index, fill_value=0.0)
    first_sale = monthly[monthly != 0].index.min()
    monthly = monthly[monthly.index >= first_sale]
    if len(monthly) < MIN_MONTHS:
        raise UserError(
            f"Only {len(monthly)} months of history were found for this selection. At least {MIN_MONTHS} months are needed to create a forecast."
        )
    if float(monthly.abs().sum()) == 0:
        raise UserError("Sales are zero for this selection, so there is nothing to forecast.")

    y = pd.Series(monthly.to_numpy(dtype=float), index=pd.period_range(monthly.index[0], periods=len(monthly), freq="M"))
    floor_zero = float(y.min()) >= 0

    kind, mean, lower, upper, info, accuracy, backtest = _choose_and_forecast(y, periods, floor_zero)
    if floor_zero:
        mean, lower, upper = np.maximum(mean, 0), np.maximum(lower, 0), np.maximum(upper, 0)
    lower = np.minimum(lower, mean)
    upper = np.maximum(upper, mean)

    if kind == "stl":
        model_key = "seasonal"
    elif kind == "average":
        model_key = "average"
    else:
        model_key = "trend" if info.get("trend") else "level"
    model_name, model_text = MODEL_TEXT[model_key]

    forecast_index = pd.period_range(y.index[-1] + 1, periods=periods, freq="M")
    history = [{"month": _month_label(p), "value": money(v)} for p, v in y.items()]
    forecast = [
        {"month": _month_label(p), "value": money(m), "lower": money(lo), "upper": money(up)}
        for p, m, lo, up in zip(forecast_index, mean, lower, upper)
    ]

    forecast_total = float(np.sum(mean))
    comparison = None
    if len(y) >= 12:
        known = [y[p - 12] for p in forecast_index if (p - 12) in y.index]
        if len(known) == len(forecast_index) and sum(known) > 0:
            comparison = {
                "label": "the same months last year",
                "previous": money(sum(known)),
                "change_pct": round(100 * (forecast_total / sum(known) - 1), 1),
            }
    if comparison is None and len(y) >= periods:
        recent = float(y.tail(periods).sum())
        if recent > 0:
            comparison = {
                "label": f"the last {periods} months",
                "previous": money(recent),
                "change_pct": round(100 * (forecast_total / recent - 1), 1),
            }

    plural = "s" if periods > 1 else ""
    insights = []
    if comparison:
        direction = "higher" if comparison["change_pct"] >= 0 else "lower"
        insights.append(
            f"Expected sales for the next {periods} month{plural} are {money(forecast_total):,.0f}, "
            f"{abs(comparison['change_pct']):.1f}% {direction} than {comparison['label']}."
        )
    else:
        insights.append(f"Expected sales for the next {periods} month{plural} are {money(forecast_total):,.0f}.")
    if periods > 1:
        peak_idx = int(np.argmax(mean))
        insights.append(f"The strongest month in the forecast is {calendar.month_name[forecast_index[peak_idx].month]} {forecast_index[peak_idx].year}.")
    if info.get("seasonal") and "effects" in info:
        sentence = _seasonal_sentence(info["effects"], y.index[-1])
        if sentence:
            insights.append(sentence)
    elif len(y) >= MIN_SEASONAL_MONTHS and kind == "ets":
        insights.append("A yearly seasonal pattern did not make the forecast more accurate for this selection, so a simpler model was used.")
    if accuracy:
        insights.append(
            f"When tested on the last {accuracy['months_tested']} months of your history, the forecast was typically within "
            f"{accuracy['typical_error_pct']:.0f}% of actual sales."
        )
    if len(y) < MIN_SEASONAL_MONTHS:
        warnings.append("Yearly seasonal patterns are included when at least 30 months of history are available. Add more history for a more detailed forecast.")
    if periods > len(y):
        warnings.append("The forecast period is longer than your history, so later months are less certain.")

    return {
        "mode": "forecast",
        "selection": filters or ["All sales"],
        "kpis": {
            "forecast_total": money(forecast_total),
            "periods": periods,
            "history_months": int(len(y)),
            "history_start": _month_label(y.index[0]),
            "history_end": _month_label(y.index[-1]),
            "last_12_months": money(y.tail(12).sum()),
        },
        "model": {"name": model_name, "description": model_text},
        "comparison": comparison,
        "accuracy": accuracy,
        "history": history,
        "forecast": forecast,
        "backtest": backtest,
        "insights": insights,
        "warnings": warnings,
    }
