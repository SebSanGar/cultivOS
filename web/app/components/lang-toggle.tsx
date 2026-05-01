"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

type Lang = "en" | "es";

export function LangToggle({ current }: { current: Lang }) {
  const pathname = usePathname();
  const params = useSearchParams();

  const buildHref = (lang: Lang) => {
    const sp = new URLSearchParams(params?.toString() ?? "");
    if (lang === "en") sp.delete("lang");
    else sp.set("lang", "es");
    const qs = sp.toString();
    return qs ? `${pathname}?${qs}` : pathname;
  };

  const baseClass =
    "rounded-full px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] transition-colors";
  const activeClass = "bg-navy text-cream";
  const inactiveClass = "text-muted hover:text-navy";

  return (
    <div className="inline-flex items-center gap-1 rounded-full border border-line bg-white/70 p-1">
      <Link
        href={buildHref("en")}
        className={`${baseClass} ${current === "en" ? activeClass : inactiveClass}`}
        aria-pressed={current === "en"}
        prefetch={false}
      >
        EN
      </Link>
      <Link
        href={buildHref("es")}
        className={`${baseClass} ${current === "es" ? activeClass : inactiveClass}`}
        aria-pressed={current === "es"}
        prefetch={false}
      >
        ES
      </Link>
    </div>
  );
}
