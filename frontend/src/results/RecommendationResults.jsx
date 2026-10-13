import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { downloadCsv } from "../lib/csv.js";
import { compactNumber, formatNumber } from "../lib/format.js";
import { DownloadIcon } from "../components/Icons.jsx";
import { Alert, Block, Insights, KpiCard, KpiRow, Notes } from "../components/ui.jsx";

export default function RecommendationResults({ data }) {
  const { kpis, customers, top_products: topProducts, insights, warnings } = data;
  const [selectedId, setSelectedId] = useState(customers[0]?.customer_id || "");
  const [typed, setTyped] = useState(customers[0]?.customer_id || "");

  const byId = useMemo(() => new Map(customers.map((c) => [c.customer_id, c])), [customers]);
  const customer = byId.get(selectedId);

  const choose = (value) => {
    setTyped(value);
    const match = byId.get(value.trim());
    if (match) setSelectedId(match.customer_id);
  };

  const randomCustomer = () => {
    const pick = customers[Math.floor(Math.random() * customers.length)];
    setSelectedId(pick.customer_id);
    setTyped(pick.customer_id);
  };

  const downloadAll = () => {
    const rows = customers.flatMap((c) => c.recommendations.map((r, index) => ({ customer: c.customer_id, rank: index + 1, ...r })));
    downloadCsv("product-recommendations.csv", rows, [
      { label: "Customer", value: (r) => r.customer },
      { label: "Rank", value: (r) => r.rank },
      { label: "Recommended product", value: (r) => r.product },
      { label: "Category", value: (r) => r.category },
      { label: "Sub category", value: (r) => r.sub_category },
      { label: "Match (%)", value: (r) => (r.match_pct === null ? "" : r.match_pct) },
      { label: "Why", value: (r) => r.reason },
    ]);
  };

  const chartData = [...topProducts].reverse().map((p) => ({ name: p.product, Revenue: p.revenue }));

  return (
    <div className="results">
      <KpiRow>
        <KpiCard label="Customers" value={formatNumber(kpis.customers)} />
        <KpiCard label="Products" value={formatNumber(kpis.products)} />
        <KpiCard label="Products bought per customer" value={formatNumber(kpis.avg_products_per_customer, 1)} sub="on average" />
        <KpiCard label="Total sales" value={formatNumber(kpis.total_revenue)} />
      </KpiRow>

      <Block
        title="Recommendations for a customer"
        subtitle="Type or choose a customer to see the five products they are most likely to want next."
        actions={
          <button type="button" className="btn btn-ghost small" onClick={downloadAll}>
            <DownloadIcon /> Download all recommendations
          </button>
        }
      >
        <div className="picker">
          <label htmlFor="customer-picker">Customer ID</label>
          <input id="customer-picker" list="customer-options" value={typed} onChange={(event) => choose(event.target.value)} placeholder="Type or choose a customer" autoComplete="off" />
          <datalist id="customer-options">
            {customers.map((c) => (
              <option key={c.customer_id} value={c.customer_id} />
            ))}
          </datalist>
          <button type="button" className="btn btn-ghost small" onClick={() => choose(customers[0].customer_id)}>
            Top spender
          </button>
          <button type="button" className="btn btn-ghost small" onClick={randomCustomer}>
            Random customer
          </button>
        </div>

        {!customer ? (
          <Alert tone="info">No customer with that ID was found. Choose one from the list. Customers are listed from highest to lowest spend.</Alert>
        ) : (
          <div className="rec-layout">
            <aside className="rec-side">
              <h4>Customer {customer.customer_id}</h4>
              <dl className="stat-list">
                <div>
                  <dt>Total spend</dt>
                  <dd>{formatNumber(customer.total_spend, 2)}</dd>
                </div>
                <div>
                  <dt>Different products bought</dt>
                  <dd>{formatNumber(customer.products_bought)}</dd>
                </div>
              </dl>
              <h5>Buys most often</h5>
              <ul className="chips">
                {customer.top_purchases.map((p) => (
                  <li key={p.product} title={`${p.category} / ${p.sub_category}`}>
                    {p.product}
                  </li>
                ))}
              </ul>
            </aside>
            <div className="rec-main">
              <div className="table-scroll">
                <table className="table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Recommended product</th>
                      <th>Category</th>
                      <th>Sub category</th>
                      <th className="num">Match</th>
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
                        <td>{r.category}</td>
                        <td>{r.sub_category}</td>
                        <td className="num">
                          {r.match_pct === null ? (
                            "Popular pick"
                          ) : (
                            <span className="match">
                              <span className="match-bar">
                                <span style={{ width: `${r.match_pct}%` }} />
                              </span>
                              {r.match_pct}%
                            </span>
                          )}
                        </td>
                        <td className="muted">{r.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="muted small-print">Match shows how closely a product fits what this customer already buys. Higher is a better fit.</p>
            </div>
          </div>
        )}
      </Block>

      <Block title="Best selling products" subtitle="Top 10 products by sales value.">
        <div className="chart" style={{ height: 340 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e9f0" />
              <XAxis type="number" tickFormatter={compactNumber} tickLine={false} axisLine={{ stroke: "#cfd6e0" }} />
              <YAxis type="category" dataKey="name" width={170} tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value) => formatNumber(value, 2)} cursor={{ fill: "rgba(11,94,168,0.06)" }} />
              <Bar dataKey="Revenue" fill="#0b5ea8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Block>

      <Insights items={insights} />
      <Notes items={warnings} />
    </div>
  );
}
