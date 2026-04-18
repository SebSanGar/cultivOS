# ADR 0001 — SQLite for the MVP database

## Context

cultivOS needs a persistent relational store for farms, fields, flight logs, NDVI results,
health scores, and alert rules. At MVP stage we are deploying to a single Railway instance,
operating in one geographic market (Jalisco), and the active farm count is in the tens.
Network latency, concurrent write volume, and cross-region replication are non-problems right now.
Operational burden is a real problem — every external service we add is one more thing that can
fail during a demo, a grant review, or an early farm onboarding.

## Decision

We use SQLite as the sole database for the MVP. The file lives at the path set by `DB_URL`
(default: `sqlite:///cultivos.db`). SQLAlchemy is the ORM. All schema changes go through
`Base.metadata.create_all` at startup until Alembic migrations land (N9 in the backlog).

## Consequences

Deploying and backing up the database is a `cp` command. There is no separate database
service to provision, secure, or pay for. The test suite creates an in-memory SQLite instance
(`sqlite:///:memory:`) for each test run — no external state, no cleanup step.

The trade-off is that SQLite does not support concurrent writes from multiple processes.
If we ever run multiple uvicorn workers or move to a multi-region setup, we will migrate
to Postgres. That migration is planned for Year 2 when the farm count justifies it.
SQLAlchemy's ORM layer means the migration will be a one-line `DB_URL` change plus a
schema apply — no application-level rewrites required.

## Alternatives considered

**Postgres on Railway** — adds $10-25/month, a connection string secret, and a cold-start
dependency. Not worth it at 15 farms. We revisit at 50.

**MongoDB** — document model is a poor fit for the relational farm → field → flight → result
hierarchy. Schema flexibility is not a benefit here; it is a liability that hides data bugs.
