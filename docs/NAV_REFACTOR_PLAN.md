# Nav refactor — shared nav component (planned 2026-06-15, execute next session)

## Problem (root cause, diagnosed)
No shared nav. Each of ~80 `frontend/*.html` hand-rolls its own `<nav>`, so they
have **10+ different tab sets** that drift. Navigating between pages visibly
changes the bar (Seb's report: clicking Chat → "My Crops·Intelligence·Chat·Summary·Status";
Intelligence → "My Crops·Intelligence·Flights·Notifications·Knowledge·Status"; etc.).
Also `toggle.js` (agronomist view + hamburger) is included on only **4/87 pages**,
so the Agronomist toggle is dead almost everywhere.

## Decision (founder)
- **Canonical = the dashboard (index.html) nav, applied everywhere.**
- Farmer pages keep their minimal nav (do NOT touch): `field.html`, `impacto-agricultor.html`.

## Canonical nav (from index.html)
Always-visible farmer tabs: **My Crops** `/` · **Alerts** `/notificaciones` ·
**Knowledge** `/conocimiento` · **Chat** `/whatsapp-demo`.
Agronomist extras (revealed by toggle, `.nav-agronomo-extras[hidden]`): **Intelligence**
`/intel` · **Map** `/mapa` · **Flights** `/vuelos` · **Platform** `/plataforma` ·
**Status** `/estado`. Plus `#agronomo-toggle`, `.nav-lang-toggle` (ES/EN), `#nav-user-info`.
i18n keys already exist: `nav.farms/alerts/knowledge/whatsapp/intel/map/flights/platform/status`,
`toggle.agronomo/farmer`, `user.logout`.

## Approach — self-contained `frontend/nav.js`
1. Renders the canonical nav markup (replace existing `<nav>`, or insert as first
   body child on the ~10 nav-less pages). Sets `.active` on the link matching
   `location.pathname`.
2. Owns the agronomist toggle (fold in `toggle.js`): `localStorage 'cultivos_view_mode'`
   ('farmer' default / 'agronomist'); reveal `.nav-agronomo-extras` + `.agronomo-only`;
   update `#agronomo-toggle` label; + hamburger (`#nav-hamburger` → `.nav-inner.nav-open`).
3. Labels/lang: `i18n.js` (on 87 pages) handles them. nav.js must render BEFORE
   i18n's DOMContentLoaded (include `<script src="/nav.js">` BEFORE i18n.js, render
   synchronously), OR call `window.cultivOS_i18n.applyAll()` after render.
   API: `window.cultivOS_i18n = {t, localized, cropName, switchLang, getLang, applyAll}`.
4. Delete `toggle.js` (superseded) — update its 4 includes + any test referencing it.

## Rollout
- Add `<script src="/nav.js"></script>` (before i18n.js) to every app page EXCEPT:
  `login.html`, `demo.html`, `walkthrough.html` (auth/public), and the 2 farmer pages.
- Guard test (`tests/test_nav_shared.py`): assert every app page includes nav.js; re-crawl
  asserts identical canonical tab set + working toggle across pages. Keep
  `test_nav_title_consistency.py`.

## Verify (required)
Re-crawl ALL nav pages logged in (token via POST /api/auth/login, seb/cultivos2026):
every page shows the identical canonical nav, active state correct, agronomist toggle
reveals extras, lang toggle works. Then `./scripts/verify.sh` (full gate).

## Risk
High blast radius (site-wide nav). A nav.js bug breaks navigation everywhere — verify
exhaustively before commit. Build nav.js + test on 2-3 pages first, then roll out.
