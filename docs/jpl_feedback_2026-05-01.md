# JPL Feedback — Round 2 — 2026-05-01

**Source:** Seb session with Jean-Paul Laurin, dump 2026-05-01.
**Owner:** agency (act on it)
**Audience tag:** dev-team
**Origin:** Follows up the 2026-04-17 JPL review (`docs/landing_rebuild_2026-04-30.md`). Landing v1.0 deployed to cultivosagro.com 2026-05-01. JPL re-reviewed; this is what he flagged.

---

## Top-line headline

> Lots of words and fancy terms — are they all needed?

The landing pitches well but reads dense. Compression pass is the #1 ask. Cut filler. Fewer adjectives. Per-acre framing tighter. One-minute pitch must be possible at the top.

---

## Verbatim items (Seb's notes, do not paraphrase)

- IP protection
- First to market
- Demo screens — display the solution and how it works on presentations
- Show the price that makes sense, clear projections
- Show the product not the service
- 10X investment 3-5 year for private
- Sold benefits well
- Trade show price
- License protection — small win
- When software finished, customer number one… what happens when 30 ppl sign up but only pilots
- Trade show initial launch, have a radius
- Marketing campaign and launch plan targeting all of southern Ontario
- Direct marketing
- Door to door
- Think more about target audience — how they sign up, how they benefit
- Analyze subscription models — who is actually doing a good job
- Think about target audience
- Minute or less to sell the idea — why they would care
- LAUNCH PLAN
- How much is it going to cost and how much time will it take to see it back
- Marketing launch plan to acquire should be 10X what it is right now
- Pharma blows brains out on marketing, providing that it recoups fast
- IP — be the first on the market and stand out with marketing and build relationships
- Farmers are loyal and have principles
- Watch out for cheaper competition
- Total investment number is not an accurate picture to take off — to get 20 yards into the race
- Think about the picture — what does the first 2-3 years look like with customer acquisition and marketing
- What is the cost of an acre
- Unit acres rather than farms — to project better
- Farming map targets — where is saturated, who has biggest farms
- Numbers change per acre
- Well articulated launch plan

---

## Themes (agency: collapse to these)

### A. Compression — primary ask
Every section currently uses 3 sentences where 1 would carry. Cut adjectives, rephrase in plain language. Specific offenders: ThesisBand body, Solution body, DualMarket moat, Investors header, Team bullets. Hero subhead is borderline — leave one strong sentence, kill the rest.

Standard: each block must pass the *"would a farmer texting a friend recognize this?"* test. Investor blocks can stay technical (ARR, SaaS multiple) but cut filler.

### B. IP / License protection — NEW section
Not on landing yet. Add a small block under or near the Competitive section:
- Trademarks: cultivOS, Cerebro, Cosechera (Mexico + Canada filings status)
- Provisional patent on Cerebro architecture (3-layer action/intelligence/data) — file if not filed
- Software license (proprietary, internal-only) — defensive note
- Trade secrets: training data + bilingual prompt corpus
- Why it matters: first-mover defensibility against cheaper copycats — JPL specifically flagged "watch out for cheaper competition"

This is a *small win* per JPL — one paragraph + bullets, not a section. Slot in between Competitive and DualMarket.

### C. Subscription model comparison — extend Competitive
JPL: "analyze subscription models, who is actually doing a good job."
Add a small panel inside or next to the Competitive section comparing per-acre subscription cost across the 6 row landscape (we already have $/ac column — call it out explicitly with a sentence: "Standard tier matches Climate FieldView's per-acre price while bundling drone services and an agronomist contractor pool").

### D. Target audience — flesh out Customer Path
Current `CustomerPathSection` is a 30→8→4→25 funnel. JPL wants more:
- Who specifically? Specialty crop operator profile: 50–500 acres, 2nd/3rd-generation, owner-operator, makes decisions with spouse, talks to neighbors first.
- How they sign up: trade show booth NFC tap, postcard QR, neighbor referral.
- What they benefit from in 30 / 90 / 180 days. (Day 30: first map. Day 90: first prescription saves them a spray pass. Day 180: visible yield delta.)

Insert a short profile card before the funnel. 1 paragraph + 3 bullets.

