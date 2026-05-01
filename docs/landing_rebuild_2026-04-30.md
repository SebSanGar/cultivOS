# cultivOS Landing Rebuild — Spec for Agency

**Date locked:** 2026-04-30
**Owner:** Seb (product), agency (build)
**Origin:** Jean-Paul Laurin pitch review + 2026-04-30 strategy session
**Audience tag:** dev-team

---

## Mission

Rebuild `cultivosagro.com` as a single-page investor-grade pitch + farmer-grade marketing site. **Landing IS the pitch.** No separate deck. No `/pitch` route.

Stack migration: vanilla `index.html` → **Next.js (App Router)**. Deploy on existing Railway pipeline.

---

## Locked decisions (do not re-litigate)

- **Single page** — all 18 deck cards become scroll sections
- **Mockups** — Seb provides 5 Designer-Claude outputs as PNG/SVG. Code wires them in. Do NOT generate from scratch
- **Pricing & ARR numbers** — locked, see `/Users/SebSan/.claude/projects/-Users-SebSan/memory/project_cultivos_economics.md`
- **Brand palette:** agricultural green `#2D6A2D`, cream `#FAF8F3`, navy `#1B2A3B`, signal yellow `#F4B400`, signal red `#C0392B`, water blue-gray `#A8C0CC`
- **Typography:** Inter (or Söhne if licensed)
- **Bilingual:** ES + EN switcher in header (existing site is Spanish; both required)
- **Pre-seed ask:** $750K CAD on $3M pre-money (Option B locked)

---

## Section list (top → bottom of single scroll)

