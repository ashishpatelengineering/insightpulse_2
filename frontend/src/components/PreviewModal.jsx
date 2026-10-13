import { useEffect } from "react";
import { formatNumber } from "../lib/format.js";
import { CloseIcon } from "./Icons.jsx";

export default function PreviewModal({ dataset, onClose }) {
  useEffect(() => {
    const onKey = (event) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Data preview">
        <div className="modal-head">
          <div>
            <h2>Data preview</h2>
            <p className="muted">
              {dataset.filename}: {formatNumber(dataset.rows)} rows and {dataset.columns.length} columns. Showing the first {dataset.preview.length} rows.
            </p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close preview">
            <CloseIcon />
          </button>
        </div>
        <div className="table-scroll">
          <table className="table compact">
            <thead>
              <tr>
                {dataset.columns.map((column) => (
                  <th key={column.name}>
                    {column.name}
                    <span className="kind">{column.kind}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataset.preview.map((row, index) => (
                <tr key={index}>
                  {dataset.columns.map((column) => (
                    <td key={column.name}>{row[column.name]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
