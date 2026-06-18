# cultivOS — Frontend Rebuild Spec (Claude-Design-native)

**Decided 2026-06-18.** Greenfield, component-based frontend for cultivOS, built
by the agency through the Claude Design workflow (`autoagent/skills/claude-design.md`).
Proves the agency Claude Design loop on a real app and produces a wow-grade,
pitch-ready UI. Model: the RedHunter landing/console rebuild that wowed pros —
same agency, same loop, now against a mapped API.

## Non-goals (hard)
- **No backend changes.** The FastAPI intelligence layer (NDVI/thermal/health/
  economics, 5679 tests, bilingual data, farm-scoped auth) is the moat and is
  verified. Rebuild the *frontend* only; hit the existing API.
- **No full rewrite, no big-bang cutover.** If it wins, migrate incrementally
  (strangler — new frontend replaces old page-by-page, same backend).
- **No fake A/B.** ~6 pilot farms can't reach statistical significance. Judge by
  qualitative head-to-head (Seb + 1-2 pilot farmers) + pitch reception.

## Stack
- **Next.js (App Router) + TypeScript** — component layer, Claude-Design-native.
- **Tailwind CSS + shadcn/ui** — primitives (agency `web-artifacts.md`).
- **Framer Motion** — stateful animation (agency `ui-stack.md`).
- **Bilingual ES/EN** — reuse backend `_en` data convention + a client i18n layer.
- Location: `cultivOS/web/` (in-repo, versioned with backend; deploy as a
  separate Railway service). Backend untouched at `src/`, legacy frontend stays
  at `frontend/` until the strangler migration retires pages.

## Integration contract (verified against live code 2026-06-18)
- **Auth:** `POST /api/auth/login` → `{access_token, token_type, user}`. Store in
  `localStorage.cultivOS_token`. All API calls send `Authorization: Bearer <token>`.
  Dev bypass: `AUTH_ENABLED=false`.
- **CORS:** `CORSMiddleware` allows `CORS_ORIGINS` (default includes
  `http://localhost:3000`) — Next dev origin works out of the box. Add the
  deployed origin to `CORS_ORIGINS` for prod.
- **i18n:** DATA fields return `<field>` + `<field>_en` (e.g. `tratamiento`/
  `tratamiento_en`, `name`/`name_en`, knowledge `description_es/_en`). Client
  picks by language (mirror the legacy `loc()` helper).
- **Pagination:** `/api/farms` → `{data:[...], meta:{total,page,page_size}}`;
  most other lists are bare arrays. Errors: `{detail}` + HTTP status.

## Surfaces (5 — the wow set + the pitch)
1. **Farmer dashboard** (`/`) — `GET /api/farms` (paged), per-field
   `GET /api/farms/{id}/fields` + `/fields/{fid}/health|ndvi|soil|treatments`,
   `/heatmap`, `/weather`, `/notifications`. Health overview + map.
2. **Field detail** (`/campo?farm=X&field=Y`) — `/fields/{fid}` +
   `/health(/history,/trend)`, `/ndvi`, `/thermal`, `/soil`, `/treatments`.
3. **Intelligence** (`/intel`) — `/api/intel/summary`, `/anomalies`,
   `/soil-trends`, `/treatments` (treatment-effectiveness; `tratamiento_en`),
   `/regional-summary`.
4. **Alerts** (`/notificaciones`) — all farms → `/farms/{id}/notifications`
   (severity filter) + `POST .../{nid}/acknowledge`.
5. **Knowledge / WhatsApp demo** (pitch surface) — `/api/knowledge/fertilizers|
   crops|ancestral|tek-calendar`; WhatsApp demo flow for the pitch narrative.

(Full endpoint/response shapes in the API map appended to the session log.)

## Design approach — agency-led (per `ui-stack.md`; `claude-design.md` supports)
The agency design stack LEADS (ui-ux-pro-max → frontend-design → Framer Motion /
shadcn + council + Seb's taste) — the same engine that produced the RedHunter UX
that wowed pros. It out-designs Claude Design on produced-product quality, so the
build runs through the agency, not through a Claude Design canvas gate.
1. Manifest already extracted → `frontend/design/DESIGN_SYSTEM.md` (105 tokens;
   drift `treatment-*`/`intel-*`). Consolidate token synonyms first (`--accent`/
   `--accent-green`/`--brand-green` → one; `--card-bg`/`--card-surface`/`--surface`
   → one) so the brand system is honest.
2. **Agency builds** the 5 surfaces against the cultivOS brand tokens — this is
   where the wow comes from.
3. **Claude Design (optional, supporting):** drift enforcement on the new `web/`,
   deck export (PDF/PPTX) for the pitch, quick mockups for early alignment. Not
   the builder.
4. Re-extract from the new `web/` to verify: new tokens reuse existing; no new
   drift families.

## Phased build (de-risk + cost cap)
- **Phase 0 — scaffold:** Next app in `web/`, Tailwind+shadcn, API client
  (Bearer + base URL), i18n layer, design tokens from manifest. Cost cap: small.
- **Phase 1 — ONE vertical slice (farmer dashboard):** end-to-end against live
  API (`AUTH_ENABLED=false`). **CHECKPOINT — Seb reviews before continuing.**
- **Phase 2 — remaining 4 surfaces** once Phase 1 wows.
- Each phase: hard token/$ cap on the autoagent run (RedHunter burn lesson).
  Checkpoint between phases — no unattended multi-phase burn.

## Verification (per phase)
- App builds + runs; hits live API with real data.
- Playwright smoke of each surface (per `playwright.md`).
- Design-system re-extract shows no new drift.
- Bilingual ES/EN renders correctly (incl. `_en` data fields).

## Decision gate
After Phase 1 (and again after Phase 2): qualitative head-to-head vs legacy +
pitch reception. WIN → strangler migration plan (route new pages in, retire
legacy `frontend/` page-by-page). LOSE → keep legacy, cost was one capped spike.
