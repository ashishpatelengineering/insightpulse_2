import { ALL_VALUE, NONE_VALUE, validateSelections } from "../modes/config.js";
import { useData } from "../context/DataContext.jsx";
import { ChevronIcon } from "./Icons.jsx";

function ColumnSelect({ id, field, value, columns, disabled, onChange }) {
  const placeholder = `Select ${field.label.replace(/ \(Optional\)/, "").replace(/ Column$/, "")}`;
  return (
    <div className="select-wrap">
      <select id={id} value={value || ""} disabled={disabled} onChange={(event) => onChange(event.target.value)} className={value ? "" : "placeholder"}>
        {field.allowNone ? (
          <option value={NONE_VALUE}>None</option>
        ) : (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {columns.map((column) => (
          <option key={column.name} value={column.name}>
            {column.name}
          </option>
        ))}
      </select>
      <ChevronIcon />
    </div>
  );
}

function ValueSelect({ id, field, value, column, disabled, onChange }) {
  if (column?.values?.length) {
    return (
      <div className="select-wrap">
        <select id={id} value={value ?? ALL_VALUE} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
          <option value={ALL_VALUE}>All</option>
          {column.values.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <ChevronIcon />
      </div>
    );
  }
  // Columns with a very large number of different values: let the user type one.
  return (
    <input
      id={id}
      type="text"
      value={value === ALL_VALUE ? "" : value ?? ""}
      disabled={disabled}
      placeholder="Type a value exactly as in your file, or leave empty for All"
      onChange={(event) => onChange(event.target.value.trim() === "" ? ALL_VALUE : event.target.value)}
    />
  );
}

export default function InputsForm({ mode }) {
  const { dataset, loading, selections, setSelection, results, runAnalysis } = useData();
  const current = selections[mode.id] || {};
  const columns = dataset?.columns || [];
  const disabled = !dataset || loading;
  const problems = dataset ? validateSelections(mode, current, columns) : [];
  const running = results[mode.id]?.status === "loading";
  const canAnalyze = Boolean(dataset) && problems.length === 0 && !loading && !running;

  const duplicates = new Set();
  const seen = {};
  mode.fields.forEach((field) => {
    if (field.type || !current[field.key] || current[field.key] === NONE_VALUE) return;
    if (seen[current[field.key]]) {
      duplicates.add(field.key);
      duplicates.add(seen[current[field.key]]);
    }
    seen[current[field.key]] = field.key;
  });

  return (
    <section className="card inputs-card" aria-labelledby={`inputs-${mode.id}`}>
      <h2 id={`inputs-${mode.id}`} className="card-title">
        Inputs
      </h2>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (canAnalyze) runAnalysis(mode.id);
        }}
      >
        <div className="fields">
          {mode.fields.map((field) => {
            const id = `${mode.id}-${field.key}`;
            if (field.type === "value") {
              const parentValue = current[field.column];
              if (!parentValue || parentValue === NONE_VALUE) return null;
              const parent = columns.find((c) => c.name === parentValue);
              return (
                <div className="field" key={field.key}>
                  <label htmlFor={id}>{field.label}</label>
                  <ValueSelect id={id} field={field} value={current[field.key]} column={parent} disabled={disabled} onChange={(v) => setSelection(mode.id, field.key, v)} />
                  <p className="hint">{field.hint}</p>
                </div>
              );
            }
            if (field.type === "number") {
              const n = Number(current[field.key]);
              const invalid = current[field.key] !== "" && (!Number.isInteger(n) || n < field.min || n > field.max);
              return (
                <div className="field" key={field.key}>
                  <label htmlFor={id}>{field.label}</label>
                  <input
                    id={id}
                    type="number"
                    inputMode="numeric"
                    min={field.min}
                    max={field.max}
                    step={1}
                    value={current[field.key] ?? ""}
                    disabled={disabled}
                    placeholder={field.placeholder}
                    aria-invalid={invalid}
                    onChange={(event) => setSelection(mode.id, field.key, event.target.value)}
                  />
                  <p className={`hint${invalid ? " error" : ""}`}>{invalid ? `Enter a whole number between ${field.min} and ${field.max}.` : field.hint}</p>
                </div>
              );
            }
            const duplicate = duplicates.has(field.key);
            return (
              <div className="field" key={field.key}>
                <label htmlFor={id}>{field.label}</label>
                <ColumnSelect id={id} field={field} value={current[field.key]} columns={columns} disabled={disabled} onChange={(v) => setSelection(mode.id, field.key, v)} />
                <p className={`hint${duplicate ? " error" : ""}`}>{duplicate ? "This column is already used by another input." : field.hint}</p>
              </div>
            );
          })}
        </div>
        <div className="form-footer">
          <p className="footer-note" aria-live="polite">
            {!dataset
              ? "Upload a CSV file or choose sample data to begin."
              : duplicates.size > 0
              ? "Each input needs a different column."
              : problems.length > 0
              ? problems[0]
              : "Everything looks good. Click Analyze to continue."}
          </p>
          <button type="submit" className="btn btn-primary" disabled={!canAnalyze || duplicates.size > 0}>
            {running ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </form>
    </section>
  );
}
