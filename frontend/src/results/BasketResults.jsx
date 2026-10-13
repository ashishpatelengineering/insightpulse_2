import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatNumber } from "../lib/format.js";
import { Block, DataTable, Insights, KpiCard, KpiRow, Notes } from "../components/ui.jsx";

export default function BasketResults({ data }) {
  const { kpis, rules, pairs, insights, warnings } = data;
  const [tab, setTab] = useState("pairs");

  const chartData = pairs
    .slice(0, 8)
    .map((p) => ({ name: `${p.product_a} + ${p.product_b}`, Lift: p.lift }))
    .reverse();

  const pairColumns = [
    { key: "product_a", label: "Product A" },
    { key: "product_b", label: "Product B" },
    { key: "baskets", label: "Bought together", align: "right", render: (r) => `${formatNumber(r.baskets)} baskets` , csv: (r) => r.baskets },
    { key: "support", label: "Support", align: "right", render: (r) => `${r.support}%`, csv: (r) => r.support },
    { key: "confidence_a_to_b", label: "A then B", align: "right", render: (r) => `${r.confidence_a_to_b}%`, csv: (r) => r.confidence_a_to_b },
    { key: "confidence_b_to_a", label: "B then A", align: "right", render: (r) => `${r.confidence_b_to_a}%`, csv: (r) => r.confidence_b_to_a },
    { key: "lift", label: "Lift", align: "right", render: (r) => <strong>{r.lift.toFixed(2)}</strong>, csv: (r) => r.lift },
  ];

  const ruleColumns = [
    { key: "if_buy", label: "If a customer buys", value: (r) => r.if_buy.join(" + ") },
    { key: "also_buy", label: "They also buy" },
    { key: "baskets", label: "Baskets", align: "right", render: (r) => formatNumber(r.baskets) },
    { key: "support", label: "Support", align: "right", render: (r) => `${r.support}%`, csv: (r) => r.support },
    { key: "confidence", label: "Confidence", align: "right", render: (r) => `${r.confidence}%`, csv: (r) => r.confidence },
    { key: "lift", label: "Lift", align: "right", render: (r) => <strong>{r.lift.toFixed(2)}</strong>, csv: (r) => r.lift },
  ];

  return (
    <div className="results">
      <KpiRow>
        <KpiCard label="Baskets analyzed" value={formatNumber(kpis.baskets)} sub="one member on one date" />
        <KpiCard label="Products" value={formatNumber(kpis.products)} />
        <KpiCard label="Average basket size" value={formatNumber(kpis.avg_basket_size, 1)} sub="products per basket" />
        <KpiCard label="Product links found" value={formatNumber(kpis.rules_found)} sub={`seen in at least ${formatNumber(kpis.min_baskets)} baskets`} />
      </KpiRow>

      <Insights items={insights} />

      <Block title="Strongest product pairs" subtitle="Lift shows how many times more likely two products are bought together than by chance. Above 1 is a real link.">
        <div className="chart" style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e9f0" />
              <XAxis type="number" tickLine={false} axisLine={{ stroke: "#cfd6e0" }} />
              <YAxis type="category" dataKey="name" width={310} tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value) => [`${value} times more likely`, "Lift"]} cursor={{ fill: "rgba(11,94,168,0.06)" }} />
              <Bar dataKey="Lift" fill="#0b5ea8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Block>

      <Block title="Detailed results" subtitle="Click a column heading to sort. Download the table for use in your own reports.">
        <div className="tabs" role="tablist" aria-label="Result views">
          <button type="button" role="tab" aria-selected={tab === "pairs"} className={tab === "pairs" ? "tab active" : "tab"} onClick={() => setTab("pairs")}>
            Product pairs
          </button>
          <button type="button" role="tab" aria-selected={tab === "rules"} className={tab === "rules" ? "tab active" : "tab"} onClick={() => setTab("rules")}>
            If then rules
          </button>
        </div>
        {tab === "pairs" ? (
          <DataTable key="pairs" columns={pairColumns} rows={pairs} pageSize={10} searchLabel="Search by product" searchText={(r) => `${r.product_a} ${r.product_b}`} downloadName="product-pairs.csv" initialSort={{ key: "lift", direction: "desc" }} />
        ) : (
          <DataTable key="rules" columns={ruleColumns} rows={rules} pageSize={10} searchLabel="Search by product" searchText={(r) => `${r.if_buy.join(" ")} ${r.also_buy}`} downloadName="product-rules.csv" initialSort={{ key: "lift", direction: "desc" }} />
        )}
        <p className="muted small-print">
          Support is the share of all baskets that contain the products together. Confidence is how often the second product is bought when the first one is.
        </p>
      </Block>
      <Notes items={warnings} />
    </div>
  );
}
