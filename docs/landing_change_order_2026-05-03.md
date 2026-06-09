# CultivOS Landing Page — Change Order

**For:** autoagent dev team
**From:** Sebastián
**Goal:** Shift tone from VC pitch deck → open, transparent presentation. Same facts, less performance.

---

## What's changing and why

The current page reads like an investor deck pasted into a website. We're shifting it toward an honest exposition that any thoughtful reader — investor, professor, agronomist, family — can walk away from with a clear sense of what we're building, where we are, and what we need.

**Keep:** narrative, problem, solution, why-now, competitive table, team, pilot specifics, sources.
**Cut:** exit multiples, funnel math, use-of-funds breakdown, 5-year ARR table, "three pillars ask," sales-deck section headers.
**Soften:** pricing promos, IP claims, anything that reads as a forecast.

---

## Global tone rules

1. **No exit math.** Drop "8–12× SaaS multiple," "$80M–$180M exit," "15–20× return," "Series A trigger." If a reader wants exit math, they'll ask.
2. **No internal funnel numbers on the public page.** "30 leads → 8 demos → 4 pilots" belongs in a deck, not the homepage.
3. **No promo language.** "trade-show launch promo," "buys density + case studies," "pharma-style aggressive" — all out.
4. **No claim we can't defend in front of a skeptical agronomist or IP lawyer.** Specifically: drop the "provisional patent on 3-layer architecture" line.
5. **Section headers describe content, not pitch theater.** "Investment story · pre-seed" → "Where we are." "Customer #1 path" → cut.

---

## Section-by-section changes

### 1. Top nav

**ACTION: EDIT**

```
BEFORE:  [Why now] [Product] [Pricing] [Investors]
AFTER:   [Why now] [Product] [Pricing] [Where we are]
```

Anchor `#investors` → `#where-we-are`.

---

### 2. Hero

**ACTION: KEEP HEADLINE + SUBHEAD. TRIM ONE LINE.**

Keep:

```
Hecho en México · scaling to Canada

The intelligence layer for precision agriculture.

Mexican company digitizing the farmers big agtech wrote off.
Precision ag via WhatsApp — validated in Jalisco, Ontario pilot
locked: White Church Farm, 400+ acres.

[Talk to us]  [hola@cultivosagro.com]
```

Keep the four stat cards (15–25%, 400+ ac, $121, $300–600K).

**Remove this line entirely:**

```
$750K CAD pre-seed · 8–12X SaaS multiple at exit
```

---

### 3. "Our unfair advantage" section

**ACTION: RENAME HEADER. KEEP BODY.**

```
BEFORE:  Our unfair advantage
         We digitize the demographic big agtech wrote off.

AFTER:   Who we build for
         The farmers big agtech wrote off.
```

Body copy (Who / How / Why now blocks) stays as-is.

---

### 4. "Why now · Three independent triggers"

**ACTION: KEEP.** This is the strongest section on the page.

Optional small edit: the closing line currently reads —

```
Deveron exited (April 2026), Farmers Edge pivoted B2B (Dec 2025) —
no one serves Ontario's direct-to-farmer specialty-crop segment.
```

Add a parallel line for the Mexican audience:

```
Deveron exited (April 2026), Farmers Edge pivoted B2B (Dec 2025).
On both sides of the border, the direct-to-farmer specialty-crop
intelligence layer is unbuilt.
```

---

### 5. "The problem · three failure modes"

**ACTION: KEEP.** Body is fine.

Remove this closing line:

```
Market vacuum: Deveron exited. Farmers Edge pivoted to B2B.
The specialty-crop direct-to-farmer intelligence slot is open.
```

It's redundant with section 4 and reads pitchy.

---

### 6. "Solution · Cerebro AI"

**ACTION: KEEP.** Three layers, mockup, Cosechera teaser — all fine.

---

### 7. "Demo trio · drone → decision → review"

**ACTION: KEEP.** Mockups 2/3/4 stay.

---

### 8. "Mexico foundation · Jalisco first"

**ACTION: EXPAND.** This is currently the thinnest section relative to its strategic importance. Replace the three-bullet ITESO block with the version below.

**Replace:**

```
ITESO partnership · three distinct programs
01 HAU Agroecological Garden
02 PAP "Vida digital" — Drone work
03 LINK Office
```

**With:**

```
ITESO partnership · three working tracks

01  HAU Agroecological Garden
    Hardware and sensor integration in ITESO's on-campus
    agroecological garden — controlled environment, real crop data,
    iterative testing under the direction of the agroecology team.

02  PAP "Vida digital"
    Professional Action Project — drone flights, NDVI mapping, and
    field data pipelines built alongside ITESO agricultural
    engineering students. Coordinated with Luis Luque (drone lab).

03  LINK Open Innovation Office
    ITESO's industry-university bridge. Coordinated with
    Juan José Solórzano (CEGINT). Channels practitioner feedback
    into curriculum and connects us to Jalisco's ag industry network.

Academic sponsor: Mtro. Carlos Alberto Fernández Guillot,
Coordinator, Unidad Académica Básica Ciencia de los Servicios.
```

