import { useEffect, useRef } from "react";
import { useData } from "../context/DataContext.jsx";
import { buildParams } from "../modes/config.js";
import DatasetBar, { UploadButton } from "./DatasetBar.jsx";
import DataGrid from "./DataGrid.jsx";
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
  return (
    <div className="start-panel">
      <h2 className="start-title">Upload a CSV file to get started</h2>
      <UploadButton primary />
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
    body = <Spinner label={slow ? "Still working. The server may take up to a minute to wake up..." : "Analyzing data..."} />;
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
        <View data={result.data} />
      </>
    );
  } else {
    body = dataset ? null : <StartPanel />;
  }

  if (!body && !(datasetError && !loading)) return null;

  return (
    <section className="card results-card" ref={panel} aria-live="polite" aria-busy={loading || result?.status === "loading"}>
      {datasetError && !loading && <Alert>{datasetError}</Alert>}
      {body}
    </section>
  );
}

export default function ModePage({ mode }) {
  const { dataset } = useData();
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
        </div>
        <DatasetBar />
      </div>
      {dataset && <DataGrid dataset={dataset} />}
      <ResultsPanel mode={mode} />
      {dataset && <InputsForm mode={mode} />}
    </div>
  );
}
