"use client";

import { useEffect, useState } from "react";

type EmbedCardProps = {
  src: string;
  title: string;
  subtitle?: string;
  badge?: string;
  aspectRatio?: string;
  className?: string;
};

export function EmbedCard({
  src,
  title,
  subtitle,
  badge,
  aspectRatio = "16 / 9",
  className = "",
}: EmbedCardProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <article
        className={`overflow-hidden rounded-2xl border border-line bg-white shadow-[var(--shadow-soft)] ${className}`}
      >
        <div className="flex items-center justify-between border-b border-line bg-cream-2/60 px-4 py-2 text-[11px] font-mono uppercase tracking-[0.16em] text-muted">
          <span>{badge ?? title}</span>
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-[10px] font-medium text-green hover:bg-green-100"
          >
            Expand
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path
                d="M2 6v2h2M8 4V2H6M2 8l3-3M8 2L5 5"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
        <div
          className="relative w-full overflow-hidden bg-cream-2/30"
          style={{ aspectRatio }}
        >
          <iframe
            src={src}
            title={title}
            className="absolute inset-0 h-full w-full"
            loading="lazy"
          />
        </div>
        {subtitle ? (
          <div className="px-4 py-4">
            <p className="text-sm font-medium text-navy">{title}</p>
            <p className="mt-1 text-xs leading-relaxed text-muted">{subtitle}</p>
          </div>
        ) : null}
      </article>

      <EmbedModal open={open} src={src} title={title} onClose={() => setOpen(false)} />
    </>
  );
}

type EmbedModalProps = {
  open: boolean;
  src: string;
  title: string;
  onClose: () => void;
};

function EmbedModal({ open, src, title, onClose }: EmbedModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-navy/80 p-4 backdrop-blur-sm md:p-8"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className="relative h-full max-h-[96vh] w-full max-w-[96vw] overflow-hidden rounded-2xl border border-line bg-cream shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line bg-white px-4 py-3">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
            {title}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1.5 text-xs font-medium text-navy hover:bg-cream-2"
            aria-label="Close preview"
          >
            Close
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
              <path
                d="M2 2l7 7M9 2l-7 7"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
        <iframe
          src={src}
          title={`${title} expanded`}
          className="block h-[calc(96vh-49px)] w-full bg-cream"
        />
      </div>
    </div>
  );
}
