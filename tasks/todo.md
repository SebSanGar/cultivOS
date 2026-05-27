# cultivOS — Farmer-First Prototype Sprint

**Started:** 2026-05-26
**Trigger:** ITESO meeting with Dr. Gonzalez-Jimenez (next couple of days)
**Owner:** autoagent, supervised by Seb + Claude main thread

## Why this sprint

FODECIJAL focus paused. The app is architecturally complete (87 routes, 178 frontend files, 2900+ tests) but visually starved -- empty dashboards, "Cargando..." everywhere on a fresh DB, no farmer voice in the UI.

This sprint makes the prototype demo-able to a farmer (Don Manuel, 58, never opened SaaS) in 15 seconds. WhatsApp option as fallback for the tech-averse. Agronomist toggle expands the same screens with more numeric depth for Dr. Gonzalez when he wants it.

## Persona test (every screen must pass)

Don Manuel picks up Seb's phone:
1. Recognizes his fields (cards, color-coded health)
2. Taps a field, sees a photo and one Spanish sentence
3. Knows what to do next (one button, one action)
4. If lost: floating WhatsApp button always 1 tap away

## Hard rules

- No jargon in farmer view (no NDVI, ROI, KPI, threshold, anomaly, dashboard, metricas)
- One primary action per screen
- Numbers only where farmer cares (hectares, pesos, horas, dias). No decimals in farmer view.
- Mobile-first, 375px design target (iPhone SE)
- No emojis in code or UI (per cultivOS CLAUDE.md, except market flag toggle)
- Hide analytical screens from farmer nav: /intel /vuelos /efectividad /carbono /microbioma /coop-evidencia

## Tasks (mirror of autoagent backlog F1-F9)

- [x] **F1** -- Seed 3 farms x 3 fields, mixed-color health (green/yellow/red), fix orphan farms bug -- `0220e12`
- [x] **F2** -- Rewrite /campo: big photo + one sentence + one button -- `9af9068`
- [x] **F3** -- Imagen 4 fixtures (NDVI/thermal/RGB aerial), `scripts/gen_fixtures.py` -- `eeb0c67`
- [x] **F4** -- `farmer_voice.translate_to_farmer()`, 12 signal types -- `a8950dd`
- [x] **F5** -- WhatsApp FAB on /, /campo, /notificaciones, /conocimiento -- `c92df25`
- [x] **F6** -- Farmer nav 4 items + nav-agronomo-extras[hidden] -- `8759228`
- [x] **F7** -- Playwright 375x812 sweep (15 tests, pages already compliant) -- `298946a`
- [x] **F8** -- Agronomist toggle, localStorage persist, .agronomo-only reveal -- `6e01a62`
- [x] **F9** -- Railway deploy config: DATABASE_URL alias, psycopg2, healthcheck, alembic on boot -- `5652cb5`

## Sprint complete F1->F9 (18 commits, 3893 tests, 0 regressions)

## Hotfix sprint complete H1-H5 (2026-05-27)

Surfaced by manual Playwright visual sweep post-F-sprint. Tests-green != demo-ready lesson learned, council now requires Playwright visual gate per H-task.

- [x] **H1** -- F1 NDVI zone shape match NDVIZoneOut (classification/min/max/pixel_count/percentage) -- `fe8e7e0`
- [x] **H2** -- Mobile nav hamburger at 390px, no overflow -- `7d318a9`
- [x] **H3** -- Strip [DEMO] tag from farmer-view display -- `6fc04fa`
- [x] **H4** -- field.js error msg corrected ?farm/?field -- `ee96e83`
- [x] **H5** -- Graceful degradation on /mission-plan + /growth-stage -- `fb7dbc0`

## Visual verification 2026-05-27 (HX-* screenshots in /tmp/cultivos-screenshots/)
- Dashboard 390px: nav clean, no [DEMO], 3 farms wired, WhatsApp FAB present
- /campo farmer view: hero NDVI image + Spanish sentence + "Que hago?" CTA
- /campo agronomo view: 30+ data sections render w/ real seed data (no Cargando cascade)
- /notificaciones: nav clean, stats placeholders show -- (alerts table empty by design, not a bug)
- **0 HTTP errors across 4 pages**

## Stashed (NOT applied)
- `stash@{0}` — S1 auth WIP: agency started enabling auth_enabled=True by default mid-session. Demo would re-break (login wall). Decision pending Seb: keep auth disabled for demo OR ship auth + provide demo creds.

## Manual Seb action remaining

1. **Railway DNS** (~5min) — Railway dashboard -> custom domain `app.cultivosagro.com` -> copy CNAME -> Vercel DNS add CNAME `app` -> Railway target
2. **S1 auth decision** — `git stash show -p stash@{0}` to review; `git stash drop` to discard OR `git stash pop` to apply

## Deferred (post-meeting)

- API docs (`docs/API.md`)
- Saturation map for Launch Plan section on landing
- Empty page cleanups (/intel /vuelos /efectividad) -- currently hidden from nav, leave alone

## How to fire

Autoagent picks tasks from `~/Documents/autoagent/memory/backlog.md`. Sprint F1-F9 is pinned at top.

```bash
# Seb runs from a fresh terminal (NOT from Claude Code main thread -- writepath hook bug):
cd ~/Documents/autoagent
py -X utf8 launcher.py --once          # single session, picks F1
py -X utf8 launcher.py --tasks 9       # full sprint, 9 sessions
py -X utf8 launcher.py --status        # check spend after
```

Council-on-pivot mode recommended for F2 and F4 (voice-sensitive). F8 + F9 council-mandatory (architectural).

## Pre-flight notes

- `web/app/i18n/messages.ts` and `web/app/page.tsx` have uncommitted edits from prior landing copy work (Victor removal). Safe to leave for this app-only sprint, OR stash + branch.
- `cultivos.db` ships with 2 orphan farms (no demo tag, not in seed_demo cleanup path). F1 fixes the orphan bug as a side effect.
- Gemini key already set in autoagent .env (`GEMINI_API_KEY=<set>`).
- Railway: `railway.toml` is a stub (Dockerfile builder only). F9 expands it. Project itself may need fresh `railway init`.

## Review (filled in post-sprint)

_pending_
