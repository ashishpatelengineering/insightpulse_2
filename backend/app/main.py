"""InsightPulse API and static front end."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import basket, clv, forecast, recommend
from .common import MAX_UPLOAD_BYTES, UserError, profile_table, read_table, to_jsonable
from .samples import list_samples, sample_path

logger = logging.getLogger("insightpulse")
logging.basicConfig(level=logging.INFO)

MODES = {
    "clv": clv.run,
    "recommendation": recommend.run,
    "basket": basket.run,
    "forecast": forecast.run,
}

app = FastAPI(title="InsightPulse", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GENERIC_ERROR = (
    "Something went wrong while analyzing your data. Please check that each input is matched to the right column and try again."
)


@app.exception_handler(UserError)
async def user_error_handler(_: Request, exc: UserError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": GENERIC_ERROR})


async def _read_upload(file: UploadFile) -> bytes:
    data = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_UPLOAD_BYTES:
            raise UserError(f"This file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB. Please upload a smaller extract.")
    return bytes(data)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/samples")
def samples() -> list[dict]:
    return list_samples()


@app.get("/api/samples/{sample_id}")
def sample_file(sample_id: str):
    path = sample_path(sample_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Sample not found")
    return FileResponse(path, media_type="text/csv", filename=path.name)


@app.post("/api/inspect")
async def inspect_file(file: UploadFile = File(...)) -> dict:
    data = await _read_upload(file)
    df = read_table(data, file.filename or "")
    return to_jsonable(
        {
            "filename": file.filename,
            "rows": int(len(df)),
            "columns": profile_table(df),
            "preview": df.head(8).fillna("").to_dict("records"),
        }
    )


@app.post("/api/analyze/{mode}")
async def analyze(mode: str, file: UploadFile = File(...), params: str = Form("{}")) -> JSONResponse:
    handler = MODES.get(mode)
    if handler is None:
        raise HTTPException(status_code=404, detail="Unknown mode")
    try:
        parsed = json.loads(params or "{}")
        if not isinstance(parsed, dict):
            raise ValueError
    except ValueError:
        raise UserError("The selections could not be read. Please refresh the page and try again.")
    data = await _read_upload(file)
    df = read_table(data, file.filename or "")
    result = handler(df, parsed)
    return JSONResponse(content=to_jsonable(result))


# ---------------------------------------------------------------------------
# Front end (built files), with fallback to index.html for client side routes
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"))

if FRONTEND_DIR.exists():
    assets = FRONTEND_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (FRONTEND_DIR / full_path).resolve()
        if full_path and candidate.is_file() and FRONTEND_DIR.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIR / "index.html")
