import { useEffect, useId, useRef, useState } from "react";
import { InfoIcon } from "./Icons.jsx";

const WIDTH = 300;

/** Small (i) icon that shows a short description on hover, focus or tap. */
export default function Tip({ text, label = "More information" }) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const wrapper = useRef(null);
  const id = useId();

  const show = () => {
    const rect = wrapper.current?.getBoundingClientRect();
    if (rect) {
      const left = Math.min(Math.max(12, rect.left + rect.width / 2 - WIDTH / 2), window.innerWidth - WIDTH - 12);
      setPos({ top: rect.bottom + 8, left });
    }
    setOpen(true);
  };

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    const onPointer = (event) => {
      if (wrapper.current && !wrapper.current.contains(event.target)) setOpen(false);
    };
    const onScroll = () => setOpen(false);
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    window.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [open]);

  if (!text) return null;
  return (
    <span className="tip-wrap" ref={wrapper} onMouseEnter={show} onMouseLeave={() => setOpen(false)}>
      <button type="button" className="tip-button" aria-label={label} aria-describedby={open ? id : undefined} onFocus={show} onBlur={() => setOpen(false)} onClick={show}>
        <InfoIcon size={14} />
      </button>
      {open && (
        <span className="tip-popover" id={id} role="tooltip" style={{ top: pos.top, left: pos.left, width: WIDTH }}>
          {text}
        </span>
      )}
    </span>
  );
}
