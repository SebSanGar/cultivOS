# cultivOS Deployment Runbook

This is how we deploy cultivOS. Every step here is the standard — follow it top-to-bottom on every production deploy.

---

## Overview

cultivOS runs as a single container. The backend (FastAPI + SQLite) serves both the API on `/api/` and the static frontend from `/`. Railway builds from the `Dockerfile` at repo root. No separate frontend build step — the `frontend/` directory is baked into the image at build time.

---

## 1. Railway Deploy Flow

1. Connect the `sebsangar/cultivos` GitHub repository to Railway (one-time setup via Railway dashboard > New Project > Deploy from GitHub).
2. Railway auto-detects `railway.toml` and uses the `DOCKERFILE` builder.
3. Every push to `main` triggers a new Railway build automatically. Do not push to main without passing CI on the branch first.
4. To deploy a specific commit manually: Railway dashboard > Deployments > Trigger Deploy.
5. The running service URL is shown in Railway dashboard under the service settings. Set a custom domain there if needed.

### Build process (what Railway does)

```
docker build -t cultivos .
```

The `Dockerfile` is a two-stage build: `builder` installs Python deps, `runtime` copies installed packages + source + frontend. The resulting image is lean (~200 MB).

---

## 2. Environment Variable Checklist

Set these in Railway's "Variables" tab before the first deploy. Variables marked **required** will break the app if missing.

| Variable | Required | Description |
|---|---|---|
| `DB_URL` | **required** | `sqlite:///cultivos.db` for SQLite (default). Use a full Postgres URL for production scale. |
| `AUTH_ENABLED` | **required** | Set to `true`. Never `false` in production. |
| `JWT_SECRET_KEY` | **required** | 64-char random string — see section 5. |
| `LOG_LEVEL` | recommended | `INFO` for production, `DEBUG` for troubleshooting. |
| `CORS_ORIGINS` | recommended | Comma-separated allowed origins. E.g. `https://app.cultivos.io,https://cultivos.io`. |
| `WHATSAPP_API_TOKEN` | optional | Required for alert notifications. See section 6. |
| `WHATSAPP_PHONE_ID` | optional | Required for alert notifications. See section 6. |
| `OPENWEATHER_API_KEY` | optional | Required for weather overlays. Free tier is sufficient for MVP. |
| `S3_BUCKET` | optional | S3-compatible bucket name for drone imagery. See section 7. |
| `S3_ENDPOINT` | optional | S3 endpoint URL (for non-AWS providers like Backblaze B2 or Cloudflare R2). |
| `AWS_ACCESS_KEY_ID` | optional | S3 credentials. |
| `AWS_SECRET_ACCESS_KEY` | optional | S3 credentials. |
| `ANTHROPIC_API_KEY` | optional | Enables AI-powered agronomic recommendations. |
| `REDIS_URL` | optional | `redis://...` — enables background task queue. App runs without it. |

Copy `.env.example` to `.env` for local development. Never commit `.env`.

---

## 3. Database Initialization

**Current state**: SQLite with `create_all` at startup.

On first boot, the app calls `SQLAlchemy`'s `create_all()` inside the FastAPI lifespan handler (`src/cultivos/app.py`). This creates all tables from the ORM models if they do not exist. No manual migration step required for a fresh deploy.

On Railway, the SQLite file lives inside the container filesystem at `/app/cultivos.db`. This means **the database is wiped on every redeploy** unless a persistent volume is attached.

**For production with persistent data**:
1. Add a Railway Volume mounted at `/app` (Railway dashboard > service > Volumes > Add Volume, mount path `/app`).
2. On first deploy with the volume, the app creates `cultivos.db` inside the volume. Subsequent deploys reuse the same file.

**Alembic (planned — N9)**: Schema migrations via Alembic are on the backlog. Until N9 lands, schema changes require a fresh `create_all` (acceptable at MVP scale). When Alembic is live, the startup will run `alembic upgrade head` instead.

**For Postgres**: Set `DB_URL=postgresql+psycopg2://user:pass@host/dbname`. The ORM models are SQLAlchemy-standard and work with Postgres without changes.

---

## 4. JWT Secret Generation

Before deploying, generate a cryptographically random secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy the output into Railway's `JWT_SECRET_KEY` variable. Never reuse secrets across environments. Never commit a real secret to the repo.

