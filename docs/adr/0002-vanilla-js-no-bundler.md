# ADR 0002 — Vanilla JS, no bundler, for the legacy frontend

## Context

The original cultivOS frontend (`frontend/`) is a dashboard served as static files.
It needs to render farm maps, NDVI overlays, health charts, and alert feeds. The
audience for this frontend is internal (grant reviewers, the founding team) while the
farmer-facing UI is rebuilt from scratch on `frontend-v2` (Next.js App Router).
The old frontend must remain readable, deployable, and debuggable by anyone with a
browser devtools tab — no build step, no node_modules, no transpilation.

## Decision

The `frontend/` directory is plain HTML, CSS, and JavaScript. No npm, no Webpack,
no Vite, no TypeScript compilation. Third-party libraries (Leaflet, Chart.js) are
loaded from CDN `<script>` tags. Functions are module-scoped via IIFE or native
ES modules where browsers support them. All JS files are served directly by
FastAPI's `StaticFiles` mount.

## Consequences

A new contributor can open `frontend/index.html` in a browser pointed at the local
backend and see a working dashboard with zero setup. There is no build cache to
invalidate, no lockfile drift, and no toolchain version mismatch. Debugging is
`console.log` and the Sources panel — no sourcemap complexity.

The trade-off is that shared logic (nav component, tooltips, chart helpers) must
be written as small plain-JS modules rather than imported npm packages. We accept
that cost. The legacy frontend is a transitional artifact — it exists to pass grant
reviews and provide a reference implementation while `frontend-v2` reaches parity.
Once parity is reached, `frontend/` is deleted.

## Alternatives considered

**Vite + plain JS** — adds a dev-server and a build step for production. The build
output is straightforward, but the operational overhead is not zero and the benefit
(hot reload) is not meaningful for a transitional reference frontend.

**React (CRA or Vite)** — the rebuild track (`frontend-v2`) already uses Next.js.
Introducing React into `frontend/` would split our attention between two React
codebases and create confusion about which one is canonical. We keep `frontend/`
deliberately simple so the contrast with `frontend-v2` is clear.
