import { useEffect, useId, useRef, useState } from "react";
import { InfoIcon } from "./Icons.jsx";

export default function InfoPopover({ info, modeTitle }) {
  const [open, setOpen] = useState(false);
  const wrapper = useRef(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    const onPointer = (event) => {
      if (wrapper.current && !wrapper.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open]);

  return (
    <span
      className="info-wrap"
      ref={wrapper}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="info-button"
        aria-label={`About ${modeTitle}`}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen(true)}
        onFocus={() => setOpen(true)}
      >
        <InfoIcon />
      </button>
      {open && (
        <div className="info-popover" id={panelId} role="dialog" aria-label="Selected Mode Information">
          <h2 className="info-title">Selected Mode Information</h2>
          <ul className="info-list">
            {info.bullets.map((text) => (
              <li key={text}>{text}</li>
            ))}
            <li>
              {info.stepsTitle}
              <ol>
                {info.steps.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ol>
            </li>
            {info.after && (
              <li>
                {info.afterTitle}
                <ul className="info-sublist">
                  {info.after.map((text) => (
                    <li key={text}>{text}</li>
                  ))}
                </ul>
              </li>
            )}
          </ul>
        </div>
      )}
    </span>
  );
}
