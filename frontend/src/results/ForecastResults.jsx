import { useMemo } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { compactNumber, formatMonth, formatNumber } from "../lib/format.js";
import { Block, DataTable, Insights, KpiCard, KpiRow, Notes } from "../components/ui.jsx";

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{formatMonth(label)}</strong>
      {row.history !== undefined && row.forecast === undefined && <div>Actual sales: {formatNumber(row.history)}</div>}
      {row.forecast !== undefined && row.history === undefined && (
        <>
          <div>Forecast: {formatNumber(row.forecast)}</div>
          <div className="muted">
            Likely range: {formatNumber(row.range[0])} to {formatNumber(row.range[1])}
          </div>
        </>
      )}
      {row.forecast !== undefined && row.history !== undefined && <div>Actual sales: {formatNumber(row.history)}</div>}
    </div>
  );
}

export default function ForecastResults({ data }) {
  const { kpis, model, comparison, accuracy, history, forecast, insights, warnings, selection } = data;

  const chartData = useMemo(() => {
    const rows = history.map((h) => ({ month: h.month, history: h.value }));
    const last = rows[rows.length - 1];
    rows[rows.length - 1] = { ...last, forecast: last.history, range: [last.history, last.history] };
    forecast.forEach((f) => rows.push({ month: f.month, forecast: f.value, range: [f.lower, f.upper] }));
    return rows;
  }, [history, forecast]);

  const change = comparison?.change_pct;
  const changeTone = change === undefined ? undefined : change >= 0 ? "good" : "bad";

  const forecastColumns = [
    { key: "month", label: "Month", render: (r) => formatMonth(r.month), csv: (r) => r.month },
    { key: "value", label: "Forecast sales", align: "right", render: (r) => <strong>{formatNumber(r.value)}</strong>, csv: (r) => r.value },
    { key: "lower", label: "Low estimate", align: "right", render: (r) => formatNumber(r.lower), csv: (r) => r.lower },
    { key: "upper", label: "High estimate", align: "right", render: (r) => formatNumber(r.upper), csv: (r) => r.upper },
  ];


  return (
    <div className="results">
      <div className="selection-line">
        Forecast for: {selection.map((s) => (
          <span className="pill neutral" key={s}>
            {s}
          </span>
        ))}
      </div>

      <KpiRow>
        <KpiCard label={`Expected sales, next ${kpis.periods} month${kpis.periods > 1 ? "s" : ""}`} value={formatNumber(kpis.forecast_total)} />
        {comparison ? (
          <KpiCard
            label={comparison.label === "the same months last year" ? "Versus same months last year" : `Versus ${comparison.label}`}
            value={`${change >= 0 ? "+" : ""}${change.toFixed(1)}%`}
            tone={changeTone}
            sub={`${formatNumber(comparison.previous)} before`}
          />
        ) : (
          <KpiCard label="Versus same months last year" value="Not available" sub="Needs 12 months of history" />
        )}
        {accuracy ? (
          <KpiCard
            label="Forecast accuracy"
            value={`${accuracy.accuracy_pct.toFixed(0)}%`}
            sub="tested on past data"
          />
        ) : (
          <KpiCard label="Forecast accuracy" value="Not available" sub="Needs 18 months of history" />
        )}
        <KpiCard label="History used" value={`${kpis.history_months} months`} sub={`${formatMonth(kpis.history_start)} to ${formatMonth(kpis.history_end)}`} />
      </KpiRow>

      <Block title="Sales history and forecast" subtitle="The shaded area is the likely range.">
        <div className="chart" style={{ height: 360 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ebef" />
              <XAxis dataKey="month" tickFormatter={formatMonth} minTickGap={36} tickLine={false} axisLine={{ stroke: "#d0d5db" }} />
              <YAxis tickFormatter={compactNumber} tickLine={false} axisLine={false} width={56} />
              <Tooltip content={<ChartTooltip />} />
              <Area dataKey="range" stroke="none" fill="#a9772f" fillOpacity={0.18} isAnimationActive={false} connectNulls={false} />
              <Line dataKey="history" stroke="#1e3a5f" strokeWidth={2.2} dot={false} isAnimationActive={false} connectNulls={false} />
              <Line dataKey="forecast" stroke="#a9772f" strokeWidth={2.4} strokeDasharray="6 4" dot={false} isAnimationActive={false} connectNulls={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="legend-row">
          <span><i className="swatch line blue" /> Actual sales</span>
          <span><i className="swatch line orange" /> Forecast</span>
          <span><i className="swatch area" /> Likely range</span>
        </div>
      </Block>

      <Insights items={insights} />

      <Block title="Forecast by month" subtitle="Low and high estimates mark the likely range.">
        <DataTable columns={forecastColumns} rows={forecast} pageSize={12} downloadName="sales-forecast.csv" initialSort={{ key: "month", direction: "asc" }} />
      </Block>

      {accuracy && (
        <Block title="Forecast accuracy" subtitle={model.name}>
          <div className="table-scroll">
            <table className="table measures">
              <thead>
                <tr>
                  <th>Measure</th>
                  <th className="num">Result</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Weighted absolute percentage error</td>
                  <td className="num">{accuracy.wape_pct.toFixed(1)}%</td>
                </tr>
                <tr>
                  <td>Mean absolute percentage error</td>
                  <td className="num">{accuracy.mape_pct === null ? "n/a" : `${accuracy.mape_pct.toFixed(1)}%`}</td>
                </tr>
                <tr>
                  <td>Mean absolute error</td>
                  <td className="num">{formatNumber(accuracy.mae)}</td>
                </tr>
                <tr>
                  <td>Root mean squared error</td>
                  <td className="num">{formatNumber(accuracy.rmse)}</td>
                </tr>
                <tr>
                  <td>Bias</td>
                  <td className="num">{`${accuracy.bias_pct > 0 ? "+" : ""}${accuracy.bias_pct.toFixed(1)}%`}</td>
                </tr>
                <tr>
                  <td>Benchmark error (same month last year)</td>
                  <td className="num">{accuracy.benchmark_wape_pct.toFixed(1)}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Block>
      )}
      <Notes items={warnings} />
    </div>
  );
}
