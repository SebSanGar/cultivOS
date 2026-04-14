# cultivOS at baseline on 2026-04-13

This is the agency's first pre-improvement audit. We captured it before any overnight improvement cycle ran. Every number here is machine-verified against the live `improvement-cycle` branch.

---

## Repo shape

The backend spans **30,956 lines** of Python across five subpackages. Services dominate at 16,150 LOC — the intelligence layer for NDVI processing, drone mission planning, alert delivery, and agronomic recommendations. The API layer is 8,644 LOC (218 router endpoints), models are 3,421 LOC (321 Pydantic `BaseModel` subclasses), and the database layer is 1,897 LOC. The utils package is minimal at 65 LOC.

The frontend is substantial: 9,694 lines of HTML across multiple pages, 15,605 lines of JavaScript, and 3,897 lines of CSS. There are **7 orphan HTML pages** with no matching JS file (demo, fusion, index, intelligence, reporte-fodecijal, tek, walkthrough) — these are candidates for pruning or promotion in a later phase.

---

## Backend health

The test suite has **3,449 tests**, all passing (0 failures, 0 skips) in 973 seconds on a cold run. That is a strong foundation. 321 Pydantic models cover the domain surface thoroughly. 218 routes are registered.

The SQLAlchemy layer uses the 1.x Query API in several tests (`db.query().get()`), which generates deprecation warnings under SQLAlchemy 2.x. These are warnings, not failures. No Alembic is present — the app relies on `create_all` at startup. This is appropriate for the MVP stage and is formally recorded in ADR-0001 (TBD).

**Auth is off by default.** `src/cultivos/config.py` sets `auth_enabled = False`. This is a deliberate development-mode default, not a production posture — but it is a red flag that needs hardening before any external deployment. N2 in the backlog addresses this directly.

---

## Frontend health

**Zero ARIA attributes** across the entire frontend. This is the most significant accessibility gap at baseline. The WCAG surface is entirely unaddressed. Post-grant items N5–N8 and N14 form the planned accessibility uplift.

**17 CSS rules use font sizes below 0.75rem**, which falls below our minimum legibility standard for field use on phones. This will be resolved in N6.

The frontend is vanilla JavaScript with no bundler. This is an intentional architectural choice (ADR-0002, TBD) — it keeps the dev loop simple and dependencies near-zero. The trade-off is no tree-shaking and no hot module reload, which is acceptable at current scale.

**371 hardcoded Spanish strings** were found in the frontend by the grep probe (`Granja`, `Campo`, `Salud`, `Riego`, `Cargando`). This is expected — the product is Spanish-first. An i18n skeleton (N15) will formalize this rather than eliminate it.

---

## Ops and CI

**No CI pipeline exists.** There are no `.github/workflows/` files. Every merge to `main` currently ships with no automated gate. N1 (next in the backlog) creates the test and build workflows. This is the most operationally urgent gap after auth.

No Docker deployment manifests or Railway config were found in the branch. The deployment process is not yet codified. N3 writes the runbook.

---

## Security red flags

Two items require action before any production deployment:

1. `auth_enabled = False` is the default. Any deployment that forgets to set `AUTH_ENABLED=true` ships with open endpoints.
2. No CI means no automated regression check on security-relevant changes.

Both are in the backlog and gated `GRANT-SAFE`. The code itself shows no obvious injection vectors at first read, but a full route-by-route auth audit is part of N2.

---

*Snapshot captured by cultivOS overnight agent on 2026-04-14. Baseline date is 2026-04-13 (the last commit to `improvement-cycle` before the first improvement cycle run).*
