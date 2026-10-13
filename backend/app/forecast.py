"""Sales Forecasting with ETS (exponential smoothing) and STL seasonal adjustment.

Two standard, well known approaches are tried and the more accurate one is kept:

  1. ETS: exponential smoothing with an optional damped trend, chosen by AICc.
  2. STL + ETS: remove the yearly seasonal pattern (STL decomposition), forecast the
     smoothed series with ETS, then add the seasonal pattern back.

"More accurate" is decided by a rolling origin back test on the user's own data: the model is
refitted several times, each time hiding the next few months, forecasting them and comparing with
what really happened. This is the standard way to measure forecast error on time series, and it
adapts the choice to each dataset and each filter selection.

Error is reported with the measures most used in business forecasting: WAPE, MAPE, MAE, RMSE
and bias, together with a simple benchmark (repeat the same month of last year).
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
MIN_TRAIN = 12            # a test forecast needs at least a year of earlier history
MIN_SEASONAL_TRAIN = 24   # two years are needed to learn a yearly pattern
MAX_FOLDS = 12            # rolling test starting points: one for each month of the latest year
MAX_TEST_HORIZON = 12     # months hidden in each test
MIN_TEST_POINTS = 6       # fewer tested months than this is not a fair measure
SEASONAL_MUST_BEAT = 0.85  # seasonal model must have at least 15% lower error on the back test to be used


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


def _fold_ends(n: int, horizon: int, first_allowed: int) -> list[int]:
    """Rolling origin: the forecast start points used for testing, oldest first.

    Starting points run month by month back from the newest possible one, so that together they
    cover every month of the year. Each test forecast uses only the history before its start.
    """
    newest = n - horizon
    oldest = max(first_allowed, newest - (MAX_FOLDS - 1))
    return list(range(oldest, newest + 1)) if newest >= first_allowed else []


def _measures(actual: np.ndarray, predicted: np.ndarray, benchmark: np.ndarray) -> dict:
    """The standard forecast error measures, computed over every tested month."""
    error = predicted - actual
    total = float(np.abs(actual).sum())
    wape = float(np.abs(error).sum() / total)
    nonzero = actual != 0
    mape = float(np.mean(np.abs(error[nonzero] / actual[nonzero]))) if nonzero.all() else None
    bench_wape = float(np.abs(benchmark - actual).sum() / total)
    return {
        "accuracy_pct": round(max(0.0, 100 * (1 - wape)), 1),
        "wape_pct": round(100 * wape, 1),
        "mape_pct": None if mape is None else round(100 * mape, 1),
        "mae": money(np.mean(np.abs(error))),
        "rmse": money(np.sqrt(np.mean(error ** 2))),
        "bias_pct": round(100 * float(error.sum() / total), 1),
        "benchmark_wape_pct": round(100 * bench_wape, 1),
    }


def _evaluate(series: pd.Series, horizon: int, floor_zero: bool):
    """Rolling origin back test. Returns the chosen model, every tested forecast and the error measures."""
    y = series.to_numpy(dtype=float)
    h = max(1, min(horizon, MAX_TEST_HORIZON))

    def clip(arr):
        return np.maximum(arr, 0.0) if floor_zero else arr

    def forecasts(model, ends):
        out = {}
        for end in ends:
            try:
                out[end] = clip(model(pd.Series(y[:end]), h)[0])
            except Exception:
                continue
        return out

    # Seasonal comparison: needs two years of history before every test start.
    seasonal_ends = _fold_ends(len(y), h, MIN_SEASONAL_TRAIN)
    chosen, seasonal_tested, basis, predictions = "ets", False, [], {}
    if len(seasonal_ends) * h >= MIN_TEST_POINTS:
        ets_pred = forecasts(_forecast_ets, seasonal_ends)
        stl_pred = forecasts(_forecast_stl, seasonal_ends)
        both = sorted(set(ets_pred) & set(stl_pred))
        if len(both) * h >= MIN_TEST_POINTS:
            seasonal_tested = True
            actual_all = np.concatenate([y[e:e + h] for e in both])
            err_ets = _wape(actual_all, np.concatenate([ets_pred[e] for e in both]))
            err_stl = _wape(actual_all, np.concatenate([stl_pred[e] for e in both]))
            chosen = "stl" if err_stl < err_ets * SEASONAL_MUST_BEAT else "ets"
            basis, predictions = both, (stl_pred if chosen == "stl" else ets_pred)
    if not seasonal_tested:
        ends = _fold_ends(len(y), h, MIN_TRAIN)
        predictions = forecasts(_forecast_ets, ends)
        basis = sorted(predictions)
    if len(basis) * h < MIN_TEST_POINTS:
        return None

    actual = np.concatenate([y[e:e + h] for e in basis])
    predicted = np.concatenate([predictions[e] for e in basis])
    # Benchmark: repeat the same month of the previous year, using only earlier data.
    benchmark = np.concatenate([np.array([y[e + i - 12] for i in range(h)]) for e in basis])
    if not np.isfinite(predicted).all() or float(np.abs(actual).sum()) == 0:
        return None
    return {
        "chosen": chosen,
        "seasonal_tested": seasonal_tested,
        "actual": actual,
        "predicted": predicted,
        "months": [series.index[e + i] for e in basis for i in range(h)],
        "made_from": [series.index[e - 1] for e in basis for _ in range(h)],
        "ahead": [i + 1 for _ in basis for i in range(h)],
        "folds": len(basis),
        "horizon": h,
        "measures": _measures(actual, predicted, benchmark),
    }


def _choose_and_forecast(y: pd.Series, horizon: int, floor_zero: bool):
    """Return the chosen forecast plus the back test details."""
    n = len(y)
    series = pd.Series(y.to_numpy(dtype=float))
    evaluation = _evaluate(y, horizon, floor_zero)

    accuracy = backtest = None
    chosen = "ets"
    if evaluation:
        chosen = evaluation["chosen"]
        accuracy = {
            **evaluation["measures"],
            "months_tested": int(len(evaluation["actual"])),
            "folds": evaluation["folds"],
            "horizon": evaluation["horizon"],
        }
        backtest = [
            {"month": _month_label(p), "made_from": _month_label(q), "ahead": int(k), "actual": money(a), "forecast": money(f)}
            for p, q, k, a, f in zip(evaluation["months"], evaluation["made_from"], evaluation["ahead"], evaluation["actual"], evaluation["predicted"])
        ]
        backtest.sort(key=lambda row: (row["month"], row["ahead"]))
    seasonal_tested = bool(evaluation and evaluation["seasonal_tested"])

    order = ["stl", "ets"] if chosen == "stl" else ["ets"]
    for name in order:
        try:
            fn = _forecast_stl if name == "stl" else _forecast_ets
            mean, lower, upper, info = fn(series, horizon)
            if np.isfinite(mean).all():
                if name == "stl" and evaluation is not None:
                    lower, upper = _range_from_backtest(mean, evaluation["actual"], evaluation["predicted"])
                return name, mean, lower, upper, info, accuracy, backtest, seasonal_tested
        except Exception:
            continue

    # Last resort for unusual data: average of the most recent months.
    recent = series.tail(min(6, n))
    mean = np.repeat(float(recent.mean()), horizon)
    sigma = float(recent.std(ddof=0)) or abs(float(recent.mean())) * 0.1 or 1.0
    return "average", mean, mean - 1.96 * sigma, mean + 1.96 * sigma, {"trend": False, "seasonal": False}, None, None, False


MODEL_TEXT = {
    "level": ("Exponential smoothing", "A weighted average that favors recent months."),
    "trend": ("Exponential smoothing with trend", "Follows the recent direction of sales."),
    "seasonal": ("Exponential smoothing with seasonal adjustment", "Adds the yearly seasonal pattern."),
    "average": ("Recent average", "The average of the most recent months."),
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
    cols = select_columns(df, params, SPEC, optional=["filter_column", "additional_column"])

    try:
        number = float(str(params.get("periods", "")).strip())
        if not number.is_integer():
            raise ValueError
        periods = int(number)
    except (ValueError, OverflowError):
        raise UserError("Please enter the Forecasting Period as a whole number of months, for example 6.")
    if periods < 1 or periods > MAX_PERIODS:
        raise UserError(f"The Forecasting Period must be between 1 and {MAX_PERIODS} months.")

    filter_col = cols.get("filter_column")
    filter_value = params.get("filter_value")
    if filter_col and filter_value in (None, ""):
        raise UserError("Please choose a value for the Filter Column, or choose All to forecast your total sales.")
    additional_col = cols.get("additional_column")
    additional_value = params.get("additional_value")
    if additional_col and additional_value in (None, ""):
        raise UserError("Please choose a value for the Additional Filter Column, or choose All.")

    spec = {
        "sales": (cols["sales"], "number", "Sales Column"),
        "date": (cols["date"], "date", "Date Column"),
    }
    if filter_col:
        spec["f1"] = (filter_col, "text", "Filter Column")
    if additional_col:
        spec["f2"] = (additional_col, "text", "Additional Filter Column")
    frame, warnings = build_frame(df, spec)

    start, end, notes = _complete_month_range(frame["date"])
    warnings.extend(notes)
    months = frame["date"].dt.to_period("M")
    frame = frame[(months >= start) & (months <= end)]

    filters = []
    if filter_col and filter_value != ALL_VALUE:
        frame = frame[frame["f1"] == str(filter_value).strip()]
        filters.append(f"{filter_col}: {filter_value}")
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
            f"Only {len(monthly)} month{'s' if len(monthly) != 1 else ''} of history {'was' if len(monthly) == 1 else 'were'} found for this selection. "
            f"At least {MIN_MONTHS} months are needed to create a forecast."
        )
    if float(monthly.abs().sum()) == 0:
        raise UserError("Sales are zero for this selection, so there is nothing to forecast.")

    y = pd.Series(monthly.to_numpy(dtype=float), index=pd.period_range(monthly.index[0], periods=len(monthly), freq="M"))
    floor_zero = float(y.min()) >= 0

    kind, mean, lower, upper, info, accuracy, backtest, seasonal_tested = _choose_and_forecast(y, periods, floor_zero)
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
    if accuracy:
        model_err, bench_err = accuracy["wape_pct"], accuracy["benchmark_wape_pct"]
        if bench_err > 0:
            gain = 1 - model_err / bench_err
            if gain >= 0.05:
                insights.append(
                    f"Compared with repeating the same month of last year, this forecast had {100 * gain:.0f}% lower error "
                    f"({model_err:.1f}% against {bench_err:.1f}%)."
                )
            elif gain > -0.05:
                insights.append(
                    f"Compared with repeating the same month of last year, this forecast had about the same error "
                    f"({model_err:.1f}% against {bench_err:.1f}%)."
                )
            else:
                insights.append(
                    f"Repeating the same month of last year had lower error than this forecast "
                    f"({bench_err:.1f}% against {model_err:.1f}%)."
                )
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
