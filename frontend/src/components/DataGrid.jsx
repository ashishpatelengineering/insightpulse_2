import { useRef, useState } from "react";
import { formatNumber } from "../lib/format.js";

const ROW_HEIGHT = 34;
const VISIBLE_ROWS = 10;
const COLUMN_WIDTH = 150;
const INDEX_WIDTH = 64;
const OVERSCAN = 6;

/** The whole dataset in a scrolling table. Only the rows in view are drawn, so large files stay fast. */
export default function DataGrid({ dataset }) {
  const [scrollTop, setScrollTop] = useState(0);
  const box = useRef(null);
  const rows = dataset.view || [];
  const columns = dataset.columns;
  const first = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
  const last = Math.min(rows.length, first + VISIBLE_ROWS + OVERSCAN * 2);
  const template = `${INDEX_WIDTH}px repeat(${columns.length}, minmax(${COLUMN_WIDTH}px, 1fr))`;
  const minWidth = INDEX_WIDTH + columns.length * COLUMN_WIDTH;
  const shown = rows.length;

  return (
    <section className="card data-card" aria-label="Data preview">
      <div className="data-head">
        <h2>Data</h2>
        <span className="muted">
          {formatNumber(dataset.rows)} rows and {columns.length} columns
          {shown < dataset.rows ? `. Showing the first ${formatNumber(shown)} rows.` : ""}
        </span>
      </div>
      <div
        className="grid-scroll"
        ref={box}
        style={{ height: ROW_HEIGHT * (VISIBLE_ROWS + 1) + 2 }}
        onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
        tabIndex={0}
        role="table"
        aria-label="Dataset rows"
        aria-rowcount={shown + 1}
      >
        <div className="grid-inner" style={{ minWidth }}>
          <div className="grid-row grid-header" role="row" style={{ gridTemplateColumns: template, height: ROW_HEIGHT }}>
            <div className="grid-cell grid-index" role="columnheader">#</div>
            {columns.map((column) => (
              <div className="grid-cell" role="columnheader" key={column.name} title={column.name}>
                {column.name}
              </div>
            ))}
          </div>
          <div className="grid-body" style={{ height: rows.length * ROW_HEIGHT, position: "relative" }}>
            {rows.slice(first, last).map((row, offset) => {
              const index = first + offset;
              return (
                <div
                  className={`grid-row${index % 2 ? " alt" : ""}`}
                  role="row"
                  key={index}
                  style={{ gridTemplateColumns: template, height: ROW_HEIGHT, top: index * ROW_HEIGHT }}
                >
                  <div className="grid-cell grid-index" role="cell">{index + 1}</div>
                  {row.map((value, c) => (
                    <div className="grid-cell" role="cell" key={c} title={value}>
                      {value}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
