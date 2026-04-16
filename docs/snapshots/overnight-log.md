# cultivOS overnight log

| When (Toronto) | Item | Status | Ref |
|---|---|---|---|
| 2026-04-14 02:42 Toronto | N0 | DONE | dc441b0 |
2026-04-15 02:45 Toronto — N1 — DONE — created .github/workflows/test.yml (pytest on push/PR) and build.yml (Docker push to ghcr.io on v* tags)
2026-04-16 02:42 Toronto — N2 — DONE — flipped auth_enabled default to True, added JWT secret boot guard, added Depends(get_current_user) router-level dependency to 69 unguarded API router files, added AUTH_ENABLED=false test baseline fixture in conftest, updated .env.example
