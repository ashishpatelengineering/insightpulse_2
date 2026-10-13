import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatNumber } from "../lib/format.js";
import { Block, DataTable, Insights, KpiCard, KpiRow, Notes } from "../components/ui.jsx";

export default function BasketResults({ data }) {
  const { kpis, pairs, insights, warnings } = data;

  const chartData = pairs
    .slice(0, 8)
    .map((p) => ({ name: `${p.product_a} + ${p.product_b}`, Lift: p.lift }));

  const pairColumns = [
    { key: "product_a", label: "Product A" },
    { key: "product_b", label: "Product B" },
    { key: "baskets", label: "Bought together", align: "right", render: (r) => `${formatNumber(r.baskets)} baskets` , csv: (r) => r.baskets },
    { key: "support", label: "Support", align: "right", render: (r) => `${r.support}%`, csv: (r) => r.support },
    { key: "confidence_a_to_b", label: "A then B", align: "right", render: (r) => `${r.confidence_a_to_b}%`, csv: (r) => r.confidence_a_to_b },
    { key: "confidence_b_to_a", label: "B then A", align: "right", render: (r) => `${r.confidence_b_to_a}%`, csv: (r) => r.confidence_b_to_a },
    { key: "lift", label: "Lift", align: "right", render: (r) => <strong>{r.lift.toFixed(2)}</strong>, csv: (r) => r.lift },
  ];

  return (
    <div className="results">
      <KpiRow>
        <KpiCard label="Baskets analyzed" value={formatNumber(kpis.baskets)} sub={kpis.basket_by === "order" ? "one order or receipt" : "one customer on one date"} />
        <KpiCard label="Products" value={formatNumber(kpis.products)} />
        <KpiCard label="Average basket size" value={formatNumber(kpis.avg_basket_size, 1)} sub="products per basket" />
        <KpiCard label="Product pairs found" value={formatNumber(pairs.length)} sub={`bought together in at least ${formatNumber(kpis.min_baskets)} baskets`} />
      </KpiRow>

      <Insights items={insights} />

      <Block title="Strongest product pairs" subtitle="Lift: how many times more often the products are bought together than by chance.">
        <div className="chart" style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e8ebef" />
              <XAxis type="number" tickLine={false} axisLine={{ stroke: "#d0d5db" }} />
              <YAxis type="category" dataKey="name" width={310} tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
              <Tooltip separator=": " formatter={(value) => [`${value} times more likely`, "Lift"]} cursor={{ fill: "rgba(30,58,95,0.06)" }} />
              <Bar dataKey="Lift" fill="#1e3a5f" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Block>

      <Block title="All product pairs" subtitle="Click a column heading to sort. Download the table for your own reports.">
        <DataTable columns={pairColumns} rows={pairs} pageSize={10} searchLabel="Search by product" searchText={(r) => `${r.product_a} ${r.product_b}`} downloadName="product-pairs.csv" initialSort={{ key: "lift", direction: "desc" }} />
        <p className="muted small-print">
          Support: share of orders containing both products. A then B: share of orders with A that also contain B.
        </p>
      </Block>
      <Notes items={warnings} />
    </div>
  );
}
