import { formatNumber } from "../lib/format.js";
import { Block, DataTable, KpiCard, KpiRow, Notes } from "../components/ui.jsx";

export default function BasketResults({ data }) {
  const { kpis, pairs, warnings } = data;

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
        <KpiCard label="Baskets analyzed" value={formatNumber(kpis.baskets)} sub="one order each" />
        <KpiCard label="Products" value={formatNumber(kpis.products)} />
        <KpiCard label="Average basket size" value={formatNumber(kpis.avg_basket_size, 1)} sub="products per basket" />
        <KpiCard label="Product pairs found" value={formatNumber(pairs.length)} sub={`bought together in at least ${formatNumber(kpis.min_baskets)} baskets`} />
      </KpiRow>

      <Block title="Product pairs" subtitle="Lift: how many times more often the products are bought together than by chance.">
        <DataTable columns={pairColumns} rows={pairs} pageSize={10} searchLabel="Search by product" searchText={(r) => `${r.product_a} ${r.product_b}`} downloadName="product-pairs.csv" initialSort={{ key: "lift", direction: "desc" }} />
        <p className="muted small-print">
          Support: share of orders containing both products. A then B: share of orders with A that also contain B.
        </p>
      </Block>
      <Notes items={warnings} />
    </div>
  );
}
