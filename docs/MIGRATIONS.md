# Database Migrations (alembic)

Baseline: `alembic/versions/0a265488d88f_baseline_schema_from_sqlalchemy_models.py` (2026-04-16).

## Daily ops

**Apply migrations**:
```bash
alembic upgrade head
```

**Add a new migration** (after editing SQLAlchemy models):
```bash
alembic revision --autogenerate -m "short description"
# review the generated file in alembic/versions/ — autogenerate has blind
# spots (server defaults, check constraints, column renames). Hand-check
# before committing.
alembic upgrade head
```

**Roll back the most recent migration**:
```bash
alembic downgrade -1
```

**See migration history**:
```bash
alembic history --verbose
alembic current        # which rev is the DB at
```

---

## One-time production switch (Railway)

The app currently calls `Base.metadata.create_all` on startup (see
`src/cultivos/app.py:_lifespan`). This is a fragile pattern — it only adds
new tables/columns, never alters or removes, and has no version record.

Switching to alembic requires one coordinated operation:

### Step 1 — Stamp prod at the baseline

The live Railway DB already has the schema that baseline revision
`0a265488d88f` describes (every table + index in `db/models.py` as of
2026-04-16). Tell alembic "you're already there" without running SQL:

```bash
# SSH into Railway (or run via the CLI)
railway run --service cultivos alembic stamp head
```

Verify:
```bash
railway run --service cultivos alembic current
# expected: 0a265488d88f (head)
```

Stamping writes a single `alembic_version` row into the DB. No schema
change. Safe to run on live traffic.

### Step 2 — Retire `create_all` from app startup

In a follow-up commit edit `src/cultivos/app.py`:

```python
# BEFORE
from cultivos.db.session import get_engine, get_session_factory
get_engine()  # creates tables
logger.info("Database initialized")

# AFTER — rely on alembic
from cultivos.db.session import get_session_factory
logger.info("Database schema managed by alembic (run `alembic upgrade head` before deploy)")
```

### Step 3 — Run migrations on every deploy

Add to the Dockerfile CMD or a Railway pre-deploy hook:

```bash
alembic upgrade head && uvicorn cultivos.app:create_app --factory --host 0.0.0.0 --port $PORT
```

Or a Railway *release command* (preferred — runs once per deploy, before
the web process starts):

```
alembic upgrade head
```

### Rollback plan

If step 1 or 2 goes wrong and the schema/version desync:

```bash
railway run --service cultivos alembic stamp 0a265488d88f
# OR drop the alembic_version table to revert to "not tracked"
railway run --service cultivos psql -c "DROP TABLE alembic_version;"
```

The app will fall back to `create_all` until stamped again. No data loss.

---

## Baseline drift detection

To confirm the live schema still matches baseline `0a265488d88f` (e.g. if
someone added a column manually during an incident):

```bash
# Point alembic at prod DB, ask for the diff without writing a file
DB_URL=$(railway variables get DB_URL) \
  alembic revision --autogenerate -m "drift check" --sql > /tmp/drift.sql
# Empty SQL = no drift. Any CREATE/ALTER/DROP = someone changed prod
# outside of migrations — investigate before next deploy.
rm /tmp/drift.sql
```
