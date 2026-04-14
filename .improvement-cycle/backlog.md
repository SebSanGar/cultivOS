# cultivOS Improvement Cycle — Overnight Backlog

**Branch**: `improvement-cycle` (this file is version-controlled; remote overnight agent reads and mutates it each run)
**Day branch**: `main` (FODECIJAL grant sprint; the overnight agent never touches main)
**Rule**: Overnight trigger picks the first `[ ]` item in the Queue, executes it end-to-end from the repo root, runs pytest, commits on `improvement-cycle`, appends a status line to `docs/snapshots/overnight-log.md`, marks the item `[x]`, pushes, then exits. One item per night, no scope creep.

**Grant safety gate**: While the FODECIJAL grant sprint is live (deadline **2026-05-14**), only items tagged `GRANT-SAFE` may run. `POST-GRANT` items unlock on **2026-05-15**. The agent checks the current Toronto date at the start of every session and respects the gate.

**Why this exists**: cultivOS is the agency's first project to go through a full audit → improvement → case-study cycle. The output of this backlog — the snapshot format, the delegation cadence, the DELTA.md artifact — becomes the agency's template for every future project. This isn't cleanup; it's building the pattern.

All paths below are **relative to the repo root** (the checkout the remote sandbox clones). Never absolute, never referencing any local filesystem outside the clone.

---

## Queue

### GRANT-SAFE (runnable now through 2026-05-14)

- [x] **N0 · Phase 0 — baseline snapshot**  `GRANT-SAFE`
  - Create `docs/snapshots/2026-04-13-before/` with:
    - `metrics.json` — machine-captured scalar metrics. Keys snake_case. Collect:
      - `backend_loc_total` — `wc -l $(find src/cultivos -name "*.py") | tail -1`
      - `backend_loc_by_subpackage` — object keyed by subpackage name (api, services, models, db, utils) with LOC each
      - `frontend_loc` — object with `html`, `js`, `css` totals under `frontend/`
      - `test_count` — `pytest --collect-only -q tests/ 2>/dev/null | tail -5 | grep -oE '[0-9]+ tests?' | head -1`
      - `pytest_baseline` — object `{passed, failed, skipped, wall_seconds}` from a fresh `pytest tests/` run
      - `route_count` — `grep -r "@router\." src/cultivos/ | wc -l`
      - `pydantic_model_count` — count of `class \w+\(BaseModel\)` matches under `src/cultivos/models/`
      - `hardcoded_spanish_sample` — `grep -rE "Granja|Campo|Salud|Riego|Cargando" frontend/ | wc -l`
      - `aria_attribute_count` — `grep -rE "aria-[a-z]+=" frontend/ | wc -l` (expected: 0)
      - `font_size_under_075rem_count` — count `font-size:\s*0\.[0-6][0-9]*rem` in `frontend/styles.css`
      - `orphan_html_count` — html files in `frontend/` with no same-basename js file
      - `alembic_present` — bool (directory `src/cultivos/db/alembic/` or `alembic/` exists)
      - `ci_present` — bool (`.github/workflows/` has any .yml file)
      - `auth_enabled_default` — bool from parsing `src/cultivos/config.py`
    - `audit.md` — fresh ~400-word narrative covering: repo shape, backend health, frontend health, tests, ops, security red flags. Write in first-person agency voice: "cultivOS at baseline on 2026-04-13." Do not cite external blogs or best-practice docs.
    - `README.md` — one-paragraph cover page explaining this is the pre-improvement snapshot for the agency's first full improvement cycle. Link back to `.improvement-cycle/backlog.md`.
  - Do **not** attempt screenshots or Lighthouse in this session. The remote sandbox likely has no browser. If Playwright + Chromium happen to be available, you may add `screenshots/` and `lighthouse/` subdirs; if not, add a line to `README.md` saying "visual capture deferred to local run" and skip without failing.
  - Zero source code changes. Only new files under `docs/snapshots/2026-04-13-before/`.
  - Commit message: `snapshot: cultivOS pre-improvement baseline (N0)`
  - Do not create a git tag — tagging is a separate human-reviewed step.

- [ ] **N1 · GitHub Actions CI — test + build**  `GRANT-SAFE`
  - Create `.github/workflows/test.yml`: Python 3.12, cache pip, install `requirements.txt`, run `pytest tests/`. Triggers on push to `main` and `improvement-cycle`, and on PRs targeting `main`.
  - Create `.github/workflows/build.yml`: Docker build using the existing `Dockerfile`. Triggers on tag push matching `v*`. Pushes to GitHub Container Registry (`ghcr.io/sebsangar/cultivos`).
  - Zero source file touches. `.github/` is greenfield.
  - Run `pytest tests/` as a sanity check before committing.
  - Commit message: `ci: add test + build workflows (N1)`

