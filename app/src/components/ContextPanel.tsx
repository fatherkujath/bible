"use client";

import { useEffect, useMemo, useState } from "react";
import type { Chapter } from "@/lib/types";
import { PeopleTab, PlacesTab, TermsTab, TextTab, WorldTab, XrefTab } from "./tabs";

const TABS = [
  { id: "text", label: "Text" },
  { id: "world", label: "World" },
  { id: "places", label: "Places" },
  { id: "people", label: "People" },
  { id: "terms", label: "Culture and terms" },
  { id: "xrefs", label: "Cross-references" },
] as const;
type TabId = (typeof TABS)[number]["id"];

export function ContextPanel({ chapter, focus, onClearFocus }: { chapter: Chapter; focus: number | null; onClearFocus: () => void }) {
  const [tab, setTab] = useState<TabId>("world");
  const [open, setOpen] = useState(false); // phone bottom sheet

  // Selecting a verse opens the sheet on phones and shows its words.
  useEffect(() => {
    if (focus !== null) { setOpen(true); setTab((t) => (t === "world" ? "text" : t)); }
  }, [focus]);

  const inFocus = (vs: number[]) => focus === null || vs.includes(focus);
  const counts = useMemo<Record<TabId, number | null>>(() => ({
    text: null,
    world: null,
    places: chapter.places.filter((p) => inFocus(p.verses)).length,
    people: chapter.people.filter((p) => inFocus(p.verses)).length + chapter.names.filter((p) => inFocus(p.verses)).length,
    terms: chapter.terms.filter((t) => inFocus(t.verses)).length,
    xrefs: focus === null
      ? Object.values(chapter.xrefs).reduce((n, l) => n + l.length, 0)
      : (chapter.xrefs[String(focus)]?.length ?? 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [chapter, focus]);

  return (
    <aside aria-label="Context" data-open={open}
      className="sheet bg-page lg:mt-4 lg:rounded-lg lg:border lg:border-stone-soft lg:sticky lg:top-[4.5rem] lg:max-h-[calc(100vh-5.5rem)] flex flex-col">
      <button type="button" className="lg:hidden flex flex-col items-center pt-2 pb-1 w-full" aria-expanded={open}
        onClick={() => setOpen((o) => !o)}>
        <span className="block w-10 h-1 rounded-full bg-stone" aria-hidden="true" />
        <span className="text-sm text-muted mt-1">{open ? "Hide context" : focus !== null ? `Context for verse ${focus}` : "Show context"}</span>
      </button>
      <div role="tablist" aria-label="Context layers" className="flex flex-wrap border-b border-stone-soft px-2 shrink-0">
        {TABS.map((t) => (
          <button key={t.id} role="tab" id={`tab-${t.id}`} aria-selected={tab === t.id} aria-controls={`panel-${t.id}`}
            className="panel-tab" onClick={() => { setTab(t.id); setOpen(true); }}>
            {t.label}
            {counts[t.id] !== null && <span className="count">{counts[t.id]}</span>}
          </button>
        ))}
      </div>
      <div className="px-4 pb-6 pt-2 overflow-y-auto grow" role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
        <div className="flex items-baseline justify-between py-2 text-sm text-muted">
          <span>{focus === null ? "Whole chapter" : `Verse ${focus}`}</span>
          {focus !== null && <button type="button" className="underline" onClick={onClearFocus}>Show whole chapter</button>}
        </div>
        {tab === "text" && <TextTab chapter={chapter} focus={focus} />}
        {tab === "world" && <WorldTab chapter={chapter} focus={focus} />}
        {tab === "places" && <PlacesTab chapter={chapter} focus={focus} />}
        {tab === "people" && <PeopleTab chapter={chapter} focus={focus} />}
        {tab === "terms" && <TermsTab chapter={chapter} focus={focus} />}
        {tab === "xrefs" && <XrefTab chapter={chapter} focus={focus} />}
      </div>
    </aside>
  );
}
