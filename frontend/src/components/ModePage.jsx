import { useEffect, useRef, useState } from "react";
import { useData } from "../context/DataContext.jsx";
import { buildParams } from "../modes/config.js";
import DatasetBar, { useUploadHandler } from "./DatasetBar.jsx";
import PreviewModal from "./PreviewModal.jsx";
import { UploadIcon } from "./Icons.jsx";
import { formatNumber } from "../lib/format.js";
import InfoPopover from "./InfoPopover.jsx";
import InputsForm from "./InputsForm.jsx";
import { Alert, Spinner } from "./ui.jsx";
import ClvResults from "../results/ClvResults.jsx";
import RecommendationResults from "../results/RecommendationResults.jsx";
import BasketResults from "../results/BasketResults.jsx";
import ForecastResults from "../results/ForecastResults.jsx";

const VIEWS = {
  clv: ClvResults,
  recommendation: RecommendationResults,
  basket: BasketResults,
  forecast: ForecastResults,
};

function StartPanel() {
  const { samples, loadSample } = useData();
  const handleUpload = useUploadHandler();
  const fileInput = useRef(null);
  return (
    <div className="start-panel">
      <h2 className="start-title">Add your data to get started</h2>
      <p className="muted start-text">
        Upload a CSV file of your sales data, or try a sample dataset.
      </p>
      <button type="button" className="btn btn-primary" onClick={() => fileInput.current?.click()}>
        <UploadIcon /> Upload a CSV file
      </button>
      <input
        ref={fileInput}
        type="file"
        accept=".csv,.txt,text/csv"
        hidden
        onChange={(event) => {
          handleUpload(event.target.files?.[0]);
          event.target.value = "";
        }}
      />
      {samples.length > 0 && (
        <>
          <p className="start-or">or try a sample dataset</p>
          <div className="sample-grid">
            {samples.map((sample) => (
              <button key={sample.id} type="button" className="sample-card" onClick={() => loadSample(sample)}>
                <span className="sample-name">{sample.name}</span>
                <span className="sample-text">{sample.description}</span>
                <span className="sample-meta">{formatNumber(sample.rows)} rows</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function LoadedPanel({ dataset }) {
  const [preview, setPreview] = useState(false);
  return (
    <div className="loaded-panel">
      <div className="loaded-title">
        <strong>{dataset.filename}</strong> is loaded: {formatNumber(dataset.rows)} rows and {dataset.columns.length} columns.
      </div>
      <p className="muted">
        Check the column matches below, then click Analyze.
      </p>
      <button type="button" className="btn btn-outline small" onClick={() => setPreview(true)}>
        Preview the data
      </button>
      {preview && <PreviewModal dataset={dataset} onClose={() => setPreview(false)} />}
    </div>
  );
}

function ResultsPanel({ mode }) {
  const { results, loading, loadingText, datasetError, slow, dataset, runAnalysis, selections } = useData();
  const result = results[mode.id];
  const View = VIEWS[mode.id];
  const panel = useRef(null);

  useEffect(() => {
    if (result?.status === "done") panel.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [result?.status]);

  let body;
  if (loading) {
    body = <Spinner label={loadingText || "Loading..."} />;
  } else if (result?.status === "loading") {
    body = <Spinner label={slow ? "Still working. The server may take up to a minute to wake up..." : "Analyzing your data..."} />;
  } else if (result?.status === "error") {
    body = (
      <Alert
        action={
          dataset && (
            <button type="button" className="btn btn-outline small" onClick={() => runAnalysis(mode.id)}>
              Try again
            </button>
          )
        }
      >
        {result.error}
      </Alert>
    );
  } else if (result?.status === "done") {
    const stale = result.params !== JSON.stringify(buildParams(mode, selections[mode.id] || {}));
    body = (
      <>
        {stale && (
          <Alert tone="info">
            Inputs changed. Click Analyze to update the results.
          </Alert>
        )}
        <div className="results-head">
          <span className="muted">Results for {dataset?.filename}</span>
          <button
            type="button"
            className="btn btn-ghost small"
            onClick={() => document.getElementById(`inputs-${mode.id}-card`)?.scrollIntoView({ behavior: "smooth", block: "start" })}
          >
            Change inputs
          </button>
        </div>
        <View data={result.data} />
      </>
    );
  } else {
    body = dataset ? <LoadedPanel dataset={dataset} /> : <StartPanel />;
  }

  return (
    <section className="card results-card" ref={panel} aria-live="polite" aria-busy={loading || result?.status === "loading"}>
      {datasetError && !loading && <Alert>{datasetError}</Alert>}
      {body}
    </section>
  );
}

export default function ModePage({ mode }) {
  useEffect(() => {
    document.title = `${mode.title} | InsightPulse`;
  }, [mode.title]);

  return (
    <div className="mode-page">
      <div className="page-head">
        <div>
          <h1 className="page-title">
            {mode.title}
            <InfoPopover info={mode.info} modeTitle={mode.title} />
          </h1>
          <p className="page-subtitle">{mode.subtitle}</p>
        </div>
        <DatasetBar />
      </div>
      <ResultsPanel mode={mode} />
      <InputsForm mode={mode} />
    </div>
  );
}
