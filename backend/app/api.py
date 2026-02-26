"""
FastAPI application — REST API + serves the React production build.

Run as:  uvicorn app.api:app --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.db import (
    init_db,
    get_all_monitors,
    get_monitor,
    create_monitor,
    update_monitor,
    delete_monitor,
    get_check_log,
    clear_check_log,
)
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

class MonitorCreate(BaseModel):
    name: Optional[str] = ""
    origin: Optional[str] = ""
    destination: Optional[str] = ""
    active: Optional[bool] = False
    mode: Optional[str] = "travel_time"
    alert_threshold_minutes: Optional[int] = None
    arrive_by: Optional[int] = None
    buffer_minutes: Optional[int] = None


class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    active: Optional[bool] = None
    mode: Optional[str] = None
    alert_threshold_minutes: Optional[int] = None
    arrive_by: Optional[int] = None
    buffer_minutes: Optional[int] = None


# ---------------------------------------------------------------------------
# Monitor routes
# ---------------------------------------------------------------------------

@app.get("/api/monitors")
def list_monitors():
    return get_all_monitors()


@app.post("/api/monitors", status_code=201)
def create_monitor_route(body: MonitorCreate):
    return create_monitor(body.model_dump())


@app.get("/api/monitors/{id}")
def get_monitor_route(id: int):
    monitor = get_monitor(id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@app.put("/api/monitors/{id}")
def update_monitor_route(id: int, body: MonitorUpdate):
    monitor = update_monitor(id, body.model_dump(exclude_none=True))
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@app.delete("/api/monitors/{id}")
def delete_monitor_route(id: int):
    if not delete_monitor(id):
        raise HTTPException(status_code=404, detail="Monitor not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Per-monitor check log routes
# ---------------------------------------------------------------------------

@app.get("/api/monitors/{id}/checks")
def read_checks(id: int, limit: int = Query(default=20, ge=1, le=200)):
    if not get_monitor(id):
        raise HTTPException(status_code=404, detail="Monitor not found")
    return get_check_log(monitor_id=id, limit=limit)


@app.delete("/api/monitors/{id}/checks")
def delete_checks(id: int):
    if not get_monitor(id):
        raise HTTPException(status_code=404, detail="Monitor not found")
    clear_check_log(monitor_id=id)
    return {"ok": True}


@app.post("/api/monitors/{id}/checks/trigger")
async def trigger_check(id: int):
    monitor = get_monitor(id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    result = await run_check(monitor)
    if result is None:
        return {"error": "Monitor inactive or origin/destination not configured."}
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
