import { useEffect, useRef } from "react";
import { useData } from "../context/DataContext.jsx";
import DatasetBar from "./DatasetBar.jsx";
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

function ResultsPanel({ mode }) {
  const { results, loading, loadingText, datasetError, slow, dataset, runAnalysis } = useData();
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
    body = <View data={result.data} />;
  } else {
    body = (
      <div className="empty-state">
        <div className="empty-title">No Data</div>
        <p>{dataset ? "Check the inputs below, then click Analyze to see your results." : "Upload a CSV file or choose sample data to get started."}</p>
      </div>
    );
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
        <h1 className="page-title">
          {mode.title}
          <InfoPopover info={mode.info} modeTitle={mode.title} />
        </h1>
        <DatasetBar />
      </div>
      <ResultsPanel mode={mode} />
      <InputsForm mode={mode} />
    </div>
  );
}
