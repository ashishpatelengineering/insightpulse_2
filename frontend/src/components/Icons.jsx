const base = {
  width: 28,
  height: 28,
  viewBox: "0 0 32 32",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.9,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
  focusable: false,
};

export function ModeIcon({ name, size = 28 }) {
  const props = { ...base, width: size, height: size };
  switch (name) {
    case "clv":
      return (
        <svg {...props}>
          <circle cx="16" cy="9.5" r="4" />
          <circle cx="6.5" cy="12.5" r="2.8" />
          <circle cx="25.5" cy="12.5" r="2.8" />
          <path d="M9.5 25c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5" />
          <path d="M2.5 23.5c0-2.6 1.9-4.6 4.2-4.6M29.5 23.5c0-2.6-1.9-4.6-4.2-4.6" />
        </svg>
      );
    case "recommendation":
      return (
        <svg {...props}>
          <path d="M5 11.5 16 6l11 5.5v10L16 27 5 21.5z" />
          <path d="M5 11.5 16 17l11-5.5M16 17v10" />
          <path d="m22.5 3.5.8 1.9 1.9.8-1.9.8-.8 1.9-.8-1.9-1.9-.8 1.9-.8z" />
        </svg>
      );
    case "basket":
      return (
        <svg {...props}>
          <path d="M3.5 12h25l-2.6 12.2a2 2 0 0 1-2 1.6H8.1a2 2 0 0 1-2-1.6z" />
          <path d="m10 12 4-7M22 12l-4-7" />
          <path d="M12 17v4M16 17v4M20 17v4" />
        </svg>
      );
    case "forecast":
      return (
        <svg {...props}>
          <path d="M4 27V5" />
          <path d="M4 27h24" />
          <rect x="8" y="18" width="3.4" height="6" rx="0.8" />
          <rect x="14" y="14" width="3.4" height="10" rx="0.8" />
          <rect x="20" y="10" width="3.4" height="14" rx="0.8" />
          <path d="m8 12 6-4.5 5 2.5 8-6.5M23 3.5h4v4" />
        </svg>
      );
    default:
      return null;
  }
}

export function InfoIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <circle cx="12" cy="12" r="9.2" />
      <path d="M12 11v5.5" />
      <circle cx="12" cy="7.6" r="0.6" fill="currentColor" />
    </svg>
  );
}

export function UploadIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M12 16V4M7.5 8.5 12 4l4.5 4.5" />
      <path d="M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15" />
    </svg>
  );
}

export function DownloadIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M12 4v12M7.5 11.5 12 16l4.5-4.5" />
      <path d="M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15" />
    </svg>
  );
}

export function ChevronIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

export function CloseIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  );
}

export function FileIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
    </svg>
  );
}

export function LogoMark({ size = 30 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <rect width="32" height="32" rx="8" fill="#0b5ea8" />
      <path d="M5 17h5l3-8 5 15 3-9h6" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
