import { useEffect, useState } from "react";
import { listSamples } from "../lib/api.js";
import { formatNumber } from "../lib/format.js";
import { DownloadIcon } from "./Icons.jsx";
import { Alert, Spinner } from "./ui.jsx";

export default function SamplesPage() {
  const [samples, setSamples] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    document.title = "Sample Datasets | InsightPulse";
    let cancelled = false;
    listSamples()
      .then((list) => !cancelled && setSamples(list))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mode-page help-page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Sample Datasets</h1>
          <p className="page-subtitle">Download a file, then upload it in any analysis.</p>
        </div>
      </div>
      <section className="card help-card">
        {error && <Alert>{error}</Alert>}
        {!samples && !error && <Spinner label="Loading..." />}
        {samples && (
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Dataset</th>
                  <th>Description</th>
                  <th className="num">Rows</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {samples.map((sample) => (
                  <tr key={sample.id}>
                    <td>
                      <strong>{sample.name}</strong>
                    </td>
                    <td className="muted">{sample.description}</td>
                    <td className="num">{formatNumber(sample.rows)}</td>
                    <td className="num">
                      <a className="btn btn-outline small" href={`/api/samples/${encodeURIComponent(sample.id)}`} download={sample.filename}>
                        <DownloadIcon /> Download
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
