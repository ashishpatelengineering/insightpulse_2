"""Sales forecasting with Holt-Winters exponential smoothing.

One method is used for every forecast: exponential smoothing with a damped trend and, when at
least two years of monthly history are available, an additive yearly pattern (Holt-Winters).
The weights are fitted automatically. Below two years there is nothing to learn a yearly pattern
from, so the same method runs without it.

Accuracy is measured with a rolling origin back test on the user's own data: the method is
refitted several times, each time hiding the next few months, forecasting them and comparing with
what really happened. The measures reported are the forecast error (WAPE, which gives the forecast
accuracy), the bias, and the error of a simple benchmark (repeat the same month of last year).

The likely range is an 80% range. Its width comes from the errors seen in the back test, because
the range produced by the model alone is too narrow in practice.
"""
from __future__ import annotations

import calendar
import warnings as py_warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.exponential_smoothing.ets import ETSModel

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
RANGE_LEVEL = 80          # the likely range should contain the real sales about 80 times in 100
Z_RANGE = 1.2816          # normal quantile for a two sided 80% range
NATIVE_WIDENING = 1.25    # the model's own range covered only about 70% of real sales, so it is widened by this factor
MAX_SANE_MULTIPLE = 10    # a forecast above ten times the highest past month is rejected


# ---------------------------------------------------------------------------
# The model. Returns (mean, lower, upper, info); lower and upper come from the model alone.
# ---------------------------------------------------------------------------
def _fit(y: pd.Series, trend: bool, seasonal: bool):
    model = ETSModel(
        y,
        error="add",
        trend="add" if trend else None,
        damped_trend=trend,
        seasonal="add" if seasonal else None,
        seasonal_periods=12 if seasonal else None,
    )
    with py_warnings.catch_warnings():
        py_warnings.simplefilter("ignore")
        return model.fit(disp=False, maxiter=300)


def _sane(mean: np.ndarray, y: pd.Series) -> bool:
    if not np.isfinite(mean).all():
        return False
    return float(np.abs(mean).max()) <= MAX_SANE_MULTIPLE * max(float(np.abs(y.to_numpy()).max()), 1.0)


def _forecast(y: pd.Series, horizon: int):
    options = []
    if len(y) >= MIN_SEASONAL_TRAIN:
        options.append((True, True))
    options += [(False, True), (False, False)]
    for seasonal, trend in options:
        try:
            result = _fit(y, trend, seasonal)
            with py_warnings.catch_warnings():
                py_warnings.simplefilter("ignore")
                frame = result.get_prediction(start=len(y), end=len(y) + horizon - 1).summary_frame(alpha=1 - RANGE_LEVEL / 100)
            mean = frame["mean"].to_numpy(dtype=float)
            lower = frame["pi_lower"].to_numpy(dtype=float)
            upper = frame["pi_upper"].to_numpy(dtype=float)
        except Exception:
            continue
        if not _sane(mean, y):
            continue
        if not (np.isfinite(lower).all() and np.isfinite(upper).all()):
            sigma = float(np.nanstd(np.asarray(result.resid, dtype=float))) or 0.1 * float(np.nanstd(y.to_numpy())) or 1.0
            steps = np.sqrt(np.arange(1, horizon + 1))
            lower, upper = mean - Z_RANGE * sigma * steps, mean + Z_RANGE * sigma * steps
        return mean, lower, upper, {"seasonal": seasonal, "trend": trend}
    # Last resort for unusual data: average of the most recent months.
    recent = y.tail(min(6, len(y)))
    mean = np.repeat(float(recent.mean()), horizon)
    sigma = float(recent.std(ddof=0)) or abs(float(recent.mean())) * 0.1 or 1.0
    return mean, mean - Z_RANGE * sigma, mean + Z_RANGE * sigma, {"seasonal": False, "trend": False, "average": True}


# ---------------------------------------------------------------------------
# Back test: how accurate was this method on the user's own past months?
# ---------------------------------------------------------------------------
def _fold_ends(n: int, horizon: int, first_allowed: int) -> list[int]:
    """Rolling origin: the forecast start points used for testing, oldest first.

    Starting points run month by month back from the newest possible one, so that together they
    cover every month of the year. Each test forecast uses only the history before its start.
    """
    newest = n - horizon
    oldest = max(first_allowed, newest - (MAX_FOLDS - 1))
    return list(range(oldest, newest + 1)) if newest >= first_allowed else []


def _measures(actual: np.ndarray, predicted: np.ndarray, benchmark: np.ndarray) -> dict:
    """Forecast error (WAPE) and the forecast accuracy derived from it, bias and the benchmark error."""
    error = predicted - actual
    total = float(np.abs(actual).sum())
    wape = float(np.abs(error).sum() / total)
    bench_wape = float(np.abs(benchmark - actual).sum() / total)
    return {
        "accuracy_pct": round(max(0.0, 100 * (1 - wape)), 1),
        "wape_pct": round(100 * wape, 1),
        "bias_pct": round(100 * float(error.sum() / total), 1),
        "benchmark_wape_pct": round(100 * bench_wape, 1),
    }


