# Travel Time Alerter

Dockerised web app that monitors Google Maps travel time and sends a Pushover notification when you should leave. Two alert modes: **Travel Time** (alert when traffic is light enough) and **Arrive Time** (alert when leaving now means you'd just barely arrive on time).

The UI also has a small **Global Settings** panel for app-wide options: a master "checks enabled" pause toggle, a default origin location used when a monitor's origin is blank, and the timezone used to format times in alert messages.

See `CLAUDE.md` for a deeper architecture / data-model reference.

## Prerequisites

- A `.env` file at the repo root. Copy the template and fill in the values:
  ```bash
  cp .env.example .env
  ```
  Required keys: `GOOGLE_MAPS_API_KEY`, `PUSHOVER_TOKEN`, `PUSHOVER_USER`, `DB_PATH`.
- For local dev: [`uv`](https://docs.astral.sh/uv/) and Node.js 20+.
- For deployment: Docker + Docker Compose.

## Run locally (dev mode)

The backend (FastAPI on `:8000`) and the frontend (Vite on `:5173`) run as separate processes. Vite proxies `/api` → `localhost:8000`, so you hit the Vite URL in your browser and API calls are forwarded automatically.

### One-time setup

If `backend/app/static/` exists but is empty, the API will fail to mount the static assets. Either build the frontend once, or remove the empty directory:

```bash
rm -rf backend/app/static
```

(It will be recreated by the docker build flow when you ship.)

### Terminal 1 — Backend API

```bash
cd backend
uv venv
uv pip install -r requirements.txt
set -a; source ../.env; set +a
DB_PATH=./travel.db uv run uvicorn app.api:app --reload --port 8000
```

`DB_PATH=./travel.db` overrides the in-container path so SQLite writes to a local file (`backend/travel.db`).

### Terminal 2 — Scheduler (optional)

Only needed if you want the periodic checks running locally. The API works without it.

```bash
cd backend
set -a; source ../.env; set +a
DB_PATH=./travel.db uv run python -m app.scheduler
```

The scheduler must point at the same `DB_PATH` as the API.

### Terminal 3 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually <http://localhost:5173>).

## Build & run with Docker

The frontend is built once into a shared volume, then `api` and `scheduler` services mount it read-only.

```bash
# Build the React bundle (writes to the react_dist volume)
docker compose --profile build run --rm frontend-build

# Start API + scheduler
docker compose up -d api scheduler
```

API will be live on <http://localhost:8000>. The SQLite database persists in the `db_data` volume.

### Updating after a code change

```bash
docker compose --profile build run --rm frontend-build   # if frontend changed
docker compose up -d --build api scheduler               # rebuild backend image
```

### Stopping

```bash
docker compose down                # stop containers, keep volumes
docker compose down -v             # also wipe db_data + react_dist
```

## Deploy via prebuilt image (ghcr.io)

For servers that can't clone source. The single image at `ghcr.io/iltc/travel-time` contains both the Python backend and the prebuilt React frontend.

### How images get built

`.github/workflows/build-and-push.yml` builds and pushes on every push to `main` (also on `v*` tags). Tags published:

- `latest` — tip of `main`
- `main` — same as latest
- `sha-<short>` — pinned to a commit
- `v1.2.3` — when you cut a git tag

The package is private by default — pulls require auth. Manage visibility at <https://github.com/users/iltc/packages/container/travel-time/settings>.

### Server setup

The deploy box only needs `docker-compose.prod.yml` and `.env`. One-time login with a GitHub Personal Access Token (classic, `read:packages` scope):

```bash
echo $GHCR_PAT | docker login ghcr.io -u iltc --password-stdin
```

Then pull and start:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Updating

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Pinning to a specific build: edit `docker-compose.prod.yml` and change `:latest` to e.g. `:sha-abc1234` or `:v1.2.3`.

### Building locally without Actions

If you ever need to bypass CI:

```bash
docker build -t ghcr.io/iltc/travel-time:latest .
echo $GHCR_PAT | docker login ghcr.io -u iltc --password-stdin
docker push ghcr.io/iltc/travel-time:latest
```

The PAT needs `write:packages` scope for pushing.

## Inspecting the database

Local dev DB:

```bash
sqlite3 backend/travel.db .tables
```

Dockerised DB:

```bash
docker compose run --rm api sqlite3 /app/data/travel.db .tables
```
