# cultivOS — Audit → Plan (2026-06-10)

31-agent audit (bugs + improvements, adversarially verified). 9 confirmed bugs, 23 improvements,
5 founder decisions. Ownership: **Agency** = mechanical frontend/i18n/UX. **Main-thread** = decisions + correctness-critical backend.

## 🔴 BUGS

### P0 — prod-breaking / demo-blocking
- **B1 · farms-response-unwrap (13 files)** — `/api/farms` returns `{data,meta}` but these pages call
  `farms.forEach`/`data.farms`/`farms.farms` on the wrapper → farm dropdown never populates → **app looks broken with seed data present.** THE demo killer.
  Files: `frontend/{alert-config,actions,alertas-estacionales,clima,comparar,reportes,exportar,flights,recommendations,soil-history,thermal-dashboard,timeline}.js` + `resumen.js`.
  Fix: the pattern already correct in `management.js`/`impacto-agricultor.js`/`notifications.js`:
  `const resp = await fetchJSON('/api/farms?page_size=100'); const farms = (resp && (resp.data||resp.items))||[]; if(!farms.length)return; farms.forEach(...)`.
  Done-gate: `rg "\.farms\.forEach|data\.farms|farms\.farms" frontend/` → **zero hits** + each page's `<select>` has >1 option on seeded DB. → **Agency** (main-thread reviews diff).
- **B2 · create_all-vs-alembic** — `session.py` create_all, no alembic in `run.sh`/boot → existing prod DB misses `Farm.tier` → **500 on economics.** Tests pass, prod breaks. → **Main-thread** (needs **D1**).

### P1
- **B3 · intel/intelligence i18n-lock** — `intel.html` + `intelligence.html` have ZERO data-i18n (intelligence.html hardcoded `lang=es`) → unusable in English. → Agency.
- **B4 · spanish-only API fields** — `treatment/disease/irrigation/crop_type/fertilizer.py` return `problema/tratamiento/…/description_es` with no `_en` → frontend can't show English KB/treatment content. → Main-thread (**D2**) + Agency.

### P2
- **B5 · frontend-i18n-gaps** — `mapa.html` (0 data-i18n), `economic-impact.html` (7 keys but i18n.js not loaded), `{alertas-clima,alineacion-tek,actions,api-docs}.js` (hardcoded Spanish via innerHTML), `impacto-agricultor.html` lang-toggle not wired. → Agency, batch w/ B3.
- ~~knowledge.js :8000 hardcode~~ — already fixed (ff0ffcd), no action.

## 🟢 IMPROVEMENTS
- **I1 · i18n auto-init** (P1, do first — substrate for B3/B5): auto read localStorage lang + applyAll + wire toggle globally. → Agency.
- **I2 · Ontario economics fallback** (P1): `economics.py` returns all-$0 for `country=='CA'` → at least an honest dated "coming soon"; ideally real CA assumptions. → Main-thread (**D3**).
- **I3 · UX loading/empty/aria** (P1): skeleton loaders on economic-impact hero, distinct empty-state on impacto-agricultor, aria-live on stats. → Agency.
- **I4 · API list-shape standardization** (P2): make ALL list endpoints `{data,meta}` (fields endpoint returns bare array — inconsistent). Do AFTER B1. → Main-thread (**D4**).
- **I5 · mobile/responsive + contrast** (P2): ≤480px stacking, WCAG contrast on delta-pill/legend, health-chip aria. → Agency.
- **I6 · visual polish** (P2): SVG econ icons vs unicode diamonds, badge contrast, semantic headings. → Agency (lowest).
- **I7 · backend hardening** (P2): (a) explicit `user.farm_id==farm_id` owner check for farmers [Main-thread, security]; (b) startup assertion all `assumptions` keys exist; (c) `compute_economist_summary` defaults `avg_health=50.0` for zero-data farms → **inflates new-farm savings in investor/grant outputs** → gate to insufficient_data/$0 (**D5**); (d) treatment-causality = comment only (YAGNI).

## ⚖️ FOUNDER DECISIONS (need Seb)
- **D1 (blocks B2):** migration source of truth — keep create_all + drop alembic (greenfield) OR alembic-authoritative (prod-safe). *Recommend alembic-authoritative — prod already on Railway.* One-line answer unblocks the prod 500.
- **D2 (blocks B4):** bilingual API content — pre-translated seed vs lazy Anthropic-translate-and-cache vs hybrid. *Recommend: bilingual seed for KB tables + lazy-translate-cache for generated text.* Also a voice call (farmer ES is luddite-register; machine EN→ES of admin copy may break it).
- **D3 (gates I2):** Ontario economics — ship honest "coming soon" now, or source real CA assumptions before the pilot? Touches founder-locked unit economics.
- **D4 (gates I4):** standardize all list endpoints to `{data,meta}`? Touches the bare-array fields endpoint.
- **D5 (in I7c):** OK to switch new-farm `avg_health` default 50.0 → insufficient_data/$0 even though new farms look less impressive? (Per "no false claims in investor copy".)

## EXECUTION ORDER
1. **B1** (Agency, w/ grep gate) — unblocks the whole app.
2. **I1** → **B3 + B5** (Agency) — localization.
3. **I3 → I5 → I6** (Agency) — UX/a11y/polish.
4. Decision-gated (Main-thread, after Seb): **B2/D1, B4/D2, I2/D3, I4/D4, I7c/D5, I7a**.

Source: workflow `wwfj2v3tn` (31 agents, 1.5M tokens). Full per-file evidence in that run.
