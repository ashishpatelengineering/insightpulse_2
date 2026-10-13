import { useEffect, useRef, useState } from "react";
import { listSamples } from "../lib/api.js";
import { formatNumber } from "../lib/format.js";
import { useData } from "../context/DataContext.jsx";
import { ChevronIcon, CloseIcon, FileIcon, UploadIcon } from "./Icons.jsx";
import PreviewModal from "./PreviewModal.jsx";

const MAX_BYTES = 25 * 1024 * 1024;

export function useUploadHandler() {
  const { loadUpload, setDatasetError } = useData();
  return (file) => {
    if (!file) return;
    const name = file.name.toLowerCase();
    if (/\.(xlsx|xls|xlsm)$/.test(name)) {
      setDatasetError("Please upload a CSV file. In Excel, choose File > Save As > CSV.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setDatasetError("This file is larger than 25 MB. Please upload a smaller extract.");
      return;
    }
    loadUpload(file);
  };
}

export default function DatasetBar() {
  const { dataset, loading, loadSample, clearDataset } = useData();
  const handleUpload = useUploadHandler();
  const [samples, setSamples] = useState([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const fileInput = useRef(null);
  const menu = useRef(null);

  useEffect(() => {
    let cancelled = false;
    listSamples()
      .then((list) => !cancelled && setSamples(list))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const onPointer = (event) => {
      if (menu.current && !menu.current.contains(event.target)) setMenuOpen(false);
    };
    const onKey = (event) => event.key === "Escape" && setMenuOpen(false);
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  return (
    <div className="dataset-bar">
      {dataset && (
        <div className="dataset-chip" title={dataset.filename}>
          <FileIcon />
          <button type="button" className="chip-main" onClick={() => setPreviewOpen(true)} aria-label="Preview your data">
            <span className="chip-name">{dataset.filename}</span>
            <span className="chip-rows">{formatNumber(dataset.rows)} rows</span>
          </button>
          <button type="button" className="chip-clear" onClick={clearDataset} aria-label="Remove dataset">
            <CloseIcon size={14} />
          </button>
        </div>
      )}

      {samples.length > 0 && (
        <div className="menu-wrap" ref={menu}>
          <button type="button" className="btn btn-ghost" onClick={() => setMenuOpen((o) => !o)} aria-haspopup="menu" aria-expanded={menuOpen} disabled={loading}>
            Sample data <ChevronIcon />
          </button>
          {menuOpen && (
            <div className="menu" role="menu">
              <div className="menu-heading">Try a ready made dataset</div>
              {samples.map((sample) => (
                <button
                  key={sample.id}
                  type="button"
                  role="menuitem"
                  className="menu-item"
                  onClick={() => {
                    setMenuOpen(false);
                    loadSample(sample);
                  }}
                >
                  <span className="menu-item-title">{sample.name}</span>
                  <span className="menu-item-text">{sample.description}</span>
                  <span className="menu-item-meta">{formatNumber(sample.rows)} rows</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <button type="button" className="btn btn-outline" onClick={() => fileInput.current?.click()} disabled={loading}>
        <UploadIcon /> Upload
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
      {previewOpen && dataset && <PreviewModal dataset={dataset} onClose={() => setPreviewOpen(false)} />}
    </div>
  );
}