1. **Hero / 60-sec pitch** — title + 4 stat blocks (15–25% input cost ↓, 400-acre Ontario pilot, $121/acre saved, $300–600K Y1 non-dilutive). Embed Mockup 1 (field-map dashboard) animated on scroll
2. **Why care** — 3 reasons it's now (Deveron deal closing Apr 2026, Farmers Edge → Corvian Dec 2025 finished B2B pivot, Transport Canada Phase 2 BVLOS Nov 2025)
3. **Problem** — 3 outline boxes: manual scouting cost, images-without-decisions, blanket-spray waste. Closing aside: "market vacuum"
4. **Solution + Mockup 1** — Cerebro = brain that directs drones. Embed Mockup 1 inline (or full-bleed). Farmer UX philosophy 4-bullet block
5. **Demo trio** — Mockups 2, 3, 4 in a horizontal triptych. Mobile insight card / WhatsApp brief / season report
6. **Cerebro 3-layer architecture** — Action / Intelligence / Data. Concentric circles or stacked diagram (replace Gamma's version with cleaner SVG)
7. **Mexico foundation** — Jalisco stats. **CONFIRM: agrícola $117.2B MXN OR agropecuario $217B MXN — Seb to choose**. ITESO partnership *(split into two distinct: HAU agroecological garden + PAP "Vida digital" drone work + LINK office)*. CultivOS México S.A. de C.V. status
8. **Why Ontario + Mockup 5 (radius map)** — 11.7M acres, 78% GPS, post-Deveron vacuum. Embed SW Ontario radius map. Non-dilutive funding stack on right
9. **White Church 400-ac pilot math** — full cost table. Total saved $48,400. Plus +15% yield = ~$102K total impact. Subscription cost $28,800. Payback <5 months
10. **Pricing & unit economics** — 4-tier table: Básico/Standard/Premium/Empresarial (MXN per ha + CAD per ac). Founding-100 promo $48/ac/yr. CAC ~$400, payback <6 months. **Empresarial tier line: "+ unlimited apps + on-demand agronomist hours (contractor pool — OMAFRA/OAFT in Ontario, ITESO/CONAGUA network in MX). ~80 hrs/yr included."**
11. **Competitive landscape** — comp table:
    - Deveron — agreed Nov 2025, closing April 2026 — exiting market
    - Farmers Edge — completed B2B pivot, Corvian Dec 2025 — no direct-to-farmer
    - Climate FieldView (Bayer) — **250M+ acres in 23 countries** (NOT 60M — that was hectares 2021), broad-acre row crops
    - Granular — sold by Corteva to **Traction Ag in 2022** (orig $300M / 2M ac = $150/ac comp)
    - John Deere Operations Center — equipment-tied lock-in
    - CultivOS — only direct-to-farmer specialty-crop intelligence + drone services bundle
12. **Customer #1 path** — 30 leads (Outdoor Farm Show Sept 2026) → 8 free demos → 4 paid pilots → 25 paying customers Y1 close
13. **Launch plan** — trade shows (Outdoor Farm Show, Royal Winter Fair, FCC AgriTrade, Ontario F&V Convention), 50/100/150-mi radius rollout, $110K Y1 marketing budget, channels (booth, direct mail, door-to-door, founding-100 logos, field days)
14. **Investment story** — $750K CAD ask, Y5 ARR $10–15M, 8–12X SaaS multiple, $80–180M exit, 15–20X return. "First 20 yards" Y1 milestones. Use-of-funds breakdown 45/17/25/8/5
15. **Funding pipeline** — non-dilutive stack:
    - Mexico: FODECIJAL 2026 **Modalidad C up to $2.5M MXN**, deadline May 14 (drop unverified May 7 platform date). Impulsora — applied April 30 / **September window**
    - Canada: NRC-IRAP up to $500K (verify ITA), CAAIN $9M pool / $3M max / 4 deadlines through Oct 2026, NSERC Alliance 2:1 matching, **SR&ED 35%+ enhanced cap raised $3M → $6M (Budget 2025)**
16. **Dual-market data moat** — Mexico Oct–May / Canada May–Oct. Same team, same hardware, fleet migration. Cross-market data compounding. Dual-entity funding stack
17. **Team** — three founders:
    - **Sebastián Sánchez García — CEO & Product.** 16 yrs food production. UX-first farmer tech. Dual citizen MX/CA PR. Hamilton, ON
    - **Mubeen Zulfiqar — CTO.** MMath Computer Science, University of Waterloo (Buhr Programming Languages group). 7 publications in network slicing, optical networks, concurrent systems (Boutaba networking group). **CNSM 2019 Best Paper Award.** ~86 Google Scholar citations. Director, DevGate Canada. **Toronto, ON**
    - **Víctor Hernández Quintana — Director, Mexico Operations.** Former CONAGUA infrastructure builder. 5-state agricultural logistics network. Pursuing AFAC RPAS pilot certification. Guadalajara, MX
18. **Open-ended ask** — three pillars (Strategic Capital / Academic Partners / Business Mentors). No specific people named. Universities listed as candidates (McMaster, Guelph, Waterloo, Western, UofT, ITESO, CIMMyT). Status block transparent: pre-revenue, Cerebro in design, applications active, partnerships in development. Contact: hola@cultivosagro.com

---

## Soft language fixes

- "<5% small farms have precision ag" → **"limited precision-ag adoption among small producers (INEGI ENA 2019)"**
- Drone prices in any reference: Mavic Multispectral **~$4,600 CAD**, Mavic Thermal **~$7,400 CAD**, Agras T100 **$36–48K depending on dealer**
- ITESO: split garden + drone PAP + LINK as three distinct programs

---

## Technical requirements

### Stack
- Next.js (App Router), TypeScript
- Tailwind CSS (brand palette as theme tokens)
- Framer Motion for scroll animations (subtle — no parallax theme-park nonsense)
- next-intl or simple ES/EN switcher (existing site is bilingual)
- Static export OK (Railway can serve, or migrate to Vercel — Seb's call)

### Performance budgets
- Lighthouse Performance ≥ 90 mobile
- LCP < 2.5s
- CLS < 0.1
- Total page weight < 2 MB

### Asset handling
- Mockups arrive from Seb as PNG (1x + 2x) or SVG. Place in `public/mockups/`
- All images use `next/image` with proper sizing
- SVG mockups inlined where small enough; PNG for high-detail

### Routing
- Single route `/` (the whole pitch)
- `/en` and `/es` for language slugs (or query param ?lang=en)
- 301 redirects from old `index.html` paths if any

### CI / deploy
- GitHub Actions: typecheck + build on PR
- Railway auto-deploy from main (existing pipeline)
- DNS: cultivosagro.com — already pointed (no change)

### Migration
- Move existing `index.html` content to `archive/` for reference
- Strip out old `images/` once new flow is wired
- Keep `robots.txt`, `sitemap.xml`, `CNAME` at root (or recreate via Next.js)

---

## Out of scope (do not build)

- Login / customer dashboard (later — when Cerebro v1 ships)
- Stripe checkout
- Blog
- Documentation site
- Multi-currency calculator (use static MXN/CAD numbers from spec)

---

## Acceptance criteria

- [ ] All 18 sections present + content matches spec verbatim on locked numbers
- [ ] All 5 mockups embedded responsively
- [ ] ES + EN switcher functional, no missing strings
- [ ] Mobile + tablet + desktop layouts polished
- [ ] Lighthouse mobile Perf ≥ 90, A11y ≥ 95
- [ ] Deployed to staging URL for Seb review before pointing cultivosagro.com
- [ ] 12 fact-checked corrections all reflected (FieldView 250M+, Granular at Traction Ag, Farmers Edge Corvian, Deveron closing Apr 2026, drone prices, SR&ED $6M cap, FODECIJAL Mod C $2.5M, etc.)

---

## Resolved (defaults locked 2026-04-30)

1. **Jalisco** — use **$217B MXN agropecuario (UDG citation)** — broader TAM
2. **NRC-IRAP** — phrase as "**up to $500K (subject to ITA verification)**" — honest hedge
3. **White Church Farm** — soften to "**5-year farmer relationship in Haldimand County, ON**" — not publicly listed
4. **Hosting** — **Vercel** — Next.js native, free tier, CDN edge
