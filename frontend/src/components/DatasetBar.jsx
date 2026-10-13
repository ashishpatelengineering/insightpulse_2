import { useRef } from "react";
import { formatNumber } from "../lib/format.js";
import { useData } from "../context/DataContext.jsx";
import { CloseIcon, FileIcon, UploadIcon } from "./Icons.jsx";

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
  const { dataset, loading, clearDataset } = useData();
  const handleUpload = useUploadHandler();
  const fileInput = useRef(null);

  return (
    <div className="dataset-bar">
      {dataset && (
        <div className="dataset-chip" title={dataset.filename}>
          <FileIcon />
          <span className="chip-main">
            <span className="chip-name">{dataset.filename}</span>
            <span className="chip-rows">{formatNumber(dataset.rows)} rows</span>
          </span>
          <button type="button" className="chip-clear" onClick={clearDataset} aria-label="Remove dataset">
            <CloseIcon size={14} />
          </button>
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
    </div>
  );
}
