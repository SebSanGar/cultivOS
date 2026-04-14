# cultivOS Improvement Cycle — Overnight Backlog

**Worktree**: `~/Documents/cultivOS-night` (branch: `improvement-cycle`)
**Main worktree (day, grant sprint)**: `~/Documents/cultivOS` (branch: `main`)
**Rule**: Overnight trigger picks the first `[ ]` item, executes it end-to-end in the worktree, commits on `improvement-cycle`, appends a result line to `docs/snapshots/overnight-log.md`, then exits. One item per night, no scope creep.

**Conflict avoidance**: Only items marked `GRANT-SAFE` may run while FODECIJAL sprint is live (deadline 2026-05-14). After May 14, `POST-GRANT` items unlock.

---

## Queue (while grant sprint is live, GRANT-SAFE only)

- [ ] **N0 · Phase 0 baseline snapshot** `GRANT-SAFE`
  - Create `docs/snapshots/2026-04-13-before/` with:
    - `metrics.json` — LOC (backend per-subpackage + frontend html/js/css totals), test count (`pytest --collect-only -q`), pytest baseline (pass/fail/skipped/wall-time), route count (`grep -r "@router\." src/`), Pydantic model count, hardcoded Spanish string count (sample grep `Granja|Campo|Salud|Riego|Cargando`), ARIA attribute count in frontend/, `font-size` values <0.8rem count, orphan HTML page count, alembic-present bool, ci-present bool, `auth_enabled` default
    - `audit.md` — copy the Explore subagent audit from `~/.claude/projects/-Users-SebSan/work-log/2026-04-13.md` cultivOS section
    - Screenshots pass: if a dev server can be started headlessly, Playwright-capture `{page}-{viewport}.png` for pages (login, index, farm-detail, field, notifications, knowledge) × viewports (1440×900, 768×1024, 390×844, 320×568). If dev server is not reachable, document that and skip — don't block the snapshot.
    - Lighthouse pass: if Playwright + Lighthouse work, run against login/index/field/notifications in desktop + mobile form factors. Otherwise skip.
  - Tag: `git tag baseline-2026-04-13 -m "cultivOS pre-improvement-cycle baseline"`
  - Commit: `snapshot: cultivOS pre-improvement baseline (N0)`
  - Touches ZERO source code. Pure read + new files under docs/.

- [ ] **N1 · GitHub Actions CI (test + build)** `GRANT-SAFE`
  - Create `.github/workflows/test.yml` — Python 3.12, cache pip, run `pytest tests/`, trigger on push + PR to main and improvement-cycle
  - Create `.github/workflows/build.yml` — Docker build on tag push, uses existing `Dockerfile`
  - No source file touches. `.github/` is greenfield.
  - Commit: `ci: add test + build workflows (N1)`

- [ ] **N2 · Auth gating hardening** `GRANT-SAFE`
  - `src/cultivos/config.py:18` — flip `auth_enabled: bool = True` default
  - `src/cultivos/app.py` startup — if `auth_enabled` and `jwt_secret_key == ""`, raise on boot with clear message
  - Grep every file in `src/cultivos/api/` for routers missing `Depends(require_role(...))` or equivalent auth; add where gaps found
  - Update `.env.example`: add `AUTH_ENABLED=true` + JWT secret generation command (`python -c "import secrets; print(secrets.token_urlsafe(64))"`)
  - Run full pytest — must stay green (tests may use test mode that bypasses auth; preserve that)
  - Commit: `sec: enforce auth enabled + JWT secret on boot (N2)`

- [ ] **N3 · Deployment runbook** `GRANT-SAFE`
  - Create `docs/DEPLOYMENT.md` covering: Railway deploy flow, env var checklist, DB init (current: create_all at startup; Alembic TBD), WhatsApp Business API token procurement, S3 bucket setup, JWT secret generation, CORS origins config, smoke-test checklist, rollback procedure
  - Frame as agency standard ("this is how we deploy"), not citing external "best practices"
  - Commit: `docs: add deployment runbook (N3)`

