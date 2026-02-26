"""
FastAPI application — REST API + serves the React production build.

Run as:  uvicorn app.api:app --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.db import init_db, get_settings, upsert_settings, get_check_log, clear_check_log
from app.core import run_check

app = FastAPI(title="Travel Time Alerter")

STATIC_DIR = Path(__file__).parent / "static"


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SettingsUpdate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    active: Optional[bool] = None
    mode: Optional[str] = None
    alert_threshold_minutes: Optional[int] = None
    arrive_by: Optional[int] = None
    buffer_minutes: Optional[int] = None


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/api/settings")
def read_settings():
    return get_settings()


@app.put("/api/settings")
def update_settings(body: SettingsUpdate):
    data = body.model_dump(exclude_none=True)
    return upsert_settings(data)


@app.get("/api/checks")
def read_checks(limit: int = Query(default=20, ge=1, le=200)):
    return get_check_log(limit)


@app.delete("/api/checks")
def delete_checks():
    clear_check_log()
    return {"ok": True}


@app.post("/api/checks/trigger")
async def trigger_check():
    result = await run_check()
    if result is None:
        return {"error": "Monitoring inactive or origin/destination not configured."}
    return result


# ---------------------------------------------------------------------------
# Serve React static files (catch-all must be last)
# ---------------------------------------------------------------------------

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = STATIC_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
