# Travel Time Alerter

Dockerised web app that monitors Google Maps travel time and sends a Pushover notification when you should leave. Two alert modes: **Travel Time** and **Arrive Time**.

## Alert Modes

### Travel Time Mode
Alert when travel time drops at or below a threshold.
```
trigger when: travel_minutes <= alert_threshold_minutes
```

### Arrive Time Mode
Alert when leaving now (plus buffer) means you'd just barely arrive on time.
```
trigger when: now + travel_minutes + buffer_minutes >= arrive_by
```
Alerts fire every check cycle while condition is met and `active = true`. User turns off monitoring manually via UI.

## Project Structure

```
travel-time/
├── Dockerfile                    # multi-stage prod image: builds React, bakes into Python image
├── docker-compose.yml            # dev: builds locally, separate frontend-build profile
├── docker-compose.prod.yml       # prod: pulls prebuilt image from ghcr.io/iltc/travel-time
├── .env / .env.example
├── .github/workflows/
│   └── build-and-push.yml        # CI: builds and pushes image to ghcr.io
├── backend/
│   ├── Dockerfile                # used by docker-compose.yml (dev only)
│   ├── requirements.txt
│   └── app/
│       ├── api.py                # FastAPI app + serves built React files
│       ├── scheduler.py          # APScheduler entry point (runs every 10 min)
│       ├── db.py                 # SQLModel + SQLite (WAL); monitors / check_log / app_settings
│       ├── core.py               # Shared check-and-alert logic (used by api + scheduler)
│       ├── traffic.py            # Google Maps Distance Matrix API
│       ├── notify.py             # Pushover API + timezone-aware message builder
│       └── static/               # React build output (populated at build time)
└── frontend/
    ├── Dockerfile                # used by docker-compose.yml (dev only)
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── components/
            ├── GlobalSettings.jsx
            ├── MonitorList.jsx
            ├── MonitorForm.jsx
            └── CheckLog.jsx
```

## Database (SQLite + SQLModel)

- **`monitors`** — one row per monitor. Fields: `name` (optional label), `origin`, `destination`, `active`, `mode` (`travel_time`|`arrive_time`, default `arrive_time`), `alert_threshold_minutes`, `arrive_by` (unix ts), `buffer_minutes`.
- **`check_log`** — append-only. Fields: `monitor_id` (FK → monitors), `checked_at` (unix ts), `travel_minutes` (real), `alerted` (bool), `minutes_until_leave` (real, arrive_time only — `None` for travel_time).
- **`app_settings`** — key/value store for global settings. Keys: `checks_enabled` (`"true"`/`"false"`), `default_location` (origin fallback when a monitor's origin is blank), `timezone` (IANA tz used to render alert messages, default `America/New_York`). Values are always strings.
- WAL mode enabled so API reads and scheduler writes don't block each other.
- `init_db()` runs `SQLModel.metadata.create_all` plus a small ALTER-based migration for legacy DBs missing `check_log.minutes_until_leave`, then seeds `app_settings` defaults.

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/settings` | Get global app settings (key/value) |
| `PUT` | `/api/settings` | Update one or more global settings; returns the full updated map |
| `GET` | `/api/monitors` | List all monitors |
| `POST` | `/api/monitors` | Create a monitor |
| `GET` | `/api/monitors/{id}` | Get one monitor |
| `PUT` | `/api/monitors/{id}` | Update a monitor (all fields optional) |
| `DELETE` | `/api/monitors/{id}` | Delete monitor + its logs |
| `GET` | `/api/monitors/{id}/checks` | Check log for a monitor (`?limit=20`) |
| `DELETE` | `/api/monitors/{id}/checks` | Clear check log for a monitor |
| `POST` | `/api/monitors/{id}/checks/trigger` | Manually trigger a check (forces — bypasses `checks_enabled` and `active`) |
| `GET` | `/*` | Serve React app (catch-all) |

## Scheduler Logic

The scheduler and the API's manual-trigger endpoint share `core.run_check(monitor, *, force=False)`.

1. If `force=False` and `app_settings.checks_enabled == "false"` → skip.
2. If `force=False` and `monitor.active` is false → skip.
3. Resolve origin: `monitor.origin` or fall back to `app_settings.default_location`. If both blank → skip.
4. Call Google Maps Distance Matrix API → `travel_minutes`.
5. Evaluate alert condition based on `mode` (see Alert Modes above).
6. If triggered → send Pushover notification (message includes projected arrival time formatted in the configured `timezone`).
7. For arrive_time monitors, compute `minutes_until_leave = (arrive_by − travel − buffer − now) / 60`.
8. Append a row to `check_log` (with `minutes_until_leave` for arrive_time, `None` otherwise).

The blocking `APScheduler` job in `scheduler.py` runs the above for every active monitor every 10 minutes (and once at startup). The API's `POST /checks/trigger` calls the same function with `force=True` so manual checks work even when checks are paused or the monitor is inactive.

## Build & Deploy

Two flows are supported. See `README.md` for full instructions.

**Dev / build-from-source (`docker-compose.yml`)** — uses `backend/Dockerfile` + `frontend/Dockerfile`:

```bash
docker compose --profile build run --rm frontend-build   # build React once into the react_dist volume
docker compose up -d api scheduler                       # start the app
```

`api` and `scheduler` share the `db_data` volume; `api` mounts `react_dist` read-only at `/app/app/static/`.

**Prod / prebuilt image (`docker-compose.prod.yml`)** — single combined image at `ghcr.io/iltc/travel-time:latest`, built and pushed by `.github/workflows/build-and-push.yml` on every push to `main`. Both `web` and `scheduler` services run from the same image; the React bundle is baked into `/app/app/static/` at image-build time, so no `frontend-build` step is needed on the server.

## Environment Variables (.env)

See `.env.example` for a template.

- `GOOGLE_MAPS_API_KEY`
- `PUSHOVER_TOKEN`
- `PUSHOVER_USER`
- `DB_PATH` — defaults to `/app/data/travel.db`

Runtime app behavior (timezone, default origin, paused state) lives in the `app_settings` DB table, not in the env.

## Tech Stack

- **Backend**: FastAPI, uvicorn, httpx, APScheduler, SQLModel (over SQLite), python-dotenv, `zoneinfo` for tz formatting
- **Frontend**: React (Vite)
- **Database**: SQLite (WAL mode) via SQLModel
- **Notifications**: Pushover
- **Traffic data**: Google Maps Distance Matrix API
- **CI / Registry**: GitHub Actions → GHCR (`ghcr.io/iltc/travel-time`)

## Dev Notes

- `arrive_by` is stored as a unix timestamp — timezone-agnostic. The React UI sends it from a local datetime picker; the `app_settings.timezone` value is only used to *render* arrival/leave-by times in alert messages.
- `app_settings.default_location` is used as the origin when a monitor's own `origin` is blank — handy when most monitors leave from the same place.
- The `Check Now` button in the UI calls `POST /api/monitors/{id}/checks/trigger`, which forces a check regardless of `checks_enabled` or the per-monitor `active` flag.
- In dev, configure Vite proxy to forward `/api` to `localhost:8000`.
