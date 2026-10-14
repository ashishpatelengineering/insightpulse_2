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

/** Example button that opens a worked example under the section heading. */
export function ExampleButton({ open, onToggle, controls }) {
  return (
    <button type="button" className="btn btn-outline example-toggle" aria-expanded={open} aria-controls={controls} onClick={onToggle}>
      Example
      <svg className={`chevron${open ? " open" : ""}`} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M6 9l6 6 6-6" />
      </svg>
    </button>
  );
}

export function ExampleBody({ example, id }) {
  return (
    <div className="example" id={id}>
      <p>{example.lead}</p>
      {example.leadTable && <ExampleTable table={example.leadTable} />}
      {example.steps.map((step, i) => (
        <Step key={step.title} step={step} number={i + 1} />
      ))}
    </div>
  );
}
