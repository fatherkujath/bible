"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { loadChapter } from "@/lib/data";
import { chapterHref, chapterLabel } from "@/lib/refs";
import type { Chapter } from "@/lib/types";
import { ContextPanel } from "./ContextPanel";
import { TopBar } from "./TopBar";

const LAST_READ = "sic-last-read";

export function Reader({ id }: { id: string }) {
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [focus, setFocus] = useState<number | null>(null);
  const [openNotes, setOpenNotes] = useState<Set<number>>(new Set());

  useEffect(() => {
    let live = true;
    setChapter(null);
    setError(null);
    loadChapter(id)
      .then((c) => { if (live) setChapter(c); })
      .catch(() => { if (live) setError("This chapter could not be loaded. Check your connection and reload the page."); });
    try { localStorage.setItem(LAST_READ, id); } catch {}
    return () => { live = false; };
  }, [id]);

  // Verse focus lives in the URL hash (#v16) so it can be linked and survives reload.
  useEffect(() => {
    const read = () => {
      const m = /^#v(\d+)$/.exec(window.location.hash);
      setFocus(m ? Number(m[1]) : null);
    };
    read();
    window.addEventListener("hashchange", read);
    return () => window.removeEventListener("hashchange", read);
  }, [id]);

  useEffect(() => {
    if (chapter && focus !== null) {
      const phone = window.matchMedia("(max-width: 1023px)").matches;
      document.getElementById(`v${focus}`)?.scrollIntoView({ block: phone ? "start" : "center" });
    }
    // Scroll only when the chapter first arrives, not on every focus change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapter]);

  const toggleFocus = useCallback((n: number) => {
    setFocus((cur) => {
      const next = cur === n ? null : n;
      const url = `${window.location.pathname}${next !== null ? `#v${next}` : ""}`;
      window.history.replaceState(null, "", url);
      if (next !== null && window.matchMedia("(max-width: 1023px)").matches) {
        // Keep the chosen verse visible above the bottom sheet.
        requestAnimationFrame(() => document.getElementById(`v${next}`)?.scrollIntoView({ block: "start" }));
      }
      return next;
    });
  }, []);

  // Margin marks: which verses have a named person, a located place, or a dictionary article.
  const marks = useMemo(() => {
    const m = new Map<number, { person: boolean; place: boolean; term: boolean }>();
    if (!chapter) return m;
    const get = (n: number) => m.get(n) ?? m.set(n, { person: false, place: false, term: false }).get(n)!;
    chapter.people.forEach((p) => p.verses.forEach((v) => (get(v).person = true)));
    chapter.places.forEach((p) => p.verses.forEach((v) => (get(v).place = true)));
    chapter.terms.forEach((t) => t.verses.forEach((v) => (get(v).term = true)));
    return m;
  }, [chapter]);

  const title = chapterLabel(id);

  return (
    <>
      <TopBar current={id} prev={chapter?.prev ?? null} next={chapter?.next ?? null} />
      <div className="mx-auto max-w-[78rem] lg:grid lg:grid-cols-[minmax(0,1fr)_26rem] lg:gap-8 px-3 sm:px-6 pb-40 lg:pb-12">
        <main id="main" className="bg-page rounded-lg mt-4 px-3 sm:px-8 py-6 sm:py-10 border border-stone-soft">
          <h1 className="font-serif text-[2rem] leading-tight mb-6 pl-[3.5rem]">{title}</h1>
          {error && <p className="empty pl-[3.5rem]">{error}</p>}
          {!chapter && !error && <p className="loading empty pl-[3.5rem]" role="status">Loading {title}…</p>}
          {chapter && (
            <div className="scripture max-w-[40rem]">
              {chapter.verses.map((v) => {
                const mk = marks.get(v.n);
                const isTitle = v.n === 0;
                return (
                  <div key={v.ref}>
                    {v.h.map((h, i) => (
                      <h2 key={i} className={`heading pl-[3.5rem] ${h.kind === "acrostic" ? "italic" : ""}`}>{h.text}</h2>
                    ))}
                    {isTitle ? (
                      <p id="v0" className="superscription pl-[3.5rem]">
                        {v.text}
                        {v.notes.length > 0 && <NoteToggle n={0} open={openNotes} setOpen={setOpenNotes} />}
                      </p>
                    ) : (
                      <div id={`v${v.n}`} className={`verse ${focus === v.n ? "is-focused" : ""}`}>
                        <span className="marks" aria-hidden="true">
                          {mk?.person && <span className="mark" title="Named person" />}
                          {mk?.place && <span className="mark ring" title="Place with location data" />}
                          {mk?.term && <span className="mark bar" title="Dictionary article" />}
                        </span>
                        <button type="button" className="verse-num" aria-pressed={focus === v.n}
                          aria-label={`Verse ${v.n}${focus === v.n ? ", selected" : ""}. Show its context`}
                          onClick={() => toggleFocus(v.n)}>
                          {v.n}
                        </button>
                        <span>
                          {v.text}
                          {v.notes.length > 0 && <NoteToggle n={v.n} open={openNotes} setOpen={setOpenNotes} />}
                        </span>
                      </div>
                    )}
                    {openNotes.has(v.n) && v.notes.map((t, i) => (
                      <p key={i} className="footnote ml-[3.5rem]">{t}</p>
                    ))}
                  </div>
                );
              })}
              <nav aria-label="Chapter navigation" className="flex justify-between mt-10 pl-[3.5rem] font-sans text-sm">
                {chapter.prev ? <Link href={chapterHref(chapter.prev)} className="underline">{chapterLabel(chapter.prev)}</Link> : <span />}
                {chapter.next ? <Link href={chapterHref(chapter.next)} className="underline">{chapterLabel(chapter.next)}</Link> : <span />}
              </nav>
              <p className="meta mt-8 pl-[3.5rem] font-sans">
                Margin marks show where context exists: <span className="mark inline-block align-middle" /> a named person,{" "}
                <span className="mark ring inline-block align-middle" /> a place with location data,{" "}
                <span className="mark bar inline-block align-middle" /> a dictionary article. Text: Berean Standard Bible (public domain).
              </p>
            </div>
          )}
        </main>
        {chapter && <ContextPanel chapter={chapter} focus={focus} onClearFocus={() => toggleFocus(focus ?? -1)} />}
      </div>
    </>
  );
}

function NoteToggle({ n, open, setOpen }: { n: number; open: Set<number>; setOpen: (s: Set<number>) => void }) {
  const isOpen = open.has(n);
  return (
    <button type="button" className="note-btn" aria-expanded={isOpen}
      aria-label={isOpen ? "Hide translator's note" : "Show translator's note"}
      onClick={() => { const s = new Set(open); if (isOpen) s.delete(n); else s.add(n); setOpen(s); }}>
      note
    </button>
  );
}
