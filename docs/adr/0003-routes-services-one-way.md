# ADR 0003 — One-way dependency: routes import services, services never import routes

## Context

The cultivOS backend is structured as FastAPI routers (`src/cultivos/api/`) that call
business logic in services (`src/cultivos/services/`). Without an enforced boundary, it
is easy to let services reach back into route utilities, import request/response models
from the API layer, or trigger side effects that belong in a request lifecycle. This
pattern has appeared in similar projects when service files grow and developers grab
the nearest convenient import without thinking about layering.

## Decision

Services have exactly one dependency direction: inward. A service may import from
`models/`, `db/`, and `utils/`. It may not import from `api/`. Routes import from
services; services never import from routes. This is a hard rule, not a guideline.

Pure functions are the preferred service shape: arrays and scalars in, computed results
out. No HTTP objects, no `Request`, no `Response`, no FastAPI `Depends` calls inside
service code. Side effects (database writes, WhatsApp messages, S3 uploads) are
explicit function arguments or return values — never ambient.

## Consequences

Every service function is independently testable with no FastAPI test client. The
test suite calls `compute_ndvi(nir, red)` directly; it does not need to simulate an
HTTP request. This is why our test suite can run 3000+ tests without a running server.

The trade-off is discipline. When a new endpoint needs shared logic, the reflex is
sometimes to reach for a route-layer utility. We resist that. Shared logic goes into
`utils/` or a new service module, never into the route layer where it would create a
circular import or a hidden coupling.

## Alternatives considered

**Shared utilities accessible from both layers** — creates ambiguity about where logic
lives and enables gradual coupling drift. We have seen this turn into a ball of mud in
exactly the kinds of projects cultivOS is designed not to become.

**Dependency injection framework (e.g., injector, lagom)** — adds indirection without
adding clarity for our current scale. FastAPI's `Depends` mechanism already provides
clean DI at the route boundary. We use it there and stop.
