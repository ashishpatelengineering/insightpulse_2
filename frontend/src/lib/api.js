const RETRY_STATUSES = new Set([502, 503, 504]);
const SLOW_AFTER_MS = 8000;
const TIMEOUT_MS = 180000;
const MAX_ATTEMPTS = 4;

export class ApiError extends Error {}

const NETWORK_MESSAGE =
  "We could not reach the server. Please check your internet connection and try again in a moment.";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Fetch with automatic retries. Hosted servers can take up to a minute to wake up after a quiet
 * period, so brief network errors and gateway errors are retried a few times before giving up.
 */
async function request(url, options = {}, { onSlow } = {}) {
  let lastError = null;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    const slowTimer = onSlow ? setTimeout(onSlow, SLOW_AFTER_MS) : null;
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      if (RETRY_STATUSES.has(response.status) && attempt < MAX_ATTEMPTS) {
        lastError = new ApiError(NETWORK_MESSAGE);
        await sleep(3000 * attempt);
        continue;
      }
      return response;
    } catch (error) {
      lastError = new ApiError(
        error?.name === "AbortError"
          ? "This is taking longer than expected. Please try again, or use a smaller file."
          : NETWORK_MESSAGE
      );
      if (attempt < MAX_ATTEMPTS && error?.name !== "AbortError") {
        await sleep(3000 * attempt);
        continue;
      }
    } finally {
      clearTimeout(timeout);
      if (slowTimer) clearTimeout(slowTimer);
    }
  }
  throw lastError || new ApiError(NETWORK_MESSAGE);
}

async function readJson(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    const message =
      (body && (body.error || (typeof body.detail === "string" ? body.detail : null))) ||
      "Something went wrong. Please try again.";
    throw new ApiError(message);
  }
  return body;
}

export async function listSamples() {
  const response = await request("/api/samples");
  return readJson(response);
}

export async function fetchSampleFile(sample) {
  const response = await request(`/api/samples/${encodeURIComponent(sample.id)}`);
  if (!response.ok) throw new ApiError("The sample dataset could not be loaded. Please try again.");
  const blob = await response.blob();
  return new File([blob], sample.filename, { type: "text/csv" });
}

export async function inspectFile(file, options) {
  const form = new FormData();
  form.append("file", file);
  const response = await request("/api/inspect", { method: "POST", body: form }, options);
  return readJson(response);
}

export async function analyze(mode, file, params, options) {
  const form = new FormData();
  form.append("file", file);
  form.append("params", JSON.stringify(params));
  const response = await request(`/api/analyze/${mode}`, { method: "POST", body: form }, options);
  return readJson(response);
}
