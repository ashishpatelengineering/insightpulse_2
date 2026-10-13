import { useRef } from "react";
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

export function UploadButton({ primary = false }) {
  const { loading } = useData();
  const handleUpload = useUploadHandler();
  const fileInput = useRef(null);
  return (
    <>
      <button
        type="button"
        className={primary ? "btn btn-primary" : "btn btn-outline"}
        onClick={() => fileInput.current?.click()}
        disabled={loading}
      >
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
    </>
  );
}

export default function DatasetBar() {
  const { dataset, clearDataset } = useData();
  if (!dataset) return null;

  return (
    <div className="dataset-bar">
      <div className="dataset-chip" title={dataset.filename}>
        <FileIcon />
        <span className="chip-main">
          <span className="chip-name">{dataset.filename}</span>
        </span>
        <button type="button" className="chip-clear" onClick={clearDataset} aria-label="Remove dataset">
          <CloseIcon size={14} />
        </button>
      </div>
      <UploadButton />
    </div>
  );
}
