import { useMemo, useState } from "react";
import { downloadCsv } from "../lib/csv.js";
import { DownloadIcon } from "./Icons.jsx";

export function Spinner({ label }) {
  return (
    <div className="spinner-wrap" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      {label && <p>{label}</p>}
    </div>
  );
}

export function Alert({ children, tone = "error", action }) {
  return (
    <div className={`alert alert-${tone}`} role={tone === "error" ? "alert" : "status"}>
      <div>{children}</div>
      {action}
    </div>
  );
}

export function KpiCard({ label, value, sub, tone, help }) {
  return (
    <div className="kpi" title={help}>
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value${tone ? ` tone-${tone}` : ""}`}>{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

export function KpiRow({ children }) {
  return <div className="kpi-row">{children}</div>;
}

export function Insights({ items, title = "Key takeaways" }) {
  if (!items?.length) return null;
  return (
    <section className="block">
      <h3 className="block-title">{title}</h3>
      <ul className="insights">
        {items.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
    </section>
  );
}

export function Notes({ items }) {
  if (!items?.length) return null;
  return (
    <section className="notes" aria-label="Notes about this analysis">
      <strong>Notes</strong>
      <ul>
        {items.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
    </section>
  );
}

export function Block({ title, subtitle, actions, children }) {
  return (
    <section className="block">
      <div className="block-head">
        <div>
          <h3 className="block-title">{title}</h3>
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

function compare(a, b) {
  if (a === b) return 0;
  if (a === null || a === undefined) return 1;
  if (b === null || b === undefined) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" });
}

/**
 * Sortable, searchable, paged table.
 * columns: [{ key, label, align, render, value, csv }]
 */
export function DataTable({ columns, rows, pageSize = 10, searchLabel, searchText, filter, downloadName, initialSort, empty = "Nothing to show." }) {
  const [query, setQuery] = useState("");
  const [filterValue, setFilterValue] = useState("");
  const [sort, setSort] = useState(initialSort || null);
  const [page, setPage] = useState(0);

  const valueOf = (column, row) => (column.value ? column.value(row) : row[column.key]);

  const visible = useMemo(() => {
    let list = rows;
    if (filter && filterValue) list = list.filter((row) => filter.get(row) === filterValue);
    if (searchText && query.trim()) {
      const needle = query.trim().toLowerCase();
      list = list.filter((row) => searchText(row).toLowerCase().includes(needle));
    }
    if (sort) {
      const column = columns.find((c) => c.key === sort.key);
      if (column) {
        const direction = sort.direction === "asc" ? 1 : -1;
        list = [...list].sort((a, b) => direction * compare(valueOf(column, a), valueOf(column, b)));
      }
    }
    return list;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, query, filterValue, sort, columns]);

  const pages = Math.max(1, Math.ceil(visible.length / pageSize));
  const safePage = Math.min(page, pages - 1);
  const slice = visible.slice(safePage * pageSize, safePage * pageSize + pageSize);

  const toggleSort = (key) => {
    setPage(0);
    setSort((current) => {
      if (!current || current.key !== key) return { key, direction: "desc" };
      return { key, direction: current.direction === "desc" ? "asc" : "desc" };
    });
  };

  const download = () => {
    downloadCsv(
      downloadName || "export.csv",
      visible,
      columns.map((c) => ({ label: c.label, value: (row) => (c.csv ? c.csv(row) : valueOf(c, row)) }))
    );
  };

  return (
    <div className="table-block">
      <div className="table-toolbar">
        {searchText && (
          <input
            type="search"
            className="search"
            placeholder={searchLabel || "Search"}
            aria-label={searchLabel || "Search"}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(0);
            }}
          />
        )}
        {filter && (
          <select
            className="filter-select"
            aria-label={filter.label}
            value={filterValue}
            onChange={(event) => {
              setFilterValue(event.target.value);
              setPage(0);
            }}
          >
            <option value="">{filter.label}</option>
            {filter.options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        )}
        <span className="toolbar-spacer" />
        {downloadName && (
          <button type="button" className="btn btn-ghost small" onClick={download}>
            <DownloadIcon /> Download CSV
          </button>
        )}
      </div>
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              {columns.map((column) => {
                const active = sort?.key === column.key;
                return (
                  <th
                    key={column.key}
                    className={column.align === "right" ? "num" : ""}
                    aria-sort={active ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}
                  >
                    <button type="button" className={`th-button${active ? " active" : ""}`} onClick={() => toggleSort(column.key)}>
                      {column.label}
                      <span className="sort-mark" aria-hidden="true">
                        {active ? (sort.direction === "asc" ? "▲" : "▼") : "⇅"}
                      </span>
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {slice.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="empty-cell">
                  {empty}
                </td>
              </tr>
            ) : (
              slice.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column.key} className={column.align === "right" ? "num" : ""}>
                      {column.render ? column.render(row) : valueOf(column, row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="pager">
        <span className="muted">
          {visible.length === 0 ? "0 rows" : `${safePage * pageSize + 1} to ${Math.min(visible.length, (safePage + 1) * pageSize)} of ${visible.length.toLocaleString("en-US")}`}
        </span>
        <div className="pager-buttons">
          <button type="button" className="btn btn-ghost small" onClick={() => setPage(Math.max(0, safePage - 1))} disabled={safePage === 0}>
            Previous
          </button>
          <span className="muted">
            Page {safePage + 1} of {pages}
          </span>
          <button type="button" className="btn btn-ghost small" onClick={() => setPage(Math.min(pages - 1, safePage + 1))} disabled={safePage >= pages - 1}>
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
