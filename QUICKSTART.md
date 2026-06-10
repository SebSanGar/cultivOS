# cultivOS — Quickstart

Two ways in. Local takes one command.

## Option A — Run it on your machine (one command)

**Prereqs:** `git` and Python 3.11+ (`run.sh` builds the venv and installs everything for you;
if it can't find 3.11+ it tells you the one command to install it).

```bash
git clone git@github.com:SebSanGar/cultivOS.git
cd cultivOS
./run.sh
```

Then open **http://localhost:8000**.

`./run.sh` is idempotent — run it any time. It:
1. Builds a Python 3.11+ virtualenv (`venv/`) if missing
2. Installs dependencies
3. Creates a local dev `.env` (auth off, dev JWT secret)
4. Seeds demo data (3 farms × 3 fields, color-coded health) so the dashboard isn't empty
5. Starts the server on port 8000 (auto-reload on code changes under `src/`)

**Login:** none needed locally — `AUTH_ENABLED=false` in dev, so the app opens straight to the
dashboard.

**Language:** the dashboard has an **ES | EN** toggle in the nav (defaults to Spanish, persists
your choice).

## Option B — Live hosted app (zero setup)

Open **https://app.cultivosagro.com** in a browser. Nothing to install — good for a quick click-through.

## Troubleshooting

- **Stale styles after a pull** → hard-refresh the browser (Cmd/Ctrl+Shift+R).
- **Old `venv` on Python 3.9/3.10** → `run.sh` detects and rebuilds it automatically. To force:
  `rm -rf venv && ./run.sh`.
- **Port 8000 busy** → `run.sh` frees it on start; if it persists, `lsof -ti:8000 | xargs kill -9`.
- **Tests:** `PYTHONPATH="$PWD/src" venv/bin/python -m pytest -q`

## Repo access

Repo: **SebSanGar/cultivOS** (private). If you can't clone, ask Seb to confirm your GitHub
collaborator invite (push access).