Keep the legal-entity block but expand it slightly:

```
BEFORE:  Legal entity
         CultivOS México S.A. de C.V.
         Incorporation in progress · Guadalajara, MX

AFTER:   Legal entity
         CultivOS México S.A. de C.V.
         Incorporation in progress · Notaría Pública No. 62, Guadalajara
         Domicilio: Río Pánuco #1534, Colonia Atlas, Sector Reforma
```

---

### 9. Competitive landscape table

**ACTION: KEEP AS-IS.** Best single asset on the page.

---

### 10. "Defensibility plan · what investment activates"

**ACTION: REWRITE.** Current "Four moats — two already compounding, two filed at close" includes a claim (provisional patent on 3-layer architecture) that doesn't survive scrutiny by any IP lawyer or technical reader. Replace.

**Replace entire section with:**

```
What protects us · honest version

Farmers are loyal once you earn the relationship. The risk isn't
conversion — it's a faster-funded competitor copying after we've
taken the arrows. Three things compound in our favour:

01  Bilingual training data
    A two-market, Spanish-and-English corpus of crop imagery,
    agronomist judgments, and farmer voice notes. Not replicable
    from a desk in Toronto or San Francisco. Already accumulating.

02  Brand and trademark
    cultivOS, Cerebro, and Cosechera filed at IMPI (Mexico) and
    CIPO (Canada) at pre-seed close. Brand recognition compounds
    with every farm signed.

03  Distribution licence
    Proprietary software, internal-only. No open-source exposure.
    Full control of pricing and distribution — already in place.
```

(Provisional patent line is removed. If you want to keep an IP claim, it should be a specific algorithmic process — happy to draft that with a patent agent rather than asserting it on the homepage.)

---

### 11. "Dual-market data moat"

**ACTION: KEEP HEADER + BODY.** Rename closing block from "Talent + LLM advantage" — the LLM-fluency thing has commodified — to:

```
BEFORE:  Talent + LLM advantage
         Spanish-native ops + Spanish-fluent LLMs = reach
         competitors can't ship from Toronto or the US.

AFTER:   Spanish-native operations
         A Spanish-native team building in Spanish first means
         farmer trust, field nuance, and product fit that doesn't
         translate from a US- or Canada-led roadmap.
```

---

### 12. Pricing

**ACTION: KEEP TABLE. SOFTEN PROMO LANGUAGE.**

**Replace:**

```
Founding-100 · trade-show launch promo
First 100 farms get $48 CAD/ac/yr — locked 3 yrs.
33% off Standard. Buys density + case studies for Y2 sales.
100 territories max. Outdoor Farm Show Sept 2026 + Royal Winter
Fair Nov 2026.
```

**With:**

```
Founding cohort
The first 100 farms pay $48 CAD/ac/yr, locked for 3 years.
This is below cost on Standard and reflects the value of being
early — early customers shape the product, and the case studies
they generate become the foundation for everyone who follows.
```

Keep the tier table and the ARPU/CAC/payback row.

**Remove the "White Church Farm pilot · modeled" callout** ($121/ac, +15% yield, $102K/yr modeled impact) from this section — or move it to a smaller honest framing:

```
White Church Farm · what the math looks like
On a 400-acre Ontario specialty-crop farm, OMAFRA, OPACA, and
the MDPI 2025 meta-analysis suggest combined input savings and
yield gains in the $80–120/acre range. That's the order of
magnitude we're targeting in the Y1 pilot — to be measured,
not asserted.
```

---

### 13. "Customer #1 path · Outdoor Farm Show funnel"

**ACTION: REMOVE ENTIRELY.**

This is internal sales math. It belongs in a board meeting, not on the homepage.

---

### 14. "Launch plan · Southwestern Ontario"

**ACTION: KEEP CONTENT. SOFTEN COPY.**

**Replace this paragraph:**

```
$110K marketing budget Y1 — 10× the prior plan. Pharma-style:
aggressive because payback runs under six months on Standard.
We measure traction in acres under management, not farm logos.
Founding-100 buys density and case studies that shorten Y2
sales cycles.
```

**With:**

```
We measure traction in acres under management, not farm logos.
Y1 marketing leans heavily on trade-show presence and direct
relationships in a 50-mile radius from Hamilton — concentrated
density before geographic spread.
```

Keep the three phases and Mockup 5.

---

### 15. "Investment story · pre-seed" — rename and rewrite

