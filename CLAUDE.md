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
├── docker-compose.yml
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── api.py              # FastAPI app + serves built React files
│       ├── scheduler.py        # APScheduler entry point (runs every 10 min)
│       ├── db.py               # SQLite with WAL mode, CRUD for monitors + check_log
│       ├── core.py             # Shared check-and-alert logic (used by api + scheduler)
│       ├── traffic.py          # Google Maps Distance Matrix API
│       ├── notify.py           # Pushover API
│       └── static/             # React build output (populated at build time)
└── frontend/
    ├── Dockerfile              # multi-stage: build React → copy into backend/app/static
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── components/
            ├── MonitorList.jsx
            ├── MonitorForm.jsx
            └── CheckLog.jsx
```

## Database (SQLite)

- **`monitors`** — one row per monitor. Fields: `name` (optional label), `origin`, `destination`, `active`, `mode` (`travel_time`|`arrive_time`), `alert_threshold_minutes`, `arrive_by` (unix ts), `buffer_minutes`.
- **`check_log`** — append-only. Fields: `monitor_id` (FK → monitors), `checked_at` (unix ts), `travel_minutes` (real), `alerted` (bool).
- WAL mode enabled so API reads and scheduler writes don't block each other.
- SQLite stores booleans as INTEGER 0/1 — cast to `bool` in Python.

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/monitors` | List all monitors |
| `POST` | `/api/monitors` | Create a monitor |
| `GET` | `/api/monitors/{id}` | Get one monitor |
| `PUT` | `/api/monitors/{id}` | Update a monitor (all fields optional) |
| `DELETE` | `/api/monitors/{id}` | Delete monitor + its logs |
| `GET` | `/api/monitors/{id}/checks` | Check log for a monitor (`?limit=20`) |
| `DELETE` | `/api/monitors/{id}/checks` | Clear check log for a monitor |
| `POST` | `/api/monitors/{id}/checks/trigger` | Manually trigger a check for a monitor |
| `GET` | `/*` | Serve React app (catch-all) |

## Scheduler Logic

1. Read all monitors → for each active monitor:
2. Call Google Maps Distance Matrix API → `travel_minutes`
3. Evaluate alert condition based on `mode`
4. If triggered → send Pushover notification
5. Append to `check_log` with `monitor_id`

## Build & Deploy

```bash
docker compose --profile build run frontend-build   # build React once
docker compose up -d api scheduler                   # start the app
```

Frontend builds first, output goes to a shared volume mounted at `backend/app/static/`. Both `api` and `scheduler` services share the `db_data` volume.

## Environment Variables (.env)

- `GOOGLE_MAPS_API_KEY`
- `PUSHOVER_TOKEN`
- `PUSHOVER_USER`
- `DB_PATH` — defaults to `/app/data/travel.db`

## Tech Stack

- **Backend**: FastAPI, uvicorn, httpx, APScheduler, python-dotenv
- **Frontend**: React (Vite)
- **Database**: SQLite
- **Notifications**: Pushover
- **Traffic data**: Google Maps Distance Matrix API

## Dev Notes

- `arrive_by` is a unix timestamp — timezone-agnostic. React UI sends it from a local datetime picker.
- In dev, configure Vite proxy to forward `/api` to `localhost:8000`.