- [ ] **N2 · Auth gating hardening**  `GRANT-SAFE`
  - `src/cultivos/config.py:18` — flip `auth_enabled: bool = False` → `auth_enabled: bool = True`.
  - `src/cultivos/app.py` startup — add a boot check: if `settings.auth_enabled` and `settings.jwt_secret_key == ""`, raise `RuntimeError("AUTH_ENABLED=true but JWT_SECRET_KEY is empty")`.
  - Grep `src/cultivos/api/` for every router file. For any endpoint missing `Depends(require_role(...))` or equivalent auth (exclude `/auth/login`, `/auth/register`, `/health` as intentional exceptions), add the guard. Document additions in the commit body.
  - Update `.env.example`: add `AUTH_ENABLED=true` and the JWT secret generation one-liner: `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
  - Run pytest. If tests fail because they depend on `auth_enabled=False`, prefer a test-mode env override (e.g., `AUTH_ENABLED=false` in test config) over reverting the default.
  - Commit message: `sec: enforce auth_enabled default + JWT secret on boot (N2)`

- [ ] **N3 · Deployment runbook**  `GRANT-SAFE`
  - Create `docs/DEPLOYMENT.md` covering: Railway deploy flow, env var checklist, DB init (current: `create_all` at startup; Alembic TBD), WhatsApp Business API token procurement, S3 bucket setup, JWT secret generation, CORS origins config, smoke-test checklist, rollback procedure.
  - Agency voice: write as "this is how we deploy cultivOS" — first-person, authoritative. No external "best practice" citations. Our way is the standard.
  - Commit message: `docs: add deployment runbook (N3)`

- [ ] **N4 · Seed architecture decision records**  `GRANT-SAFE`
  - Create `docs/adr/0001-sqlite-for-mvp.md`, `docs/adr/0002-vanilla-js-no-bundler.md`, `docs/adr/0003-routes-services-one-way.md`.
  - Each ~150 words, structure: Context / Decision / Consequences / Alternatives considered (and why rejected).
  - Assert as agency standards. Frame as "we do it this way because it works for us," not "chosen per industry convention X."
  - Commit message: `docs: seed architecture decision records (N4)`

### POST-GRANT (unlocks 2026-05-15)

- [ ] **N5 · Phase 1 UX — badge contrast**  `POST-GRANT` — `frontend/styles.css` `.health-badge.{good,warning,critical}`: dark text on saturated bg, WCAG AA verified
- [ ] **N6 · Phase 1 UX — text size minimums**  `POST-GRANT` — raise all `font-size < 0.75rem` to 0.75rem; labels to 0.8rem
- [ ] **N7 · Phase 1 UX — touch target sizing**  `POST-GRANT` — buttons `min-height: 44px`, inputs `40px`
- [ ] **N8 · Phase 1 UX — keyboard focus indicators**  `POST-GRANT` — `:focus-visible` global rule in `frontend/styles.css`
- [ ] **N9 · Phase 2 — Alembic migrations**  `POST-GRANT` — needs advisor/human review before ship
- [ ] **N10 · Phase 2 — field-level RBAC**  `POST-GRANT` — needs advisor/human review before ship
- [ ] **N11 · Phase 2 — semantic link refactor**  `POST-GRANT` — `<div onclick>` → `<a href>` in `frontend/app.js`, `frontend/field.js`
- [ ] **N12 · Phase 2 — error recovery + toast helper**  `POST-GRANT` — `fetchJSON` retry + user-visible failure toast
- [ ] **N13 · Phase 3 — design tokens extraction**  `POST-GRANT` — advisor review; zero visual diff required
- [ ] **N14 · Phase 3 — ARIA pass**  `POST-GRANT`
- [ ] **N15 · Phase 3 — i18n skeleton + market toggle**  `POST-GRANT`
- [ ] **N16 · Phase 3 — orphan page cleanup**  `POST-GRANT` — true orphan detection: a page is only orphan if (a) no other HTML file links to it via `href=` and (b) it loads no script that exists in `frontend/`. Basename-matching alone is wrong — `index.html` pairs with `app.js`, not `index.js`. Scan scripts and links before deleting. Verify via `grep -rE 'href=.*{name}|src=.*{name}' frontend/` for each candidate.
- [ ] **N17 · Phase 3 — Playwright smoke tests**  `POST-GRANT`
- [ ] **N18 · Phase 3 — OpenTelemetry instrumentation**  `POST-GRANT` — optional env-gated
- [ ] **N19 · Phase 3 — Vite bundler decision**  `POST-GRANT` — advisor review; stretch, may be declined
- [ ] **N20 · Phase 4 — closing snapshot `docs/snapshots/uplifted-YYYY-MM-DD/`**  `POST-GRANT`
- [ ] **N21 · Phase 4 — DELTA.md diff report**  `POST-GRANT`
- [ ] **N22 · Phase 4 — promote improvement-cycle pattern to `.improvement-cycle/PATTERN.md`**  `POST-GRANT`
- [ ] **N23 · Phase 3 — shared nav component (structural fix)**  `POST-GRANT`
  - Problem: 69 HTML files in `frontend/` each hardcode their own `<ul class="nav-tabs">`. The sets diverge (5-7 tabs each, different items, different order). A surgical fix on 2026-04-14 (`734752f` on main) added 7 tabs to `index.html` to unblock grant reviewers, but the chronic divergence remains.
  - Goal: one source of truth for the nav. Every page renders the same 7-9 main tabs with the correct `active` state set automatically.
  - Approach: small JS module `frontend/nav.js` exporting `renderNav(activeId)` which writes the `<ul class="nav-tabs">` innerHTML into a `<nav id="main-nav">` shell. Each page replaces its hardcoded nav with `<nav id="main-nav"></nav>` + `<script src="/nav.js"></script>` + an inline call like `renderNav('granjas')`. Single canonical tab list lives in `nav.js`.
  - Don't try to render the nav server-side. This is vanilla-JS no-bundler by design (ADR-0002). Keep it simple.
  - Test coverage: Playwright smoke (N17) should assert every main page renders the same top-level nav item count and includes the "Inteligencia" link.
  - Commit message: `refactor: shared nav component across all frontend pages (N23)`

---

## Session protocol

Each overnight session must follow this protocol exactly. Step order matters — the log and checkbox flip must be staged BEFORE the commit, not after, so everything lands in a single atomic commit and there is no commit-hash-prediction problem.

1. **Gate check** — read current Toronto date (`TZ=America/Toronto date +%Y-%m-%d`). Before 2026-05-15 → skip all `POST-GRANT` items. On/after → all items eligible.
2. **Tests on arrival** — `pytest tests/`. If red before any changes, follow the BLOCKED flow below and exit without touching code.
3. **Pick one** — first `[ ]` item matching the gate. If none, follow the IDLE flow below and exit cleanly.
4. **Execute** — follow the item's instructions verbatim. Do not combine items, refactor adjacent code, or add "nice-to-haves."
5. **Tests again** — `pytest tests/` must pass. If you cannot get it green without deviating from the item spec, follow the BLOCKED flow.
6. **Status log** — append a single line to `docs/snapshots/overnight-log.md` (create if missing). Format: `YYYY-MM-DD HH:MM Toronto — <item id> — DONE — <short summary of what shipped>`. **Do NOT include a commit short-hash** — you do not know it yet, and the git log is the authoritative trail. Readers can resolve item→commit via `git log --grep="(N<item>)"`.
7. **Mark done** — flip the item's checkbox from `[ ]` to `[x]` in this file.
8. **Stage everything** — `git add` the item's changes + `.improvement-cycle/backlog.md` + `docs/snapshots/overnight-log.md`. Verify with `git status` that nothing else is staged.
9. **One commit** — use the exact commit message from the item spec. Single commit. No amends.
10. **Push** — `git push origin improvement-cycle`. Never push to main. Never force-push.
11. **Exit** — one item per session. Do not pick a second.

### BLOCKED flow (tests red on arrival, test regression, ambiguous spec, or any unsafe condition)

1. Do NOT revert or clean up any partial work — let `git status` show what you touched.
2. If you have local changes, `git stash` them (do not commit them).
3. Append a single line to `docs/snapshots/overnight-log.md`: `YYYY-MM-DD HH:MM Toronto — <item id> — BLOCKED — <specific reason>`.
4. Stage only `docs/snapshots/overnight-log.md` and commit with message `overnight: log BLOCKED for <item id>`.
5. Push and exit. Do not mark the item `[x]` — it remains `[ ]` for the next session or human review.

### IDLE flow (no eligible item found)

1. Append a single line to `docs/snapshots/overnight-log.md`: `YYYY-MM-DD HH:MM Toronto — — IDLE — <reason e.g. "grant-safe queue empty, waiting for 2026-05-15">`.
2. Stage only `docs/snapshots/overnight-log.md` and commit with message `overnight: log IDLE — <short reason>`.
3. Push and exit. No item is touched.

## Safety clamps

- Max **one commit** per session.
- Never push to `main`. Never force-push any branch.
- Never delete files unless the item explicitly says "delete."
- Never touch files outside the repo working tree.
- Never run destructive git commands (`reset --hard`, `checkout .`, `clean -fd`) unless the item explicitly says to.
- If a pre-commit hook fails, fix the underlying issue and create a NEW commit. Do not `--no-verify`.
- If the item is ambiguous, log `BLOCKED: needs human review — <reason>` and exit without committing.
- If a test regression cannot be resolved in-session, log `BLOCKED: test regression — <short summary>` and exit without committing.
- If you find yourself about to do something that isn't in the item spec, stop and log a BLOCKED entry instead.
