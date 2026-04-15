# cultivOS frontend-v2

Next.js App Router rebuild of the cultivOS dashboard. Replaces the old vanilla-JS `frontend/` directory. Built as a static export — FastAPI serves the compiled `out/` directory directly.

**Run in development:** `npm run dev` (serves on :3000, proxies `/api/*` via `NEXT_PUBLIC_API_URL`)

**Build for production:** `npm run build` — output lands in `out/`, ready for FastAPI static mount.

**API base:** configured via `NEXT_PUBLIC_API_URL` in `.env.local` (copy `.env.example`).
