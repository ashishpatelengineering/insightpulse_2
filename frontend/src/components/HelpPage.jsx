import { useEffect, useId, useState } from "react";
import { MODES } from "../modes/config.js";
import { SEGMENTS, TERMS, TERM_GROUPS } from "../content/text.js";
import { EXAMPLES } from "../content/examples.js";
import { ExampleBody, ExampleButton } from "./Example.jsx";

const QUESTIONS = {
  clv: {
    question: "Who are my best customers?",
    needs: "Customer, Date, Sales",
  },
  recommendation: {
    question: "Which products should I offer each customer next?",
    needs: "Customer, Product",
  },
  basket: {
    question: "Which products are bought together?",
    needs: "Product, Order",
  },
  forecast: {
    question: "What will my sales be over the coming months?",
    needs: "Sales, Date",
  },
};

function AnalysisSection({ mode }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const terms = TERM_GROUPS[mode.id].map((key) => TERMS[key]);
  return (
    <section className="card help-card" id={mode.id}>
      <div className="help-card-head">
        <h2>{mode.title}</h2>
        <ExampleButton open={open} onToggle={() => setOpen(!open)} controls={id} />
      </div>
      <ul>
        {mode.info.bullets.map((text) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
      {open && <ExampleBody example={EXAMPLES[mode.id]} id={id} />}
      {mode.id === "clv" && (
        <>
          <h3>Customer groups</h3>
          <ul>
            {SEGMENTS.map((segment) => (
              <li key={segment.name}>
                <strong>{segment.name}.</strong> {segment.text}
              </li>
            ))}
          </ul>
        </>
      )}
      <h3>Abbreviations and terms</h3>
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Term</th>
              <th>Full form</th>
              <th>Meaning</th>
            </tr>
          </thead>
          <tbody>
            {terms.map((t) => (
              <tr key={t.term}>
                <td>
                  <strong>{t.term}</strong>
                </td>
                <td>{t.full}</td>
                <td className="muted">{t.meaning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}


export default function HelpPage() {
  useEffect(() => {
    document.title = "Help | InsightPulse";
  }, []);

  return (
    <div className="mode-page help-page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Help</h1>
          <p className="page-subtitle">Four analyses for a sales file.</p>
        </div>
      </div>

      <section className="card help-card">
        <h2>Analyses</h2>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th>Analysis</th>
                <th>Question answered</th>
                <th>Columns needed</th>
              </tr>
            </thead>
            <tbody>
              {MODES.map((mode) => (
                <tr key={mode.id}>
                  <td>
                    <a
                      href={`#${mode.id}`}
                      onClick={(event) => {
                        event.preventDefault();
                        document.getElementById(mode.id)?.scrollIntoView({ behavior: "smooth", block: "start" });
                      }}
                    >
                      <strong>{mode.title}</strong>
                    </a>
                  </td>
                  <td>{QUESTIONS[mode.id].question}</td>
                  <td className="muted">{QUESTIONS[mode.id].needs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card help-card">
        <h2>How to use it</h2>
        <ol className="help-steps">
          <li>Choose an analysis in the menu.</li>
          <li>Upload a CSV (Comma-Separated Values) file. Sample files can be downloaded from Sample Datasets.</li>
          <li>Check the column matches.</li>
          <li>Click Analyze.</li>
        </ol>
      </section>

      {MODES.map((mode) => (
        <AnalysisSection key={mode.id} mode={mode} />
      ))}
    </div>
  );
}
