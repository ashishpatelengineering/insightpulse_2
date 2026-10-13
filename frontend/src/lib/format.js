const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  return `${Number(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })}%`;
}

/** "2026-10" becomes "Oct 2026". */
export function formatMonth(value) {
  if (!value) return "";
  const [year, month] = String(value).split("-");
  const index = Number(month) - 1;
  if (!year || index < 0 || index > 11) return String(value);
  return `${MONTHS[index]} ${year}`;
}

/** "2026-10-05" becomes "5 Oct 2026". */
export function formatDate(value) {
  if (!value) return "";
  const [year, month, day] = String(value).split("-");
  const index = Number(month) - 1;
  if (!year || index < 0 || index > 11) return String(value);
  return `${Number(day)} ${MONTHS[index]} ${year}`;
}

export function compactNumber(value) {
  if (value === null || value === undefined) return "";
  const abs = Math.abs(value);
  if (abs >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(abs >= 1e4 ? 0 : 1)}K`;
  return String(Math.round(value));
}
