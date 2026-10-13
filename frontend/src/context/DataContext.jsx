import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { analyze as apiAnalyze, fetchSampleFile, inspectFile } from "../lib/api.js";
import { suggestColumns, ROLES } from "../lib/autoMap.js";
import { ALL_VALUE, MODES, MODE_BY_ID, buildParams, initialSelections } from "../modes/config.js";

const DataContext = createContext(null);

function buildAllSelections(columns) {
  const roleNames = Object.keys(ROLES);
  const suggestions = suggestColumns(columns, roleNames);
  const all = {};
  MODES.forEach((mode) => {
    const modeRoles = [...new Set(mode.fields.map((f) => f.role).filter(Boolean))];
    all[mode.id] = initialSelections(mode, suggestColumns(columns, modeRoles));
  });
  return { all, suggestions };
}

export function DataProvider({ children }) {
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  const [datasetError, setDatasetError] = useState("");
  const [selections, setSelections] = useState({});
  const [results, setResults] = useState({});
  const [slow, setSlow] = useState(false);
  const generation = useRef(0);

  const resetResults = () => setResults({});

  const loadFile = useCallback(async (file, source) => {
    generation.current += 1;
    const mine = generation.current;
    setDatasetError("");
    setLoading(true);
    setLoadingText("Reading your file...");
    try {
      const meta = await inspectFile(file, { onSlow: () => setLoadingText("Still working. The server may take up to a minute to start...") });
      if (mine !== generation.current) return;
      const { all } = buildAllSelections(meta.columns);
      setDataset({ file, filename: meta.filename || file.name, rows: meta.rows, columns: meta.columns, preview: meta.preview, source });
      setSelections(all);
      resetResults();
    } catch (error) {
      if (mine !== generation.current) return;
      setDatasetError(error.message);
    } finally {
      if (mine === generation.current) setLoading(false);
    }
  }, []);

  const loadUpload = useCallback((file) => loadFile(file, { type: "upload" }), [loadFile]);

  const loadSample = useCallback(
    async (sample) => {
      generation.current += 1;
      const mine = generation.current;
      setDatasetError("");
      setLoading(true);
      setLoadingText("Loading sample data...");
      try {
        const file = await fetchSampleFile(sample);
        if (mine !== generation.current) return;
        await loadFile(file, { type: "sample", id: sample.id, name: sample.name });
      } catch (error) {
        if (mine !== generation.current) return;
        setDatasetError(error.message);
        setLoading(false);
      }
    },
    [loadFile]
  );

  const clearDataset = useCallback(() => {
    generation.current += 1;
    setDataset(null);
    setSelections({});
    setResults({});
    setDatasetError("");
    setLoading(false);
  }, []);

  const setSelection = useCallback((modeId, key, value) => {
    setSelections((current) => {
      const mode = MODE_BY_ID[modeId];
      const next = { ...(current[modeId] || {}), [key]: value };
      // Choosing a different filter column resets its value.
      mode.fields.forEach((field) => {
        if (field.type === "value" && field.column === key) next[field.key] = ALL_VALUE;
      });
      return { ...current, [modeId]: next };
    });
  }, []);

  const runAnalysis = useCallback(
    async (modeId) => {
      if (!dataset) return;
      const mode = MODE_BY_ID[modeId];
      const params = buildParams(mode, selections[modeId] || {});
      const mine = generation.current;
      setSlow(false);
      setResults((current) => ({ ...current, [modeId]: { status: "loading" } }));
      try {
        const data = await apiAnalyze(mode.api, dataset.file, params, { onSlow: () => setSlow(true) });
        if (mine !== generation.current) return;
        setResults((current) => ({ ...current, [modeId]: { status: "done", data } }));
      } catch (error) {
        if (mine !== generation.current) return;
        setResults((current) => ({ ...current, [modeId]: { status: "error", error: error.message } }));
      } finally {
        setSlow(false);
      }
    },
    [dataset, selections]
  );

  const value = useMemo(
    () => ({ dataset, loading, loadingText, datasetError, selections, results, slow, loadUpload, loadSample, clearDataset, setSelection, runAnalysis, setDatasetError }),
    [dataset, loading, loadingText, datasetError, selections, results, slow, loadUpload, loadSample, clearDataset, setSelection, runAnalysis]
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData() {
  const context = useContext(DataContext);
  if (!context) throw new Error("useData must be used inside DataProvider");
  return context;
}
