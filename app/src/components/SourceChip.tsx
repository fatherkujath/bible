"use client";

import { useId, useState } from "react";
import { useAppData } from "./AppProviders";

/**
 * Small, quiet chip on every card. Opens the citation: dataset, license,
 * pinned version, upstream record id, and a link to the source.
 */
export function SourceChip({ src, rec, url, label }: { src: string; rec: string; url?: string | null; label?: string }) {
  const { sources } = useAppData();
  const [open, setOpen] = useState(false);
  const id = useId();
  const s = sources[src];
  return (
    <span className="inline-block">
      <button type="button" className="chip" aria-expanded={open} aria-controls={id} onClick={() => setOpen((o) => !o)}>
        {label ?? "source"}
      </button>
      {open && (
        <span id={id} role="note" className="block mt-2 p-3 rounded-md border border-stone bg-vellum text-[0.8125rem] leading-relaxed">
          <span className="block font-bold">{s?.name ?? src}</span>
          <span className="block text-muted">{s?.license}</span>
          <span className="block mt-1">{s?.attribution}</span>
          <span className="block mt-1 text-muted break-all">Record: {rec}</span>
          {s?.commit && <span className="block text-muted">Version: {s.commit.slice(0, 12)}</span>}
          <span className="flex flex-wrap gap-3 mt-1">
            {url && <a className="underline" href={url} target="_blank" rel="noreferrer">View this record</a>}
            {s?.homepage && <a className="underline" href={s.homepage} target="_blank" rel="noreferrer">Source homepage</a>}
            <a className="underline" href="/attributions/">All sources</a>
          </span>
        </span>
      )}
    </span>
  );
}