- [ ] **N4 · Seed ADRs** `GRANT-SAFE`
  - Create `docs/adr/0001-sqlite-for-mvp.md`, `0002-vanilla-js-no-bundler.md`, `0003-routes-to-services-one-way.md`
  - Each one concise: Context / Decision / Consequences / Alternatives-rejected
  - Assert as agency conventions, not "chosen because X blog recommended"
  - Commit: `docs: seed architecture decision records (N4)`

## Queue (unlocks after 2026-05-14 grant ship)

- [ ] **N5 · Phase 1 UX — badge contrast** `POST-GRANT` — `styles.css` `.health-badge.{good,warning,critical}` — dark text on saturated bg, WCAG AA
- [ ] **N6 · Phase 1 UX — text size minimums** `POST-GRANT` — raise all `font-size < 0.75rem` to 0.75rem min; labels 0.8rem
- [ ] **N7 · Phase 1 UX — touch target sizing** `POST-GRANT` — buttons `min-height: 44px`, inputs 40px
- [ ] **N8 · Phase 1 UX — keyboard focus indicators** `POST-GRANT` — `:focus-visible` global rule in styles.css
- [ ] **N9 · Phase 2 — Alembic migrations** `POST-GRANT` — opus advisor review before ship
- [ ] **N10 · Phase 2 — field-level RBAC** `POST-GRANT` — opus advisor review before ship
- [ ] **N11 · Phase 2 — semantic link refactor** `POST-GRANT` — `<div onclick>` → `<a href>` in app.js, field.js
- [ ] **N12 · Phase 2 — error recovery + toast helper** `POST-GRANT` — fetchJSON retry + user-visible failure toast
- [ ] **N13 · Phase 3 — design tokens extraction** `POST-GRANT` — opus advisor review; zero visual diff required
- [ ] **N14 · Phase 3 — ARIA pass** `POST-GRANT`
- [ ] **N15 · Phase 3 — i18n skeleton + market toggle** `POST-GRANT`
- [ ] **N16 · Phase 3 — orphan page cleanup** `POST-GRANT`
- [ ] **N17 · Phase 3 — Playwright smoke tests** `POST-GRANT`
- [ ] **N18 · Phase 3 — OpenTelemetry instrumentation** `POST-GRANT`
- [ ] **N19 · Phase 3 — Vite bundler decision** `POST-GRANT` — opus advisor; stretch
- [ ] **N20 · Phase 4 — closing snapshot `uplifted-YYYY-MM-DD`** `POST-GRANT`
- [ ] **N21 · Phase 4 — DELTA.md diff report** `POST-GRANT`
- [ ] **N22 · Phase 4 — promote improvement-cycle pattern to `~/.autoagent/patterns/improvement-cycle.md`** `POST-GRANT`

---

## Trigger instructions (for the scheduled overnight agent)

1. `cd ~/Documents/cultivOS-night`
2. `git pull origin improvement-cycle` if remote exists (safe no-op if not)
3. Read this file (`~/.autoagent/improvement-cycle-backlog.md`); pick first `[ ]` item. Today's date in Toronto time — if before 2026-05-15, only consider `GRANT-SAFE` items. Otherwise any item.
4. Execute the item's instructions end-to-end in the worktree.
5. Run `pytest tests/` — must be green before commit.
6. Commit on `improvement-cycle` branch using the commit message from the item spec.
7. Append a single line to `docs/snapshots/overnight-log.md`: `YYYY-MM-DD HH:MM — <item id> — <status> — <commit hash or error>`
8. Mark item as `[x]` in this backlog file.
9. **Exit.** One item per night. Do not pick a second item, do not refactor adjacent code, do not run another phase.
10. If pytest is red on arrival (before you change anything), log `BLOCKED: tests red on arrival` and exit without touching code.
11. If the item instructions are ambiguous, log `BLOCKED: needs human review` with the ambiguity, exit without committing.

## Safety clamps

- Max 1 commit per overnight session.
- Never push to `origin/main`. Only `origin/improvement-cycle` allowed, and only if the item explicitly calls for a push.
- Never delete files unless the item explicitly says delete.
- Never touch files outside the worktree at `~/Documents/cultivOS-night`.
- Never start the dev server on port 8000 unless the item requires it (port 8000 may be in use by day work).
- Never run `autoagent run cultivOS` — that's the day sprint project. Overnight stays in the worktree via direct git/pytest/filesystem ops.