### E. "First 20 yards" framing
JPL: "Total investment number is not an accurate picture to take off — to get 20 yards into the race." We already have a "First 20 yards" milestone block in Investors. Surface it earlier — make it Investors' lead, not buried after ARR table. Also rephrase the $750K headline: not "what we want" — "what gets us the first 20 yards: 18-month runway through Series A trigger."

### F. One-minute pitch at the top
Hero already has 4 stat blocks. Add an `<aside>` underneath the title that reads exactly like a 1-minute pitch script — written for ear, not eye. 5–7 sentences max. JPL test: read it aloud in under 60 seconds. Cut until it fits.

### G. Acres not farms — sweep
We already use acres in most places. Sweep for any remaining "farms" framing where "acres under management" is the better metric. Specifically: hero stat 2 says "Pilot partner locked in (400+ ac)" — keep. ARR table says "X farms · Y customers" — re-order to "X acres · Y customers" with farms in parens.

### H. Saturation map — Launch plan add
JPL: "where is saturated, who has biggest farms." We have phase rollout but no density map. Embed an inline SVG (small — agency, generate it, do not request from Seb) showing SW Ontario specialty-crop density by county. Phase 1 50-mi radius overlaid. Sources: StatsCan Census of Agriculture 2021 specialty-crop counts by county.

### I. 10X marketing — already in Launch but bury-the-lede
JPL: "marketing launch plan should be 10X what it is right now, pharma-style." We say this once in `LaunchPlanSection` body. Promote it: section sub-header should make the number explicit ("$110K Y1 — 10× the prior plan because payback runs <6 months on Standard").

### J. "Loyal farmers, watch cheaper competition"
Defensibility one-liner. Add to Thesis or Competitive aside:
> "Farmers are loyal once you earn the relationship. The risk isn't conversion — it's a cheaper competitor copying after we've taken arrows. IP filings + Founding-100 logos + a 5-year farmer relationship at White Church are our first three moats."

### K. Investor return clarity
JPL: "10X investment 3-5 year for private."
Investors section already has 15–20× across 4–5 years. Restate at the very top of `InvestorsSection`, in plain language: "Pre-seed → Series A trigger in 18 months. Investor return: 10–20× across 3–5 years post-Series A dilution. SaaS comps support 8–12× ARR exit multiple."

---

## Work split for the agency

Pick **one task per session**. Do not bundle. Verify build passes after each.

| ID | Task | Where | Effort |
|---|---|---|---|
| LP10 | Compression pass — Theme A (sweep all sections) | `web/app/page.tsx` + `messages.ts` | 1 session |
| LP11 | IP / License section — Theme B | new `IpDefensibilitySection` | 1 session |
| LP12 | Subscription comp panel — Theme C | extend `CompetitiveSection` | 0.5 session |
| LP13 | Target audience profile + 30/90/180 benefits — Theme D | extend `CustomerPathSection` | 1 session |
| LP14 | Hero 1-minute pitch aside — Theme F | extend `Hero` | 0.5 session |
| LP15 | Investors restructure — Themes E + K | reorder `InvestorsSection` | 0.5 session |
| LP16 | Saturation map — Theme H | new SVG + extend `LaunchPlanSection` | 1 session |
| LP17 | Acres-not-farms sweep — Theme G | grep + edit | 0.25 session |
| LP18 | 10X marketing surfacing — Theme I | tweak `LaunchPlanSection` | 0.25 session |
| LP19 | Loyalty / cheaper-competition line — Theme J | add aside in Thesis or Competitive | 0.25 session |

---

## Acceptance — when this round of feedback is closed

- [ ] Hero readable aloud in 60 seconds
- [ ] No section longer than 3 short paragraphs
- [ ] IP / License block live with at least 4 concrete IP positions named
- [ ] CustomerPath includes audience profile + 30/90/180 benefits
- [ ] Saturation map embedded under Launch plan
- [ ] All "farms" → "acres under management" where the metric is acreage
- [ ] Marketing 10× number visible in section sub-header, not buried
- [ ] Build passes, both `?lang=en` and `?lang=es` render fully, deploy to cultivosagro.com
- [ ] Lighthouse Perf ≥ 90 mobile (no regression)

---

## Anti-scope

- Do **not** rewrite section structure. Keep current section order. Just compress + insert the 3 new sub-blocks (IP, audience profile, saturation map).
- Do **not** redesign brand or palette.
- Do **not** add a separate `/pitch` route. Single page rule still holds.
- Do **not** write a new spec doc. This file IS the spec for round 2.