**ACTION: REPLACE THIS WHOLE SECTION.**

This is the section that most signals "VC pitch" rather than "honest update." Replace the entire `#investors` block (header, "First 20 yards," use of funds, 5-year ARR table, non-dilutive stack, three pillars ask) with the version below.

**New section ID:** `#where-we-are`

**New copy:**

```
Where we are · what's next

We're working toward an 18-month runway funded by a mix of
non-dilutive grants and a modest pre-seed round. Below is what's
landed, what's pending, and what we're still figuring out — in
plain language.

What's landed
- ITESO partnership confirmed across three working tracks
- White Church Farm pilot locked (400+ ac, Haldimand County)
- Team in place: Sebastián (Hamilton), Mubeen (Toronto),
  Víctor (Guadalajara)
- CultivOS México S.A. de C.V. incorporating

What's in motion
- FODECIJAL 2026 application (Jalisco state R&D fund)
- Impulsora de Innovación México seed co-investment track
- NRC-IRAP advisor conversations (Canadian R&D)
- CultivOS Canada Inc. incorporation
- Cerebro v1 in-field validation

What we're still working out
- Series A timing depends on Y1 acreage traction, not a fixed
  calendar date
- Exit pathway: we know what kind of company we want to build
  more clearly than we know what its exit looks like, and we'd
  rather not pretend otherwise on a public page

Non-dilutive funding stack we're working through
- 🇲🇽 FODECIJAL 2026 (Modalidad C / Reto II.I)
- 🇲🇽 Impulsora de Innovación México
- 🇨🇦 NRC-IRAP (clean tech stream)
- 🇨🇦 CAAIN Smart Farms
- 🇨🇦 NSERC Alliance (requires university PI)
- 🇨🇦 SR&ED (35%+ refundable, $6M cap)

What we're looking for
- Capital that's patient enough to let unit economics prove
  themselves on real farms before scaling acquisition spend
- Academic partners — we have ITESO confirmed; we're open to
  Canadian university PIs (McMaster, Guelph, Waterloo, others)
  for NSERC Alliance
- Operators who've taken vertical SaaS or agtech from
  pre-revenue to first scale — the kind of person who'll tell
  us we're wrong about something specific
```

---

### 16. Three-pillar ask (Strategic capital · Academic partners · Business mentors)

**ACTION: REMOVE.** Folded into the new "What we're looking for" block above.

---

### 17. Team

**ACTION: KEEP AS-IS.** This section already reads honest and personal. Don't touch.

Small note: McMaster isn't named anywhere on the page. Add it to the academic-partners list in the new "Where we are" section (already done above) — that's the right place, not the team section.

---

### 18. Closing "Let's talk"

**ACTION: KEEP COPY. ADD CTAs.**

Currently only `mailto:hola@cultivosagro.com`. Add two more CTAs:

```
[Read the deck (PDF)]  [Book 30 minutes]  [hola@cultivosagro.com]
```

If the deck and Calendly aren't ready, leave the email-only CTA — but the deck PDF and a Calendly link should be the next two things shipped after this change order lands.

---

## Summary of removals

For the dev team's sanity, here's what's getting deleted from the live site:

- Hero strap line: "$750K CAD pre-seed · 8–12X SaaS multiple at exit"
- "Provisional patent" claim under Defensibility
- "Customer #1 path · Outdoor Farm Show funnel" entire section
- "Pharma-style aggressive" language in Launch plan
- "Investment story · pre-seed" header and section body (replaced)
- Use-of-funds 5-bullet breakdown
- 5-year ARR projection table
- "Exit thesis: $80M–$180M @ 8–12× ARR" subline
- "Three pillars · open-ended ask" section (folded into new section)
- "Investor return: 15–20× across 4–5 years post Series A dilution" line
- "Founding-100 · trade-show launch promo" header (softened)
- "Buys density + case studies for Y2 sales" line
- "Market vacuum" closing line under "The problem"

## Summary of additions

- McMaster named in academic-partner list
- ITESO partnership track expanded with named coordinators
- Legal entity block expanded with notaría and domicilio
- "Spanish-native operations" reframe replacing LLM moat claim
- "What we're still working out" honest block under Where we are
- New Where we are section structure: landed / in motion / still figuring out / funding stack / what we're looking for

---

## File / route notes for the dev team

- The `#investors` anchor is referenced in the top nav and likely elsewhere. Rename to `#where-we-are` and update any internal anchors.
- The Spanish version (`?lang=es`) needs a parallel pass — happy to ship that as a separate change order once this lands.
- No design changes requested — only copy and section structure. Visual hierarchy and layout stay.

---

*Drafted as part of pre-FODECIJAL / pre-Impulsora positioning pass. Questions to Sebastián directly.*
