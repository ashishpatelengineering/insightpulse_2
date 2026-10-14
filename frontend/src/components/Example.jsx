import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import GroupGrid from "./GroupGrid.jsx";

function Rich({ text }) {
  const parts = String(text).split(/\*\*(.+?)\*\*/g);
  return parts.map((part, i) => (i % 2 === 1 ? <strong key={i}>{part}</strong> : part));
}

function ExampleTable({ table }) {
  return (
    <div className="table-scroll">
      <table className="table example-table">
        <thead>
          <tr>
            {table.head.map((label, i) => (
              <th key={label} className={table.align?.[i] === "right" ? "num" : ""}>
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, r) => (
            <tr key={r}>
              {row.map((cell, i) => (
                <td key={i} className={table.align?.[i] === "right" ? "num" : ""}>
                  <Rich text={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Formula({ formula }) {
  return (
    <div className="formula">
      <div className="formula-equation">{formula.equation}</div>
      <div className="formula-where">
        <span className="formula-where-label">Where</span>
        {formula.where.map(([name, meaning]) => (
          <span key={name} className="formula-term">
            <strong>{name}</strong>: {meaning}
          </span>
        ))}
      </div>
    </div>
  );
}

function Step({ step, number }) {
  return (
    <section className="example-step">
      <h4>
        <span className="step-number">{number}</span>
        {step.title}
      </h4>
      {step.text?.map((paragraph) => (
        <p key={paragraph}>
          <Rich text={paragraph} />
        </p>
      ))}
      {step.formula && <Formula formula={step.formula} />}
      {step.afterFormula?.map((paragraph) => (
        <p key={paragraph}>
          <Rich text={paragraph} />
        </p>
      ))}
      {step.table && <ExampleTable table={step.table} />}
      {step.grid && <GroupGrid />}
      {step.table2 && <ExampleTable table={step.table2} />}
      {step.after?.map((paragraph) => (
        <p key={paragraph}>
          <Rich text={paragraph} />
        </p>
      ))}
    </section>
  );
}

/** Button that opens the worked example in a pop-up window. */
export function ExampleButton({ onOpen }) {
  return (
    <button type="button" className="btn btn-outline example-toggle" aria-haspopup="dialog" onClick={onOpen}>
      Example
    </button>
  );
}

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Pop-up window with a worked example. Closes with the X, the Close button, Escape or a click outside. */
export function ExampleModal({ title, example, onClose }) {
  const dialog = useRef(null);
  const titleId = useId();

  useEffect(() => {
    const opener = document.activeElement;
    const scrollbar = window.innerWidth - document.documentElement.clientWidth;
    const previousOverflow = document.body.style.overflow;
    const previousPadding = document.body.style.paddingRight;
    document.body.style.overflow = "hidden";
    if (scrollbar > 0) document.body.style.paddingRight = `${scrollbar}px`;
    dialog.current?.querySelector(".modal-close")?.focus();

    const onKey = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !dialog.current) return;
      const items = [...dialog.current.querySelectorAll(FOCUSABLE)];
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
      document.body.style.paddingRight = previousPadding;
      if (opener && typeof opener.focus === "function") opener.focus();
    };
  }, [onClose]);

  return createPortal(
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby={titleId} ref={dialog}>
        <header className="modal-head">
          <div>
            <p className="modal-kicker">Worked example</p>
            <h2 id={titleId}>{title}</h2>
          </div>
          <button type="button" className="modal-close" aria-label="Close example" onClick={onClose}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </header>
        <div className="modal-body">
          <div className="example">
            <p>{example.lead}</p>
            {example.leadTable && <ExampleTable table={example.leadTable} />}
            {example.steps.map((step, i) => (
              <Step key={step.title} step={step} number={i + 1} />
            ))}
          </div>
        </div>
        <footer className="modal-foot">
          <button type="button" className="btn btn-outline" onClick={onClose}>
            Close
          </button>
        </footer>
      </div>
    </div>,
    document.body,
  );
}
