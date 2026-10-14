import { GROUP_GRID } from "../content/text.js";

const CLASS = {
  Champions: "cell-champions",
  "Loyal Customers": "cell-loyal",
  "Promising Customers": "cell-promising",
  "At Risk": "cell-atrisk",
  Hibernating: "cell-hibernating",
};

/** Grid of unique buckets: R score across the top, F and M average down the side. */
export default function GroupGrid() {
  return (
    <div className="table-scroll">
      <table className="group-grid">
        <colgroup>
          <col style={{ width: 26 }} />
          <col style={{ width: 70 }} />
          <col />
          <col />
          <col />
          <col />
          <col />
        </colgroup>
        <thead>
          <tr>
            <th colSpan={2} />
            <th className="axis" colSpan={5}>
              R score
            </th>
          </tr>
          <tr>
            <th colSpan={2} />
            {[1, 2, 3, 4, 5].map((n) => (
              <th key={n}>{n}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {GROUP_GRID.rows.map((row, i) => (
            <tr key={GROUP_GRID.bands[i]}>
              {i === 0 && (
                <th className="side" rowSpan={GROUP_GRID.rows.length}>
                  <span>F and M average</span>
                </th>
              )}
              <th className="rowh">{GROUP_GRID.bands[i]}</th>
              {row.map((group, j) => (
                <td key={j} className={CLASS[group]}>
                  {group}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