If `AUTH_ENABLED=true` and `JWT_SECRET_KEY` is empty, the app refuses to start with:
```
RuntimeError: AUTH_ENABLED=true but JWT_SECRET_KEY is empty
```

This is intentional. A missing secret is a deployment error, not a runtime fallback.

---

## 5. CORS Origins Config

`CORS_ORIGINS` is a comma-separated list of allowed origins. Examples:

```
# Local dev (default)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Production
CORS_ORIGINS=https://app.cultivos.io,https://cultivos.io
```

The backend rejects requests from origins not in this list. If the frontend and backend share the same Railway domain (which they do by default — the backend serves the frontend as static files), then CORS is not strictly needed, but we set it anyway for defense in depth.

---

## 6. WhatsApp Business API Setup

1. Create a Meta Developer account at developers.facebook.com and add a WhatsApp Business App.
2. In the app dashboard, go to WhatsApp > API Setup. Copy the **Phone number ID** and **temporary access token**.
3. For production: generate a permanent system user token via Meta Business Manager > System Users.
4. Set `WHATSAPP_API_TOKEN` and `WHATSAPP_PHONE_ID` in Railway variables.
5. Verify the sender phone number is approved in Meta's WhatsApp Business Account (WABA).
6. Add the destination phone numbers as test numbers in the sandbox phase, or use an approved message template for production sends.

Without these variables, alert notifications silently skip WhatsApp delivery. SMS fallback (`alerts/sms.py`) is not yet wired to a provider — set it up separately if WhatsApp is unavailable.

---

## 7. S3 Bucket Setup

cultivOS stores processed drone imagery in S3-compatible object storage. Any S3-compatible provider works (AWS S3, Cloudflare R2, Backblaze B2).

1. Create a bucket named `cultivos-imagery` (or your chosen name — set in `S3_BUCKET`).
2. Create an IAM user or API key with read/write access to that bucket only.
3. Set `S3_BUCKET`, `S3_ENDPOINT` (omit for AWS), `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` in Railway variables.
4. The upload pipeline (`src/cultivos/services/pipeline/storage.py`) uses `boto3` under the hood. The bucket must exist before the first upload — the app does not auto-create buckets.

Without S3 config, image uploads will fail at the storage step. NDVI analysis can still run on in-memory arrays passed directly.

---

## 8. Smoke-Test Checklist

Run this after every production deploy:

- [ ] `GET /health` returns `{"status": "ok"}` with HTTP 200.
- [ ] `GET /api/farms` with a valid JWT returns an empty list (or data), not a 500.
- [ ] `POST /auth/login` with test credentials returns a `{"access_token": ...}` response.
- [ ] The frontend root `GET /` serves `index.html` (check browser title "cultivOS").
- [ ] A second login with wrong credentials returns HTTP 401.
- [ ] If WhatsApp is configured: trigger a test alert via `POST /api/alerts/test` and confirm receipt on the test phone.
- [ ] Check Railway logs for any `ERROR` lines immediately after startup (DB init, seed failures).

---

## 9. Rollback Procedure

Railway keeps a deployment history. To roll back:

1. Railway dashboard > service > Deployments tab.
2. Find the last known-good deployment.
3. Click "Rollback to this deploy".
4. Railway restarts the service with the previous container image. No code changes needed.

For SQLite with a persistent volume: the database schema may be ahead of the rolled-back code if a migration ran during the failed deploy. If rollback causes schema errors, restore the SQLite file from a backup (manual step — see "Database Backups" below).

### Database Backups

We do not yet have automated backups. Until N9 (Alembic) lands, the manual procedure is:

```bash
# On your local machine, copy the DB out of the Railway container via Railway CLI:
railway run cp /app/cultivos.db ./cultivos-backup-$(date +%Y%m%d).db
```

Run this before any schema-affecting deploy. Keep the last 3 backups.

---

## Local Development

```bash
# One-time setup
cp .env.example .env
# Edit .env: set JWT_SECRET_KEY, leave AUTH_ENABLED=false for local dev

# Run
./run.sh
# Backend + frontend at http://localhost:8000
```

For local dev, set `AUTH_ENABLED=false` in `.env` to skip JWT checks. Never do this in production.

---

## Related

- `.improvement-cycle/backlog.md` — improvement queue including Alembic (N9) and RBAC (N10)
- `docs/adr/` — architecture decisions (SQLite rationale in ADR-0001)
- `.env.example` — full variable reference with defaults