def _evaluate(series: pd.Series, horizon: int, floor_zero: bool):
    """Rolling origin back test. Returns every tested forecast and the error measures, or None."""
    y = series.to_numpy(dtype=float)
    h = max(1, min(horizon, MAX_TEST_HORIZON))
    predictions = {}
    for end in _fold_ends(len(y), h, MIN_TRAIN):
        try:
            predicted = _forecast(pd.Series(y[:end]), h)[0]
        except Exception:
            continue
        predictions[end] = np.maximum(predicted, 0.0) if floor_zero else predicted
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
        "actual": actual,
        "predicted": predicted,
        "months": [series.index[e + i] for e in basis for i in range(h)],
        "made_from": [series.index[e - 1] for e in basis for _ in range(h)],
        "ahead": np.array([i + 1 for _ in basis for i in range(h)]),
        "fold": np.array([e for e in basis for _ in range(h)]),
        "folds": len(basis),
        "horizon": h,
        "measures": _measures(actual, predicted, benchmark),
    }


def _error_scale(actual: np.ndarray, predicted: np.ndarray, positive: bool) -> np.ndarray:
    return np.log(actual / predicted) if positive else actual - predicted


def _sigma_by_step(errors: np.ndarray, ahead: np.ndarray, steps: int) -> np.ndarray:
    """Typical size of the error for each month ahead, never shrinking as the distance grows.

    A month ahead needs at least 3 tested errors of its own. With fewer, the errors of all
    months up to that distance are pooled, so a thin test never gives a range that is too narrow.
    """
    sigma = np.zeros(steps)
    for k in range(1, steps + 1):
        own = errors[ahead == k]
        pool = errors[ahead <= k]
        used = own if len(own) >= 3 else pool
        sigma[k - 1] = float(np.sqrt(np.mean(used ** 2))) if len(used) else 0.0
    return np.maximum.accumulate(sigma)


def _range_from_backtest(mean: np.ndarray, evaluation: dict):
    """80% range sized from the errors seen in the back test."""
    actual, predicted, ahead = evaluation["actual"], evaluation["predicted"], evaluation["ahead"]
    positive = float(np.min(actual)) > 0 and float(np.min(predicted)) > 0 and float(np.min(mean)) > 0
    errors = _error_scale(actual, predicted, positive)
    tested = evaluation["horizon"]
    sigma = _sigma_by_step(errors, ahead, tested)
    floor = 0.03 if positive else 0.03 * float(np.mean(np.abs(actual)))
    sigma = np.maximum(sigma, floor)
    steps = len(mean)
    widths = np.array([sigma[k - 1] if k <= tested else sigma[-1] * np.sqrt(k / tested) for k in range(1, steps + 1)])
    if positive:
        return mean * np.exp(-Z_RANGE * widths), mean * np.exp(Z_RANGE * widths)
    return mean - Z_RANGE * widths, mean + Z_RANGE * widths


def _choose_and_forecast(y: pd.Series, horizon: int, floor_zero: bool):
    """Return the forecast, its likely range, the model details and the back test."""
    series = pd.Series(y.to_numpy(dtype=float))
    mean, lower, upper, info = _forecast(series, horizon)
    native_lower, native_upper = lower, upper
    evaluation = _evaluate(y, horizon, floor_zero)
    accuracy = backtest = None
    if evaluation:
        lower, upper = _range_from_backtest(mean, evaluation)
        # Never narrower than the model's own (widened) range.
        lower = np.minimum(lower, mean - (mean - native_lower) * NATIVE_WIDENING)
        upper = np.maximum(upper, mean + (native_upper - mean) * NATIVE_WIDENING)
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
    else:
        # Too little history to test the method. Widen the model's own range, which is too narrow.
        lower = mean - (mean - lower) * NATIVE_WIDENING
        upper = mean + (upper - mean) * NATIVE_WIDENING
    return mean, lower, upper, info, accuracy, backtest


MODEL_TEXT = {
    "level": ("Exponential smoothing", "A weighted average that favors recent months."),
    "trend": ("Exponential smoothing with trend", "Follows the recent direction of sales."),
    "seasonal": ("Exponential smoothing with trend and yearly pattern", "Follows the recent direction of sales and repeats the yearly pattern."),
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
            notes.append(f"{calendar.month_name[first.month]} {first.year} was left out because the data starts part way through that month.")
            start = start + 1
        days_in_last = calendar.monthrange(last.year, last.month)[1]
        if last.day < days_in_last - 4:
            notes.append(f"{calendar.month_name[last.month]} {last.year} was left out because it is not a complete month yet.")
            end = end - 1
    return start, end, notes


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
        raise UserError("Please choose a value for the Filter Column, or choose All to forecast total sales.")
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

    mean, lower, upper, info, accuracy, backtest = _choose_and_forecast(y, periods, floor_zero)
    if floor_zero:
        mean, lower, upper = np.maximum(mean, 0), np.maximum(lower, 0), np.maximum(upper, 0)
    lower = np.minimum(lower, mean)
    upper = np.maximum(upper, mean)

    if info.get("average"):
        model_key = "average"
    elif info.get("seasonal"):
        model_key = "seasonal"
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
        warnings.append("The forecast period is longer than the history, so later months are less certain.")
    if accuracy and periods > MAX_TEST_HORIZON:
        warnings.append(f"Forecast accuracy was tested up to {MAX_TEST_HORIZON} months ahead. Later months are less certain.")

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
