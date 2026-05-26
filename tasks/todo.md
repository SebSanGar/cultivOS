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

- [x] **F1** -- Seed 3 farms x 3 fields, mixed-color health (green/yellow/red), fix orphan farms bug
- [x] **F2** -- Rewrite /campo: big photo + one sentence + one button
- [ ] **F3** -- Generate 4 NDVI/thermal/RGB fixtures via Gemini (GEMINI_API_KEY from autoagent .env)
- [ ] **F4** -- Plain-Spanish alert generator (`services/intelligence/farmer_voice.py`), 12 alert types
- [ ] **F5** -- Floating WhatsApp button on every farmer page (in-tab, not external)
- [ ] **F6** -- Hide analytics from farmer nav (4 items: Parcelas / Alertas / Conocimiento / WhatsApp)
- [ ] **F7** -- Mobile sweep, all farmer pages 375px clean
- [ ] **F8** -- Agronomist toggle (localStorage-persisted, inline data expansion)
- [ ] **F9** -- Railway deploy at app.cultivosagro.com, Postgres add-on, alembic migration

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
