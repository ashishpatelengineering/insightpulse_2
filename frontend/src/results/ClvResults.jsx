import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatDate, formatNumber, formatPercent } from "../lib/format.js";
import { Block, DataTable, Insights, KpiCard, KpiRow, Notes } from "../components/ui.jsx";

const SEGMENT_COLORS = {
  "Low Value": "#8fa3b8",
  "Medium Value": "#4a90d9",
  "High Value": "#0b4f94",
};

function SegmentCard({ segment }) {
  return (
    <article className="segment-card" style={{ borderTopColor: SEGMENT_COLORS[segment.segment] }}>
      <header>
        <span className="dot" style={{ background: SEGMENT_COLORS[segment.segment] }} />
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
          <dt>Average spend per customer</dt>
          <dd>{formatNumber(segment.avg_spend)}</dd>
        </div>
        <div>
          <dt>Spend range</dt>
          <dd>
            {formatNumber(segment.min_spend)} to {formatNumber(segment.max_spend)}
          </dd>
        </div>
        <div>
          <dt>Average orders</dt>
          <dd>{formatNumber(segment.avg_orders, 1)}</dd>
        </div>
        <div>
          <dt>Days since last purchase</dt>
          <dd>{formatNumber(segment.avg_days_since_last)} on average</dd>
        </div>
      </dl>
      <p className="action">
        <strong>Suggested action:</strong> {segment.action}
      </p>
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
    { key: "total_spend", label: "Total spend", align: "right", render: (r) => formatNumber(r.total_spend, 2) },
    { key: "orders", label: "Orders", align: "right" },
    { key: "avg_order_value", label: "Average order", align: "right", render: (r) => formatNumber(r.avg_order_value, 2) },
    { key: "last_purchase", label: "Last purchase", render: (r) => formatDate(r.last_purchase), csv: (r) => r.last_purchase },
    { key: "days_since_last", label: "Days since last purchase", align: "right" },
  ];

  return (
    <div className="results">
      <KpiRow>
        <KpiCard label="Customers analyzed" value={formatNumber(kpis.customers)} sub={`${formatDate(kpis.period_start)} to ${formatDate(kpis.period_end)}`} />
        <KpiCard label="Total revenue" value={formatNumber(kpis.total_revenue)} sub={`${formatNumber(kpis.orders)} orders`} />
        <KpiCard label="Average spend per customer" value={formatNumber(kpis.avg_spend)} />
        <KpiCard label="Average order value" value={formatNumber(kpis.avg_order_value)} />
      </KpiRow>

      <Block title="Your three customer segments" subtitle="Customers are grouped by their total spend over the period in your data.">
        <div className="segment-grid">
          {segments.map((segment) => (
            <SegmentCard key={segment.segment} segment={segment} />
          ))}
        </div>
      </Block>

      <Block title="Who drives your revenue" subtitle="Compare each segment's share of customers with its share of revenue.">
        <div className="chart" style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 4 }} barGap={6}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e9f0" />
              <XAxis dataKey="name" tickLine={false} axisLine={{ stroke: "#cfd6e0" }} />
              <YAxis tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} width={48} />
              <Tooltip formatter={(value) => `${value}%`} cursor={{ fill: "rgba(11,94,168,0.06)" }} />
              <Legend />
              <Bar dataKey="Share of customers" fill="#9fb3c8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Share of revenue" fill="#0b5ea8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Block>

      <Insights items={insights} />

      <Block title="Customer list" subtitle="Search, sort or filter your customers, then download the list with each customer's segment.">
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
      </Block>
      <Notes items={warnings} />
    </div>
  );
}
