import { useMemo, useState } from "react";
import { downloadCsv } from "../lib/csv.js";
import { formatNumber } from "../lib/format.js";
import { DownloadIcon } from "../components/Icons.jsx";
import { Alert, Block, KpiCard, KpiRow, Notes } from "../components/ui.jsx";
import Tip from "../components/Tip.jsx";
import { BLOCK_TEXT, TERMS } from "../content/text.js";


const VERDICT_TEXT = {
  better: "Personalized suggestions found the hidden purchase more often than the most popular products.",
  similar: "Personalized suggestions performed about the same as the most popular products.",
  worse: "The most popular products found the hidden purchase more often than personalized suggestions.",
};

function AccuracyTest({ validation }) {
  if (!validation) {
    return (
      <Block title="Reliability of the suggestions">
        <p className="muted">Testing needs at least 30 customers who have bought 3 or more different products.</p>
      </Block>
    );
  }
  return (
    <Block
      title="Reliability of the suggestions"
      tip={BLOCK_TEXT.reliability}
      subtitle={`Tested on ${formatNumber(validation.customers_tested)} customers.`}
    >
      <div className="kpi-row">
        <KpiCard label="Suggestions" value={`${validation.model_hit_pct.toFixed(0)}%`} sub="hit rate" tip={TERMS.hitRate.meaning} />
        <KpiCard label="Most popular products" value={`${validation.bestseller_hit_pct.toFixed(0)}%`} sub="hit rate" tip={TERMS.hitRate.meaning} />
      </div>
      <p className={`verdict verdict-${validation.verdict}`}>{VERDICT_TEXT[validation.verdict]}</p>
    </Block>
  );
}

export default function RecommendationResults({ data }) {
  const { kpis, customers, warnings, validation } = data;
  const [typed, setTyped] = useState((customers.find((c) => c.recommendations.length >= 5) || customers[0])?.customer_id || "");

  const byId = useMemo(() => new Map(customers.map((c) => [c.customer_id, c])), [customers]);
  const customer = byId.get(typed.trim());

  const downloadAll = () => {
    const rows = customers.flatMap((c) => c.recommendations.map((r, index) => ({ customer: c.customer_id, rank: index + 1, ...r })));
    downloadCsv("product-recommendations.csv", rows, [
      { label: "Customer", value: (r) => r.customer },
      { label: "Rank", value: (r) => r.rank },
      { label: "Recommended product", value: (r) => r.product },
      ...(kpis.has_category ? [{ label: "Category", value: (r) => r.category }] : []),
      ...(kpis.has_sub_category ? [{ label: "Sub category", value: (r) => r.sub_category }] : []),
      { label: "Match (%)", value: (r) => (r.match_pct === null ? "" : r.match_pct) },
      { label: "Why", value: (r) => r.reason },
    ]);
  };

  return (
    <div className="results">
      <KpiRow>
        <KpiCard label="Customers" value={formatNumber(kpis.customers)} />
        <KpiCard label="Products" value={formatNumber(kpis.products)} />
        <KpiCard label="Products bought per customer" value={formatNumber(kpis.avg_products_per_customer, 1)} sub="on average" />
        {kpis.total_revenue !== null && <KpiCard label="Total sales" value={formatNumber(kpis.total_revenue)} />}
      </KpiRow>

      <Block
        title="Recommendations for a customer"
        actions={
          <button type="button" className="btn btn-ghost small" onClick={downloadAll}>
            <DownloadIcon /> Download all recommendations
          </button>
        }
      >
        <div className="picker">
          <label htmlFor="customer-picker">Customer ID</label>
          <input id="customer-picker" list="customer-options" value={typed} onChange={(event) => setTyped(event.target.value)} placeholder="Type or choose a customer" autoComplete="off" />
          <datalist id="customer-options">
            {customers.map((c) => (
              <option key={c.customer_id} value={c.customer_id} />
            ))}
          </datalist>
        </div>

        {!customer ? (
          <Alert tone="info">
            {typed.trim() === ""
              ? "Type or choose a customer ID to see their suggested products."
              : "No match yet. Choose a customer ID from the list."}
          </Alert>
        ) : (
          <div className="rec-layout">
            <aside className="rec-side">
              <h4>Customer {customer.customer_id}</h4>
              <dl className="stat-list">
                {customer.total_spend !== null && (
                  <div>
                    <dt>Total spend</dt>
                    <dd>{formatNumber(customer.total_spend, 2)}</dd>
                  </div>
                )}
                <div>
                  <dt>Different products bought</dt>
                  <dd>{formatNumber(customer.products_bought)}</dd>
                </div>
              </dl>
              <h5>Buys most often</h5>
              <ul className="chips">
                {customer.top_purchases.map((p) => (
                  <li key={p.product} title={[kpis.has_category && p.category, kpis.has_sub_category && p.sub_category].filter(Boolean).join(" / ") || undefined}>
                    {p.product}
                  </li>
                ))}
              </ul>
            </aside>
            <div className="rec-main">
              {customer.recommendations.length === 0 && (
                <Alert tone="info">This customer has bought every product in the file.</Alert>
              )}
              <div className="table-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Recommended product</th>
                      {kpis.has_category && <th>Category</th>}
                      {kpis.has_sub_category && <th>Sub category</th>}
                      <th className="num">
                        Match
                        <Tip text={BLOCK_TEXT.matchColumn} label="About Match" />
                      </th>
                      <th>Why this product</th>
                    </tr>
                  </thead>
                  <tbody>
                    {customer.recommendations.map((r, index) => (
                      <tr key={r.product_id}>
                        <td>{index + 1}</td>
                        <td>
                          <strong>{r.product}</strong>
                        </td>
                        {kpis.has_category && <td>{r.category}</td>}
                        {kpis.has_sub_category && <td>{r.sub_category}</td>}
                        <td className="num">{r.match_pct === null ? "Popular" : `${r.match_pct}%`}</td>
                        <td className="muted">{r.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </Block>

      <AccuracyTest validation={validation} />

      <Notes items={warnings} />
    </div>
  );
}
