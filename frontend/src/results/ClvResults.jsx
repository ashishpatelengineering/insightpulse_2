import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatDate, formatNumber, formatPercent } from "../lib/format.js";
import { Block, DataTable, Insights, KpiCard, KpiRow, Notes } from "../components/ui.jsx";

const SEGMENT_COLORS = {
  Champions: "#1e3a5f",
  "Loyal Customers": "#6384ab",
  "Promising Customers": "#4a8f8a",
  "At Risk": "#b7791f",
  Hibernating: "#98a3b0",
};

function SegmentCard({ segment }) {
  const color = SEGMENT_COLORS[segment.segment];
  return (
    <article className="segment-card" style={{ borderTopColor: color }}>
      <header>
        <span className="dot" style={{ background: color }} />
        <h4>{segment.segment}</h4>
      </header>
      <p className="muted">{segment.description}</p>
      <div className="segment-main">
        <strong>{formatNumber(segment.customers)}</strong>
        <span>customers ({formatPercent(segment.pct_customers, 0)})</span>
      </div>
      <dl className="stat-list">
        <div>
          <dt>Share of revenue</dt>
          <dd>{formatPercent(segment.pct_revenue, 0)}</dd>
        </div>
        <div>
          <dt>Average spend</dt>
          <dd>{formatNumber(segment.avg_spend)}</dd>
        </div>
        <div>
          <dt>Last bought</dt>
          <dd>{formatNumber(segment.avg_days_since_last)} days ago</dd>
        </div>
      </dl>
    </article>
  );
}

export default function ClvResults({ data }) {
  const { kpis, segments, customers, insights, warnings } = data;
  const chartData = segments.map((s) => ({
    name: s.segment,
    "Share of customers": s.pct_customers,
    "Share of revenue": s.pct_revenue,
  }));

  const columns = [
    { key: "customer_id", label: "Customer" },
    {
      key: "segment",
      label: "Segment",
      render: (row) => (
        <span className="pill" style={{ background: `${SEGMENT_COLORS[row.segment]}22`, color: SEGMENT_COLORS[row.segment] }}>
          {row.segment}
        </span>
      ),
    },
    { key: "total_spend", label: "Lifetime spend", align: "right", render: (r) => formatNumber(r.total_spend, 2) },
    { key: "orders", label: "Orders", align: "right" },
    { key: "last_purchase", label: "Last purchase", render: (r) => formatDate(r.last_purchase), csv: (r) => r.last_purchase },
    { key: "days_since_last", label: "Days since last purchase", align: "right" },
    { key: "rfm", label: "Score", align: "right" },
  ];

  return (
    <div className="results">
      <KpiRow>
        <KpiCard label="Customers" value={formatNumber(kpis.customers)} sub={`${formatDate(kpis.period_start)} to ${formatDate(kpis.period_end)}`} />
        <KpiCard label="Total revenue" value={formatNumber(kpis.total_revenue)} sub={`${formatNumber(kpis.orders)} orders`} />
        <KpiCard label="Average lifetime value" value={formatNumber(kpis.avg_spend)} sub="per customer" />
        <KpiCard label="Average order value" value={formatNumber(kpis.avg_order_value)} sub="per order" />
      </KpiRow>

      <Insights items={insights} />

      <Block title="Customer segments" subtitle="Based on how recently, how often and how much customers buy.">
        <div className="segment-grid">
          {segments.map((segment) => (
            <SegmentCard key={segment.segment} segment={segment} />
          ))}
        </div>
      </Block>

      <Block title="Who drives your revenue" subtitle="Share of customers compared with share of revenue.">
        <div className="chart" style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 4 }} barGap={6}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ebef" />
              <XAxis dataKey="name" tickLine={false} axisLine={{ stroke: "#d0d5db" }} tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} width={48} />
              <Tooltip formatter={(value) => `${value}%`} cursor={{ fill: "rgba(30,58,95,0.06)" }} />
              <Legend />
              <Bar dataKey="Share of customers" fill="#b9c4d0" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Share of revenue" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Block>

      <Block title="Customer list" subtitle="Search, sort, filter and download.">
        <DataTable
          columns={columns}
          rows={customers}
          pageSize={10}
          searchLabel="Search by customer"
          searchText={(row) => row.customer_id}
          filter={{ label: "All segments", options: segments.map((s) => s.segment), get: (row) => row.segment }}
          downloadName="customer-segments.csv"
          initialSort={{ key: "total_spend", direction: "desc" }}
        />
        <p className="muted small-print">
          Score: Recency, Frequency and Monetary value, each from 1 (lowest) to 5 (highest). For example, 5-4-3 means Recency 5, Frequency 4 and Monetary value 3.
        </p>
      </Block>
      <Notes items={warnings} />
    </div>
  );
}
