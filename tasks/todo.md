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

## Manual Seb action remaining (DNS, ~5min)

1. Railway -> cultivOS service -> Settings -> Custom Domain -> add `app.cultivosagro.com`
2. Copy Railway CNAME target shown
3. Vercel DNS (cultivosagro.com) -> add CNAME `app` -> Railway target
4. Wait for cert provision (~2min), verify https://app.cultivosagro.com loads dashboard

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
