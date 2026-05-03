import Image from "next/image";
import { EmbedCard } from "./components/embed-card";
import { LangToggle } from "./components/lang-toggle";
import { getDict, type Lang } from "./i18n/messages";

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function Home({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const langParam = Array.isArray(params.lang) ? params.lang[0] : params.lang;
  const lang: Lang = langParam === "es" ? "es" : "en";
  const t = getDict(lang);

  return (
    <div className="flex flex-1 flex-col bg-cream text-navy">
      <SiteNav lang={lang} t={t} />
      <main className="flex flex-1 flex-col">
        <Hero lang={lang} t={t} />
        <ThesisBand t={t} />
        <WhyNow t={t} />
        <ProblemSection t={t} />
        <SolutionSection lang={lang} t={t} />
        <DemoTrioSection lang={lang} t={t} />
        <MexicoFoundationSection t={t} />
        <CompetitiveSection t={t} />
        <IpDefensibilitySection t={t} />
        <DualMarketSection t={t} />
        <PricingSection t={t} />
        <LaunchPlanSection lang={lang} t={t} />
        <InvestorsSection t={t} />
        <TeamSection t={t} lang={lang} />
        <ContactStrip lang={lang} />
      </main>
      <SiteFooter lang={lang} />
    </div>
  );
}

type T = ReturnType<typeof getDict>;

function SiteNav({ lang, t }: { lang: Lang; t: T }) {
  return (
    <header className="border-b border-line/70 bg-cream/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4 md:px-10">
        <a
          href={lang === "es" ? "/?lang=es" : "/"}
          className="flex items-center gap-3 group"
        >
          <Image
            src="/brand/cultivOS_drop.png"
            alt="cultivOS drop"
            width={48}
            height={48}
            priority
            className="h-9 w-9 md:h-10 md:w-10"
          />
          <span className="font-serif text-2xl tracking-tight text-navy md:text-[28px] leading-none">
            cultiv<span className="text-green italic">OS</span>
          </span>
        </a>
        <nav className="hidden items-center gap-8 text-sm text-muted md:flex">
          <a className="hover:text-navy" href="#why-now">
            {t.nav.whyNow}
          </a>
          <a className="hover:text-navy" href="#product">
            {t.nav.product}
          </a>
          <a className="hover:text-navy" href="#pricing">
            {t.nav.pricing}
          </a>
          <a className="hover:text-navy" href="#where-we-are">
            {t.nav.investors}
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <LangToggle current={lang} />
          <a
            href="mailto:hola@cultivosagro.com"
            className="rounded-full bg-green px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-green-700"
          >
            {t.nav.cta}
          </a>
        </div>
      </div>
    </header>
  );
}

function Hero({ lang, t }: { lang: Lang; t: T }) {
  const stats = [
    { label: t.hero.stat1Label, title: t.hero.stat1Title, sub: t.hero.stat1Sub },
    { label: t.hero.stat2Label, title: t.hero.stat2Title, sub: t.hero.stat2Sub },
    { label: t.hero.stat3Label, title: t.hero.stat3Title, sub: t.hero.stat3Sub },
    { label: t.hero.stat4Label, title: t.hero.stat4Title, sub: t.hero.stat4Sub },
  ];
  return (
    <section className="relative overflow-hidden border-b border-line/70 bg-cream">
      <div className="mx-auto grid max-w-7xl gap-12 px-6 pb-24 pt-16 md:grid-cols-12 md:px-10 md:pb-32 md:pt-24">
        <div className="md:col-span-7">
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-white/70 px-3 py-1 text-xs font-medium uppercase tracking-[0.16em] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-green" />
            {t.hero.badge}
          </span>
          <h1 className="mt-6 font-serif text-5xl leading-[1.05] tracking-tight text-navy md:text-7xl">
            {t.hero.title}
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-navy-2 md:text-xl">
            {t.hero.subhead}
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <a
              href="#pricing"
              className="inline-flex items-center gap-2 rounded-full bg-navy px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-navy-2"
            >
              {t.hero.ctaPrimary}
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path
                  d="M3 7h8M7.5 3.5L11 7l-3.5 3.5"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>
            <a
              href="mailto:hola@cultivosagro.com"
              className="text-sm font-medium text-navy underline-offset-4 hover:underline"
            >
              {t.hero.ctaSecondary}
            </a>
          </div>
        </div>
        <div className="md:col-span-5">
          <div className="grid gap-3 sm:grid-cols-2">
            {stats.map((stat) => (
              <div
                key={stat.title}
                className="rounded-2xl border border-line bg-white p-5 shadow-[0_1px_2px_rgba(27,42,59,0.04)]"
              >
                <div className="font-serif text-3xl font-medium tracking-tight text-green">
                  {stat.label}
                </div>
                <div className="mt-2 text-sm font-semibold text-navy">
                  {stat.title}
                </div>
                <div className="mt-1 text-xs leading-relaxed text-muted">
                  {stat.sub}
                </div>
              </div>
            ))}
          </div>
          {t.hero.footnote && (
            <p className="mt-5 font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
              {t.hero.footnote}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

function ThesisBand({ t }: { t: T }) {
  const points = [
    { label: t.thesis.whoLabel, copy: t.thesis.whoCopy },
    { label: t.thesis.howLabel, copy: t.thesis.howCopy },
    { label: t.thesis.whyLabel, copy: t.thesis.whyCopy },
  ];
  return (
    <section className="border-b border-line/70 bg-navy py-24 text-cream md:py-28">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-cream/60">
          {t.thesis.eyebrow}
        </span>
        <h2 className="mt-3 max-w-4xl font-serif text-4xl leading-[1.05] tracking-tight text-cream md:text-6xl">
          {t.thesis.title}
        </h2>
        <p className="mt-6 max-w-3xl text-base leading-relaxed text-cream/80 md:text-lg">
          {t.thesis.body}
        </p>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {points.map((p) => (
            <div
              key={p.label}
              className="rounded-2xl border border-cream/10 bg-cream/[0.03] p-6"
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cream/55">
                {p.label}
              </div>
              <p className="mt-3 text-sm leading-relaxed text-cream/85">
                {p.copy}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function WhyNow({ t }: { t: T }) {
  const cards = [
    { title: t.whyNow.card1Title, body: t.whyNow.card1Body },
    { title: t.whyNow.card2Title, body: t.whyNow.card2Body },
    { title: t.whyNow.card3Title, body: t.whyNow.card3Body },
  ];
  return (
    <section
      id="why-now"
      className="border-b border-line/70 bg-cream-2/60 py-24 md:py-28"
    >
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.whyNow.eyebrow}
          </span>
          <h2 className="max-w-3xl font-serif text-3xl tracking-tight text-navy md:text-5xl">
            {t.whyNow.title}
          </h2>
        </div>
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {cards.map((card, i) => (
            <article
              key={card.title}
              className="rounded-2xl border border-line bg-white p-7"
            >
              <div className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.14em] text-muted">
                <span className="font-mono text-green">0{i + 1}</span>
                <span>{t.whyNow.triggerLabel}</span>
              </div>
              <h3 className="mt-4 font-serif text-2xl tracking-tight text-navy">
                {card.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-navy-2">
                {card.body}
              </p>
            </article>
          ))}
        </div>
        <p className="mt-8 max-w-3xl text-sm leading-relaxed text-muted">
          {t.whyNow.footer}
        </p>
      </div>
    </section>
  );
}

function ProblemSection({ t }: { t: T }) {
  const boxes = [
    { title: t.problem.box1Title, body: t.problem.box1Body },
    { title: t.problem.box2Title, body: t.problem.box2Body },
    { title: t.problem.box3Title, body: t.problem.box3Body },
  ];
  return (
    <section className="border-b border-line/70 bg-cream py-24 md:py-28">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.problem.eyebrow}
          </span>
          <h2 className="max-w-3xl font-serif text-3xl tracking-tight text-navy md:text-5xl">
            {t.problem.title}
          </h2>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {boxes.map((box, i) => (
            <div
              key={box.title}
              className="rounded-2xl border border-line bg-white p-7"
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                0{i + 1}
              </div>
              <h3 className="mt-4 font-serif text-xl tracking-tight text-navy">
                {box.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-navy-2">
                {box.body}
              </p>
            </div>
          ))}
        </div>
        {t.problem.aside && (
          <aside className="mt-10 rounded-2xl border border-red/30 bg-red/[0.04] px-6 py-5">
            <p className="text-sm leading-relaxed text-navy">
              {t.problem.aside}
            </p>
          </aside>
        )}
      </div>
    </section>
  );
}

function SolutionSection({ lang, t }: { lang: Lang; t: T }) {
  const layers = [
    { label: t.solution.layer1Label, copy: t.solution.layer1Copy },
    { label: t.solution.layer2Label, copy: t.solution.layer2Copy },
    { label: t.solution.layer3Label, copy: t.solution.layer3Copy },
  ];
  return (
    <section
      id="product"
      className="border-b border-line/70 bg-cream py-24 md:py-28"
    >
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="md:col-span-7">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
              {t.solution.eyebrow}
            </span>
            <h2 className="mt-3 font-serif text-4xl tracking-tight text-navy md:text-5xl">
              {t.solution.title}
            </h2>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-navy-2 md:text-lg">
              {t.solution.body}
            </p>
          </div>
          <ul className="md:col-span-5 grid gap-3 self-end">
            {layers.map((layer) => (
              <li
                key={layer.label}
                className="rounded-xl border border-line bg-white p-4"
              >
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                  {layer.label}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-navy-2">
                  {layer.copy}
                </p>
              </li>
            ))}
          </ul>
        </div>
        <div className="mt-12">
          <EmbedCard
            src="/mockups/field-map/index.html"
            title={t.solution.mockupTitle}
            badge={t.solution.mockupBadge}
            aspectRatio="16 / 9"
          />
          <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
            {t.solution.mockupCaption}
          </p>
        </div>
        <aside className="mt-12 rounded-2xl border border-line bg-cream-2/50 p-6 md:p-8">
          <div className="flex flex-col items-start gap-3 md:flex-row md:items-center md:justify-between md:gap-8">
            <div>
              <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-green">
                {t.solution.asideEyebrow}
              </span>
              <p className="mt-2 max-w-3xl text-base leading-relaxed text-navy md:text-lg">
                {t.solution.asideBody1} <b>{t.solution.asideWeight}</b>
                {t.solution.asideBody2}{" "}
                <b className="text-green">{t.solution.cosecheraName}</b>{" "}
                {t.solution.cosecheraGloss}{" "}
                <span className="text-muted">{t.solution.asideNote}</span>
              </p>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-green font-semibold whitespace-nowrap">
              <b className="text-navy">{t.solution.asideTag}</b> {t.solution.asideTagSuffix}
            </span>
          </div>
        </aside>
      </div>
    </section>
  );
}

function DemoTrioSection({ lang, t }: { lang: Lang; t: T }) {
  return (
    <section className="border-b border-line/70 bg-cream-2/40 py-24 md:py-28">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="flex flex-col gap-3">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.demoTrio.eyebrow}
          </span>
          <h2 className="max-w-3xl font-serif text-4xl tracking-tight text-navy md:text-5xl">
            {t.demoTrio.title}
          </h2>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-2">
          <EmbedCard
            src="/mockups/insight-card/index.html"
            title={t.demoTrio.card1Title}
            badge={t.demoTrio.card1Badge}
            subtitle={t.demoTrio.card1Subtitle}
            aspectRatio="9 / 16"
            className="md:max-w-md md:mx-auto md:w-full"
          />
          <EmbedCard
            src="/mockups/weekly-brief/index.html"
            title={t.demoTrio.card2Title}
            badge={t.demoTrio.card2Badge}
            subtitle={t.demoTrio.card2Subtitle}
            aspectRatio="9 / 16"
            className="md:max-w-md md:mx-auto md:w-full"
          />
        </div>
        <div className="mt-6">
          <EmbedCard
            src="/mockups/season-report/index.html"
            title={t.demoTrio.card3Title}
            badge={t.demoTrio.card3Badge}
            subtitle={t.demoTrio.card3Subtitle}
            aspectRatio="16 / 10"
          />
        </div>
      </div>
    </section>
  );
}

function MexicoFoundationSection({ t }: { t: T }) {
  const programs = [
    { title: t.mexico.program1Title, body: t.mexico.program1Body },
    { title: t.mexico.program2Title, body: t.mexico.program2Body },
    { title: t.mexico.program3Title, body: t.mexico.program3Body },
  ];
  return (
    <section className="border-b border-line/70 bg-cream-2/40 py-24 md:py-28">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.mexico.eyebrow}
          </span>
          <h2 className="max-w-3xl font-serif text-3xl tracking-tight text-navy md:text-5xl">
            {t.mexico.title}
          </h2>
          <p className="mt-3 max-w-3xl text-base leading-relaxed text-navy-2 md:text-lg">
            {t.mexico.body}
          </p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-line bg-white p-6">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.mexico.statLabel}
            </div>
            <div className="mt-2 font-serif text-3xl font-medium tracking-tight text-navy">
              {t.mexico.statTitle}
            </div>
            <div className="mt-1 text-xs leading-relaxed text-muted">
              {t.mexico.statSub}
            </div>
          </div>
          <div className="rounded-2xl border border-line bg-white p-6">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.mexico.adoptionLabel}
            </div>
            <div className="mt-2 font-serif text-3xl font-medium tracking-tight text-navy">
              {t.mexico.adoptionTitle}
            </div>
            <div className="mt-1 text-xs leading-relaxed text-muted">
              {t.mexico.adoptionSub}
            </div>
          </div>
        </div>

        <div className="mt-10">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.mexico.itesoBadge}
          </span>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {programs.map((prog, i) => (
              <div
                key={prog.title}
                className="rounded-2xl border border-line bg-white p-6"
              >
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                  0{i + 1}
                </div>
                <h3 className="mt-3 font-serif text-lg tracking-tight text-navy">
                  {prog.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-navy-2">
                  {prog.body}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 rounded-2xl border border-green/30 bg-green/[0.04] px-6 py-5 flex flex-col gap-1 md:flex-row md:items-center md:gap-8">
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
            {t.mexico.entityLabel}
          </span>
          <span className="font-serif text-xl tracking-tight text-navy">
            {t.mexico.entityTitle}
          </span>
          <span className="font-mono text-[11px] text-muted">
            {t.mexico.entityStatus}
          </span>
        </div>
      </div>
    </section>
  );
}

function CompetitiveSection({ t }: { t: T }) {
  const rows = [
    {
      name: "Climate FieldView (Bayer)",
      status: "Active · 250M+ acres, 23 countries",
      price: "~$25/ac",
      crop: "Broad-acre row crops",
      d2f: "Yes",
      bundle: "Software only",
      muted: false,
    },
    {
      name: "Granular (Traction Ag, since 2022)",
      status: "Active · sold by Corteva 2022",
      price: "~$15–30/ac",
      crop: "Broad-acre",
      d2f: "Yes",
      bundle: "Software only",
      muted: false,
    },
    {
      name: "Deveron Corp",
      status: "Asset sale closed April 2026",
      price: "n/a",
      crop: "Specialty",
      d2f: "Yes",
      bundle: "Drone services — exiting",
      muted: true,
    },
    {
      name: "Farmers Edge → Corvian",
      status: "B2B pivot completed Dec 2025",
      price: "n/a",
      crop: "Broad-acre",
      d2f: "No (enterprise B2B)",
      bundle: "Software",
      muted: true,
    },
    {
      name: "John Deere Operations Center",
      status: "Active · equipment-bundled",
      price: "Bundled",
      crop: "Broad-acre",
      d2f: "Locked-in to JD equipment",
      bundle: "Equipment-tied",
      muted: false,
    },
    {
      name: "cultivOS",
      status: "Launching 2026 · MX foundation, CA expansion",
      price: "$36–$216 CAD/ac",
      crop: "Specialty crops",
      d2f: "Yes — WhatsApp + voice + color cards",
      bundle: "Drone services + AI prescriptions + agronomist contractor + bilingual",
      muted: false,
      highlight: true,
    },
  ];
  return (
    <section className="border-b border-line/70 bg-cream-2/40 py-24 md:py-28">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="flex flex-col gap-3">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.competitive.eyebrow}
          </span>
          <h2 className="max-w-3xl font-serif text-4xl tracking-tight text-navy md:text-5xl">
            {t.competitive.title}
          </h2>
          <p className="mt-2 max-w-3xl text-base leading-relaxed text-navy-2 md:text-lg">
            {t.competitive.body}
          </p>
        </div>

        <div className="mt-12 overflow-hidden rounded-2xl border border-line bg-white shadow-[var(--shadow-soft)]">
          <table className="w-full border-collapse text-sm">
            <thead className="bg-cream-2/60 text-left font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">{t.competitive.colPlayer}</th>
                <th className="px-4 py-3 font-medium">{t.competitive.colStatus}</th>
                <th className="px-4 py-3 font-medium">{t.competitive.colPerAcre}</th>
                <th className="px-4 py-3 font-medium">{t.competitive.colCrops}</th>
                <th className="px-4 py-3 font-medium">{t.competitive.colD2f}</th>
                <th className="px-4 py-3 font-medium">{t.competitive.colBundle}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.name}
                  className={`border-t border-line align-top ${r.highlight ? "bg-green/[0.06]" : ""} ${r.muted ? "opacity-70" : ""}`}
                >
                  <td className="px-4 py-3">
                    <div className={`text-sm font-semibold ${r.highlight ? "text-green" : "text-navy"}`}>
                      {r.name}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs leading-relaxed text-navy-2">
                    {r.status}
                  </td>
                  <td className="px-4 py-3 font-mono text-sm font-semibold text-navy">
                    {r.price}
                  </td>
                  <td className="px-4 py-3 text-xs leading-relaxed text-navy-2">
                    {r.crop}
                  </td>
                  <td className="px-4 py-3 text-xs leading-relaxed text-navy-2">
                    {r.d2f}
                  </td>
                  <td className="px-4 py-3 text-xs leading-relaxed text-navy-2">
                    {r.bundle}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-6 max-w-3xl text-xs leading-relaxed text-muted">
          {t.competitive.sources}
        </p>
      </div>
    </section>
  );
}

function IpDefensibilitySection({ t }: { t: T }) {
  const items = [
    { label: t.ip.tmLabel, copy: t.ip.tmCopy },
    { label: t.ip.patentLabel, copy: t.ip.patentCopy },
    { label: t.ip.licenseLabel, copy: t.ip.licenseCopy },
    { label: t.ip.secretsLabel, copy: t.ip.secretsCopy },
  ];
  return (
    <section className="border-b border-line/70 bg-cream py-16 md:py-20">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="rounded-2xl border border-navy/20 bg-navy/[0.03] p-6 md:p-8">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.ip.eyebrow}
          </span>
          <h3 className="mt-2 font-serif text-2xl tracking-tight text-navy md:text-3xl">
            {t.ip.title}
          </h3>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-navy-2">
            {t.ip.body}
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
            {items.map((item) => (
              <div
                key={item.label}
                className="rounded-xl border border-line bg-white p-4"
              >
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                  {item.label}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-navy-2">
                  {item.copy}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function DualMarketSection({ t }: { t: T }) {
  const seasons = [
    {
      label: t.dualMarket.season1Label,
      copy: t.dualMarket.season1Copy,
      color: "from-yellow/20 to-cream",
    },
    {
      label: t.dualMarket.season2Label,
      copy: t.dualMarket.season2Copy,
      color: "from-cream-2 to-cream",
    },
    {
      label: t.dualMarket.season3Label,
      copy: t.dualMarket.season3Copy,
      color: "from-green/20 to-cream",
    },
  ];
  const moat = [
    { title: t.dualMarket.moat1Title, copy: t.dualMarket.moat1Copy },
    { title: t.dualMarket.moat2Title, copy: t.dualMarket.moat2Copy },
    { title: t.dualMarket.moat3Title, copy: t.dualMarket.moat3Copy },
  ];
  return (
    <section className="border-b border-line/70 bg-cream py-24 md:py-28">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="flex flex-col gap-3">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.dualMarket.eyebrow}
          </span>
          <h2 className="max-w-3xl font-serif text-4xl tracking-tight text-navy md:text-5xl">
            {t.dualMarket.title}
          </h2>
        </div>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {seasons.map((s) => (
            <div
              key={s.label}
              className={`rounded-2xl border border-line bg-gradient-to-br ${s.color} p-6`}
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                {s.label}
              </div>
              <p className="mt-4 text-sm leading-relaxed text-navy-2">
                {s.copy}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {moat.map((m) => (
            <div
              key={m.title}
              className="rounded-2xl border border-line bg-white p-6"
            >
              <h3 className="font-serif text-xl tracking-tight text-navy">
                {m.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-navy-2">
                {m.copy}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PricingSection({ t }: { t: T }) {
  const tiers = [
    {
      name: t.pricing.tier1Name,
      mx: t.pricing.tier1Mx,
      ca: t.pricing.tier1Ca,
      includes: t.pricing.tier1Includes,
      tag: t.pricing.tier1Tag,
    },
    {
      name: t.pricing.tier2Name,
      mx: t.pricing.tier2Mx,
      ca: t.pricing.tier2Ca,
      includes: t.pricing.tier2Includes,
      tag: t.pricing.tier2Tag,
    },
    {
      name: t.pricing.tier3Name,
      mx: t.pricing.tier3Mx,
      ca: t.pricing.tier3Ca,
      includes: t.pricing.tier3Includes,
      tag: t.pricing.tier3Tag,
    },
    {
      name: t.pricing.tier4Name,
      mx: t.pricing.tier4Mx,
      ca: t.pricing.tier4Ca,
      includes: t.pricing.tier4Includes,
      tag: t.pricing.tier4Tag,
    },
  ];
  return (
    <section
      id="pricing"
      className="border-b border-line/70 bg-cream py-24 md:py-28"
    >
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="md:col-span-6">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
              {t.pricing.eyebrow}
            </span>
            <h2 className="mt-3 font-serif text-4xl tracking-tight text-navy md:text-5xl">
              {t.pricing.title}
            </h2>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-navy-2 md:text-lg">
              {t.pricing.body}
            </p>
          </div>
          <aside className="md:col-span-6 self-end rounded-2xl border border-green/40 bg-green/[0.06] p-6 md:p-8">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-green font-semibold">
              {t.pricing.foundingBadge}
            </span>
            <h3 className="mt-2 font-serif text-2xl tracking-tight text-navy md:text-3xl">
              {t.pricing.foundingTitle}
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-navy-2">
              {t.pricing.foundingBody}
            </p>
          </aside>
        </div>

        <div className="mt-12 overflow-hidden rounded-2xl border border-line bg-white shadow-[var(--shadow-soft)]">
          <table className="w-full border-collapse text-sm">
            <thead className="bg-cream-2/60 text-left font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
              <tr>
                <th className="px-5 py-3 font-medium">{t.pricing.colTier}</th>
                <th className="px-5 py-3 font-medium">{t.pricing.colMx}</th>
                <th className="px-5 py-3 font-medium">{t.pricing.colCa}</th>
                <th className="px-5 py-3 font-medium">{t.pricing.colIncludes}</th>
              </tr>
            </thead>
            <tbody>
              {tiers.map((tier) => (
                <tr key={tier.name} className="border-t border-line align-top">
                  <td className="px-5 py-4">
                    <div className="font-serif text-2xl font-medium text-navy">
                      {tier.name}
                    </div>
                    <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                      {tier.tag}
                    </div>
                  </td>
                  <td className="px-5 py-4 font-mono text-base font-semibold text-navy">
                    {tier.mx}
                  </td>
                  <td className="px-5 py-4 font-mono text-base font-semibold text-navy">
                    {tier.ca}
                  </td>
                  <td className="px-5 py-4 leading-relaxed text-navy-2">
                    {tier.includes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-8 grid gap-4 text-sm md:grid-cols-3">
          <div className="rounded-xl border border-line bg-white p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.pricing.arpuLabel}
            </div>
            <div className="mt-2 font-serif text-3xl font-medium text-navy">
              {t.pricing.arpuValue}
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              {t.pricing.arpuSub}
            </p>
          </div>
          <div className="rounded-xl border border-line bg-white p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.pricing.cacLabel}
            </div>
            <div className="mt-2 font-serif text-3xl font-medium text-navy">
              {t.pricing.cacValue}
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              {t.pricing.cacSub}
            </p>
          </div>
          <div className="rounded-xl border border-line bg-white p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.pricing.paybackLabel}
            </div>
            <div className="mt-2 font-serif text-3xl font-medium text-navy">
              {t.pricing.paybackValue}
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              {t.pricing.paybackSub}
            </p>
          </div>
        </div>

        <div className="mt-10 rounded-2xl border border-line bg-navy p-6 text-cream md:p-8">
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-cream/60">
            {t.pricing.pilotBadge}
          </span>
          <p className="mt-3 text-sm leading-relaxed text-cream/85">
            {t.pricing.pilotTitle}
          </p>
          <p className="mt-5 max-w-3xl text-xs text-cream/65 leading-relaxed">
            {t.pricing.sources}
          </p>
        </div>
      </div>
    </section>
  );
}


function LaunchPlanSection({ lang, t }: { lang: Lang; t: T }) {
  const phases = [
    { label: t.launch.phase1Label, radius: t.launch.phase1Radius, copy: t.launch.phase1Copy },
    { label: t.launch.phase2Label, radius: t.launch.phase2Radius, copy: t.launch.phase2Copy },
    { label: t.launch.phase3Label, radius: t.launch.phase3Radius, copy: t.launch.phase3Copy },
  ];
  return (
    <section
      id="launch"
      className="border-b border-line/70 bg-cream py-24 md:py-28"
    >
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="md:col-span-7">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
              {t.launch.eyebrow}
            </span>
            <h2 className="mt-3 font-serif text-4xl tracking-tight text-navy md:text-5xl">
              {t.launch.title}
            </h2>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-navy-2 md:text-lg">
              {t.launch.body}
            </p>
          </div>
          <ul className="md:col-span-5 grid gap-3 self-end">
            {phases.map((phase) => (
              <li
                key={phase.label}
                className="rounded-xl border border-line bg-white p-4"
              >
                <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.18em]">
                  <span className="text-green">{phase.label}</span>
                  <span className="text-muted">{phase.radius}</span>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-navy-2">
                  {phase.copy}
                </p>
              </li>
            ))}
          </ul>
        </div>
        <div className="mt-12">
          <EmbedCard
            src="/mockups/launch-diagram/index.html"
            title={t.launch.mockupTitle}
            badge={t.launch.mockupBadge}
            aspectRatio="16 / 9"
          />
          <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
            {t.launch.mockupCaption}
          </p>
        </div>
      </div>
    </section>
  );
}

function InvestorsSection({ t }: { t: T }) {
  const arr = [
    { y: "Y1", ca: "1,000 ac · 4 customers", mx: "5 farms · 125 ha", arr: "$145K" },
    { y: "Y2", ca: "6,250 ac · 25 customers", mx: "25 farms · 625 ha", arr: "$862K" },
    { y: "Y3", ca: "20,000 ac · 80 customers", mx: "60 farms · 1,500 ha", arr: "$2.64M" },
    { y: "Y4", ca: "45,000 ac · 180 customers", mx: "100 farms · 2,500 ha", arr: "$5.71M" },
    { y: "Y5", ca: "80,000 ac · 320 customers", mx: "160 farms · 4,000 ha", arr: "$10–15M" },
  ];
  const useOfFunds = [
    { pct: "45%", line: "Personnel — 3 founders + agronomist contractor (18 mo)" },
    { pct: "25%", line: "Sales & marketing — 10× prior plan, trade shows, direct, field days" },
    { pct: "17%", line: "Hardware — drone fleet (substantially offset by FODECIJAL match)" },
    { pct: "8%", line: "Legal · incorporation · RPAS certs" },
    { pct: "5%", line: "Pilot operations · field travel · insurance" },
  ];
  const fundingStack = [
    { ar: "🇲🇽 FODECIJAL 2026 (Modalidad C)", note: "up to $2.5M MXN · TRL 3→4 · final May 14" },
    { ar: "🇲🇽 Impulsora de Innovación", note: "up to $6M MXN seed co-investment · Sept window" },
    { ar: "🇨🇦 NRC-IRAP", note: "up to $500K (subject to ITA verification) · clean tech stream" },
    { ar: "🇨🇦 CAAIN Smart Farms", note: "up to $3M / project · $9M pool · 4 deadlines through Oct 2026" },
    { ar: "🇨🇦 NSERC Alliance", note: "2:1 matching · rolling intake · requires university PI" },
    { ar: "🇨🇦 SR&ED", note: "35%+ refundable · enhanced cap raised $3M → $6M (Budget 2025)" },
  ];
  const milestones = [
    "CultivOS México S.A. de C.V. operational + FODECIJAL/Impulsora landed",
    "CultivOS Canada Inc. incorporated + NRC-IRAP secured",
    "Cerebro v1 in-field with farmers (not architecture-only)",
    "4 paid Ontario pilots → 25 paying customers by Y1 close",
    "Outdoor Farm Show launch (Sept 2026) + Founding-100 program live",
    "ARR run-rate: $145K → trajectory to $862K Y2",
  ];
  return (
    <section
      id="where-we-are"
      className="border-b border-line/70 bg-cream-2/40 py-24 md:py-28"
    >
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="flex flex-col gap-3">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {t.investors.eyebrow}
          </span>
          <h2 className="max-w-3xl font-serif text-4xl tracking-tight text-navy md:text-5xl">
            {t.investors.title}
          </h2>
          <p className="mt-2 max-w-3xl text-base leading-relaxed text-navy-2 md:text-lg">
            {t.investors.body} <b>{t.investors.bodyBold}</b>{t.investors.bodyEnd}
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-line bg-white p-6">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.investors.milestonesLabel}
            </span>
            <ul className="mt-4 space-y-3 text-sm text-navy-2">
              {milestones.map((m) => (
                <li key={m} className="flex items-start gap-3 leading-relaxed">
                  <span className="mt-2 h-1 w-3 flex-shrink-0 rounded-full bg-green" />
                  <span>{m}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-line bg-white p-6">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.investors.fundsLabel}
            </span>
            <ul className="mt-4 space-y-3 text-sm text-navy-2">
              {useOfFunds.map((u) => (
                <li key={u.line} className="flex items-start gap-3">
                  <span className="font-mono text-base font-semibold text-navy w-12 flex-shrink-0">
                    {u.pct}
                  </span>
                  <span className="leading-relaxed">{u.line}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 overflow-hidden rounded-2xl border border-line bg-white">
          <div className="flex items-center justify-between bg-cream-2/60 px-5 py-3">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
              {t.investors.arrLabel}
            </span>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
              {t.investors.arrExit}
            </span>
          </div>
          <table className="w-full border-collapse text-sm">
            <thead className="text-left font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
              <tr className="border-t border-line">
                <th className="px-5 py-3 font-medium">{t.investors.colYear}</th>
                <th className="px-5 py-3 font-medium">{t.investors.colCanada}</th>
                <th className="px-5 py-3 font-medium">{t.investors.colMexico}</th>
                <th className="px-5 py-3 font-medium text-right">{t.investors.colArr}</th>
              </tr>
            </thead>
            <tbody>
              {arr.map((row) => (
                <tr key={row.y} className="border-t border-line align-top">
                  <td className="px-5 py-3 font-mono text-base font-semibold text-navy">
                    {row.y}
                  </td>
                  <td className="px-5 py-3 leading-relaxed text-navy-2">
                    {row.ca}
                  </td>
                  <td className="px-5 py-3 leading-relaxed text-navy-2">
                    {row.mx}
                  </td>
                  <td className="px-5 py-3 text-right font-mono text-base font-semibold text-green">
                    {row.arr}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-10">
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
            {t.investors.ndLabel}
          </span>
          <ul className="mt-4 grid gap-3 md:grid-cols-2">
            {fundingStack.map((f) => (
              <li
                key={f.ar}
                className="rounded-xl border border-line bg-white p-4 text-sm leading-relaxed text-navy-2"
              >
                <div className="font-semibold text-navy">{f.ar}</div>
                <div className="mt-1 text-xs text-muted">{f.note}</div>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-12 rounded-2xl border border-navy bg-navy p-6 text-cream md:p-8">
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-cream/60">
            {t.investors.pillarsLabel}
          </span>
          <h3 className="mt-2 font-serif text-2xl tracking-tight text-cream md:text-3xl">
            {t.investors.pillarsTitle}
          </h3>
          <div className="mt-6 grid gap-6 md:grid-cols-3 text-sm leading-relaxed text-cream/85">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                {t.investors.pillar1Label}
              </div>
              <p className="mt-2">{t.investors.pillar1Body}</p>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                {t.investors.pillar2Label}
              </div>
              <p className="mt-2">
                {t.investors.pillar2ConfirmedLabel} <b>ITESO</b> (Guadalajara) and <b>PLAi</b> (GDL university dept). <b>UWaterloo</b> via CTO Mubeen Zulfiqar (alumni). NSERC Alliance unlocks once a Canadian university Principal Investigator (PI) signs on — open to McMaster, Guelph, Waterloo and others.
              </p>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                {t.investors.pillar3Label}
              </div>
              <p className="mt-2">{t.investors.pillar3Body}</p>
            </div>
          </div>
          <a
            href="mailto:hola@cultivosagro.com"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-green px-6 py-3 text-sm font-semibold text-cream transition-colors hover:bg-green-700"
          >
            {t.investors.ctaLabel}
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M3 7h8M7.5 3.5L11 7l-3.5 3.5"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}

function TeamSection({ t, lang }: { t: T; lang: Lang }) {
  const isEs = lang === "es";
  const team = [
    {
      name: "Sebastián Sánchez García",
      role: "CEO & Product",
      city: "Hamilton, ON · dual citizen MX / CA PR",
      bullets: [
        "16 years in food production — field operations to commercial kitchen systems",
        "UX-first farmer technology · operational workflow depth · adoption-barrier instinct",
        "Connects agricultural reality to product clarity",
      ],
    },
    {
      name: "Mubeen Zulfiqar",
      role: "CTO",
      city: "Toronto, ON",
      bullets: [
        "MMath Computer Science · University of Waterloo (Buhr Programming Languages group)",
        "7 publications · Boutaba networking group · CNSM 2019 Best Paper Award",
        "Director, DevGate Canada · ships infrastructure systems prototype to production",
      ],
    },
    {
      name: "Víctor Hernández Quintana",
      role: "Director, Mexico Operations",
      city: "Guadalajara, MX",
      bullets: [
        "Former CONAGUA infrastructure builder · public-sector execution track record",
        "Operates 5-state agricultural logistics network across western Mexico",
        "Pursuing AFAC RPAS pilot certification · grounds Mexican field ops in local relationships",
      ],
    },
  ];

  const teamEs = [
    {
      name: "Sebastián Sánchez García",
      role: "CEO & Producto",
      city: "Hamilton, ON · ciudadanía dual MX / PR CA",
      bullets: [
        "16 años en producción de alimentos — operaciones de campo a sistemas de cocina comercial",
        "Tecnología agrícola centrada en UX · profundidad en flujos operativos · instinto para barreras de adopción",
        "Conecta la realidad del campo con la claridad del producto",
      ],
    },
    {
      name: "Mubeen Zulfiqar",
      role: "CTO",
      city: "Toronto, ON",
      bullets: [
        "MMath Ciencias de la Computación · Universidad de Waterloo (grupo Buhr de Lenguajes de Programación)",
        "7 publicaciones · grupo de redes Boutaba · Premio al Mejor Artículo CNSM 2019",
        "Director, DevGate Canada · lleva sistemas de infraestructura de prototipo a producción",
      ],
    },
    {
      name: "Víctor Hernández Quintana",
      role: "Director de Operaciones México",
      city: "Guadalajara, MX",
      bullets: [
        "Ex constructor de infraestructura CONAGUA · historial de ejecución en sector público",
        "Opera red de logística agrícola de 5 estados en el occidente de México",
        "En proceso de certificación RPAS AFAC · ancla las operaciones de campo con relaciones locales",
      ],
    },
  ];

  const members = isEs ? teamEs : team;

  return (
    <section
      id="team"
      className="border-b border-line/70 bg-cream py-24 md:py-28"
    >
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
          {t.team.eyebrow}
        </span>
        <h2 className="mt-3 max-w-3xl font-serif text-4xl tracking-tight text-navy md:text-5xl">
          {t.team.title}
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {members.map((m) => (
            <article
              key={m.name}
              className="rounded-2xl border border-line bg-white p-6 shadow-[var(--shadow-soft)]"
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-green">
                {m.role}
              </div>
              <h3 className="mt-3 font-serif text-2xl tracking-tight text-navy">
                {m.name}
              </h3>
              <div className="mt-1 font-mono text-[11px] text-muted">
                {m.city}
              </div>
              <ul className="mt-4 space-y-2 text-sm leading-relaxed text-navy-2">
                {m.bullets.map((b, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="mt-2 h-1 w-3 flex-shrink-0 rounded-full bg-green" />
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <p className="mt-8 max-w-3xl text-sm leading-relaxed text-muted">
          {t.team.footer}
        </p>
      </div>
    </section>
  );
}

function ContactStrip({ lang }: { lang: Lang }) {
  const isEs = lang === "es";
  return (
    <section className="bg-navy py-16 text-cream">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 md:flex-row md:items-end md:justify-between md:px-10">
        <div className="max-w-2xl">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-cream/60">
            {isEs ? "Hablemos" : "Let's talk"}
          </span>
          <h2 className="mt-3 font-serif text-3xl tracking-tight text-cream md:text-5xl">
            {isEs
              ? "Hecho en México. Listos para inversionistas, socios académicos y mentores."
              : "Built in Mexico. Open to investors, academic partners, and operator mentors."}
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-cream/70 md:text-base">
            {isEs
              ? "30 minutos. Te mostramos los pilotos, los números y los huecos donde tu experiencia mueve más la aguja."
              : "30 minutes. We walk you through the pilots, the numbers, and the gaps where your experience moves the needle most."}
          </p>
        </div>
        <div className="flex flex-col gap-3">
          <a
            href="mailto:hola@cultivosagro.com"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-green px-6 py-3 text-sm font-semibold text-cream transition-colors hover:bg-green-700"
          >
            hola@cultivosagro.com
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M3 7h8M7.5 3.5L11 7l-3.5 3.5"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>
          <a
            href="https://cultivosagro.com"
            className="text-center font-mono text-[11px] uppercase tracking-[0.18em] text-cream/60 hover:text-cream"
          >
            cultivosagro.com
          </a>
        </div>
      </div>
    </section>
  );
}

function SiteFooter({ lang }: { lang: Lang }) {
  return (
    <footer className="border-t border-line bg-cream py-10 text-xs text-muted">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 md:flex-row md:items-center md:justify-between md:px-10">
        <span className="font-mono uppercase tracking-[0.18em]">
          {lang === "es"
            ? "cultivOS · v1.0 · para discusión"
            : "cultivOS · v1.0 · for discussion"}
        </span>
        <span>
          {lang === "es"
            ? "Hamilton, ON · Toronto, ON · Guadalajara, MX"
            : "Hamilton, ON · Toronto, ON · Guadalajara, MX"}
        </span>
      </div>
    </footer>
  );
}
