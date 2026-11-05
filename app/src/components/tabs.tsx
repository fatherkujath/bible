"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Fragment, useState } from "react";
import { loadChapter, loadEaston } from "@/lib/data";
import { formatRange, parseRef, refHref, splitPlaceName, tipnrName, verseList, yearLabel } from "@/lib/refs";
import type { Chapter, EastonArticle, Identification, LexEntry, OriginalWord } from "@/lib/types";
import { SourceChip } from "./SourceChip";

const MiniMap = dynamic(() => import("./MiniMap"), { ssr: false, loading: () => <div className="h-56 rounded-md bg-stone-soft" /> });

type TabProps = { chapter: Chapter; focus: number | null };
const NONE = "No sourced material yet.";

function inFocus(vs: number[], focus: number | null) {
  return focus === null || vs.includes(focus);
}

// ---------------------------------------------------------------- Text
function rootTags(tag: string | null): string[] {
  if (!tag) return [];
  const roots = [...tag.matchAll(/\{([HG]\d{4}[A-Za-z]?)\}/g)].map((m) => m[1]);
  const all = [...tag.matchAll(/[HG]\d{4}[A-Za-z]?/g)].map((m) => m[0]);
  return [...roots, ...all.filter((t) => !roots.includes(t))];
}

function lexFor(chapter: Chapter, keys: string[]): LexEntry | undefined {
  for (const k of keys) if (chapter.lex[k]) return chapter.lex[k];
  return undefined;
}

export function TextTab({ chapter, focus }: TabProps) {
  if (focus === null) {
    return <p className="empty">Choose a verse number in the text to see its Hebrew or Greek words, with Strong’s numbers and glosses.</p>;
  }
  const verse = chapter.verses.find((v) => v.n === focus);
  const originals = chapter.original.filter((o) => o.kjv.includes(focus));
  return (
    <div>
      <section className="card">
        <h3 className="card-title">Original words</h3>
        {originals.length === 0 && <p className="empty">{NONE}</p>}
        {originals.map((o) => {
          const pr = parseRef(o.org);
          const differs = pr && (pr.chapter !== chapter.chapter || pr.verse !== focus);
          return (
            <div key={o.org} className="mt-3">
              {differs && <p className="meta mb-1">{o.lang} numbering: {formatRange(o.org, o.org)}</p>}
              <div dir={o.lang === "Hebrew" ? "rtl" : "ltr"} className="flex flex-wrap gap-x-4 gap-y-3">
                {o.words.map((w) => <OriginalWordCard key={w.rec} w={w} lang={o.lang} lex={lexFor(chapter, rootTags(w.s))} />)}
              </div>
              <p className="mt-3"><SourceChip src="stepbible" rec={o.words[0]?.rec.split("#")[0] ?? o.org} /></p>
            </div>
          );
        })}
      </section>
      {verse && verse.w.length > 0 && (
        <section className="card">
          <h3 className="card-title">How the BSB translates them</h3>
          <table className="w-full text-sm mt-2">
            <thead className="text-left text-muted">
              <tr><th className="font-normal py-1 pr-2">English</th><th className="font-normal py-1 pr-2">Strong’s</th><th className="font-normal py-1">Gloss</th></tr>
            </thead>
            <tbody>
              {verse.w.map((w, i) => {
                const lex = lexFor(chapter, w.slice(4) as string[]);
                return (
                  <tr key={i} className="border-t border-stone-soft align-top">
                    <td className="py-1 pr-2 font-serif">{w[0] ?? <span className="text-muted">(not translated)</span>}</td>
                    <td className="py-1 pr-2 text-muted whitespace-nowrap">{w[1]}</td>
                    <td className="py-1">{lex?.gloss ?? ""}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="mt-3 flex gap-2 flex-wrap">
            <SourceChip src="bsb" rec={verse.rec} label="BSB alignment" />
            <SourceChip src="stepbible" rec="TBESH/TBESG glosses" label="glosses" />
          </p>
        </section>
      )}
    </div>
  );
}

function OriginalWordCard({ w, lang, lex }: { w: OriginalWord; lang: "Hebrew" | "Greek"; lex?: LexEntry }) {
  return (
    <span className="inline-flex flex-col items-center text-center min-w-[3.5rem]" dir="ltr">
      <span className={lang === "Hebrew" ? "hebrew" : "greek"} lang={lang === "Hebrew" ? "he" : "grc"}>{w.o.replaceAll("/", "").replaceAll("\\", "")}</span>
      {w.x && <span className="text-xs text-muted italic">{w.x}</span>}
      {w.g && <span className="text-[0.8125rem]">{w.g.replaceAll("/", "").replace(/<|>/g, "")}</span>}
      <span className="text-[0.6875rem] text-muted" title={lex ? `${lex.lemma} (${lex.tr ?? ""}): ${lex.gloss ?? ""}` : undefined}>
        {rootTags(w.s)[0] ?? ""}{w.m ? ` ${w.m}` : ""}
      </span>
    </span>
  );
}

// ---------------------------------------------------------------- World
export function WorldTab({ chapter, focus }: TabProps) {
  const years = chapter.world.years.filter((y) => inFocus(y.verses, focus));
  const events = chapter.world.events.filter((e) => inFocus(e.verses, focus));
  return (
    <div>
      <section className="card">
        <h3 className="card-title">When</h3>
        {years.length === 0 ? <p className="empty">{NONE}</p> : (
          <>
            <ul className="mt-1 text-[0.9375rem]">
              {years.map((y) => (
                <li key={y.year}><span className="font-bold">{yearLabel(y.year)}</span> <span className="text-muted">{focus === null ? verseList(y.verses) : ""}</span></li>
              ))}
            </ul>
            <p className="meta mt-2">Dates follow Theographic’s single chronology (Ussher-style). Other chronologies date these events differently.</p>
            <p className="mt-2"><SourceChip src="theographic" rec="verses.json yearNum" /></p>
          </>
        )}
      </section>
      <section className="card">
        <h3 className="card-title">Events</h3>
        {events.length === 0 ? <p className="empty">{NONE}</p> : events.map((e) => (
          <div key={e.id} className="mt-2">
            <p>{e.title}</p>
            <p className="meta">{e.start ? `Starts ${yearLabel(Number(e.start))} per Theographic. ` : ""}{verseList(e.verses)}</p>
            <SourceChip src={e.src} rec={e.rec} />
          </div>
        ))}
      </section>
      <section className="card">
        <h3 className="card-title">Rulers in power</h3>
        <p className="empty">{NONE}</p>
      </section>
      <section className="card">
        <h3 className="card-title">Study notes</h3>
        <p className="empty">{NONE}</p>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------- Places
export function confClass(conf: number | null): "high" | "medium" | "low" {
  if (conf !== null && conf >= 500) return "high";
  if (conf !== null && conf >= 100) return "medium";
  return "low";
}

function IdentificationRow({ id }: { id: Identification }) {
  const c = confClass(id.conf);
  return (
    <li className="flex gap-2 items-start py-1">
      <span className={`conf conf-${c} mt-1 shrink-0`} aria-hidden="true" />
      <span>
        {id.desc}
        <span className="meta block">
          {id.conf === null ? "No confidence score published" : `${Math.max(0, Math.round(id.conf / 10))}% confidence`}
          {id.lat === null ? ". No map point" : ""}
        </span>
      </span>
    </li>
  );
}

export function PlacesTab({ chapter, focus }: TabProps) {
  const places = chapter.places.filter((p) => inFocus(p.verses, focus));
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  if (places.length === 0) return <p className="empty">{NONE}</p>;
  return (
    <div>
      <MiniMap places={places} />
      <p className="meta mt-2">
        Confidence is OpenBible.info’s score for current scholarship. OpenBible treats 50% or higher as high confidence.
        <span className="whitespace-nowrap"> <span className="conf conf-high" /> 50% or more</span>
        <span className="whitespace-nowrap"> <span className="conf conf-medium" /> 10–49%</span>
        <span className="whitespace-nowrap"> <span className="conf conf-low" /> under 10%</span>
      </p>
      {places.map((p) => {
        const { base, n } = splitPlaceName(p.name);
        const all = expanded.has(p.id);
        const shown = all ? p.ids : p.ids.slice(0, 3);
        return (
          <article key={p.id} className="card">
            <h3 className="card-title">{base}{n && <span className="text-muted font-normal text-sm"> ({n})</span>}</h3>
            <p className="meta">{verseList(p.verses)}{p.types ? `. ${p.types.replaceAll(",", ", ")}` : ""}</p>
            <ul className="mt-1 text-[0.9375rem]">{shown.map((id) => <IdentificationRow key={id.rank} id={id} />)}</ul>
            {p.ids.length > 3 && (
              <button type="button" className="text-sm underline text-muted" onClick={() => {
                const s = new Set(expanded); if (all) s.delete(p.id); else s.add(p.id); setExpanded(s);
              }}>{all ? "Show fewer" : `Show all ${p.ids.length} proposed locations`}</button>
            )}
            <p className="mt-1"><SourceChip src={p.src} rec={p.rec} url={p.url} /></p>
          </article>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------- People
const REL_LABEL = { parent: "Parents", sibling: "Siblings", partner: "Spouses", offspring: "Children" } as const;

export function PeopleTab({ chapter, focus }: TabProps) {
  const people = chapter.people.filter((p) => inFocus(p.verses, focus));
  const names = chapter.names.filter((p) => inFocus(p.verses, focus));
  if (!people.length && !names.length) return <p className="empty">{NONE}</p>;
  return (
    <div>
      {people.map((p) => (
        <article key={p.id} className="card">
          <h3 className="card-title">{p.name}</h3>
          <p className="meta">{[p.type, verseList(p.verses)].filter(Boolean).join(". ")}</p>
          {(Object.keys(REL_LABEL) as (keyof typeof REL_LABEL)[]).filter((k) => p.rel[k]?.length).map((k) => (
            <p key={k} className="text-[0.9375rem]"><span className="text-muted">{REL_LABEL[k]}: </span>{p.rel[k]!.map(tipnrName).join(", ")}</p>
          ))}
          <p className="mt-1"><SourceChip src={p.src} rec={p.rec} /></p>
        </article>
      ))}
      {names.length > 0 && (
        <section className="card">
          <h3 className="card-title">Other names</h3>
          <ul className="text-[0.9375rem] mt-1">
            {names.map((p) => <li key={p.id}>{p.name} <span className="meta">{verseList(p.verses)}</span></li>)}
          </ul>
          <p className="mt-1"><SourceChip src="stepbible" rec="TIPNR" /></p>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Culture and terms
/** Easton's text, verbatim. Markdown scripture links become in-app links. */
function EastonBody({ body }: { body: string }) {
  const paras = body.split(/\n{2,}|\n/).filter((p) => p.trim());
  return (
    <div className="article mt-2">
      {paras.map((p, i) => (
        <p key={i}>
          {p.split(/(\[[^\]]+\]\([^)]+\))/g).map((part, j) => {
            const m = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(part);
            if (!m) return <Fragment key={j}>{part}</Fragment>;
            const ref = m[2].split("#")[1];
            return ref ? <Link key={j} href={refHref(ref)} className="underline">{m[1]}</Link> : <Fragment key={j}>{m[1]}</Fragment>;
          })}
        </p>
      ))}
    </div>
  );
}

export function TermsTab({ chapter, focus }: TabProps) {
  const terms = chapter.terms.filter((t) => inFocus(t.verses, focus));
  const [open, setOpen] = useState<Record<string, EastonArticle | "loading" | "error">>({});
  if (!terms.length) return <p className="empty">{NONE}</p>;
  const toggle = (id: string) => {
    if (open[id]) { const o = { ...open }; delete o[id]; setOpen(o); return; }
    setOpen((o) => ({ ...o, [id]: "loading" }));
    loadEaston(id).then((a) => setOpen((o) => ({ ...o, [id]: a }))).catch(() => setOpen((o) => ({ ...o, [id]: "error" })));
  };
  return (
    <div>
      <p className="meta pt-1">Easton’s Bible Dictionary (1897) articles that cite {focus === null ? "verses in this chapter" : "this verse"}.</p>
      {terms.map((t) => {
        const a = open[t.id];
        return (
          <article key={t.id} className="card">
            <button type="button" className="text-left w-full" aria-expanded={!!a} onClick={() => toggle(t.id)}>
              <span className="card-title block">{t.term}</span>
              <span className="meta">Cites {verseList(t.verses)}</span>
            </button>
            {a === "loading" && <p className="meta mt-2">Loading article…</p>}
            {a === "error" && <p className="meta mt-2">This article could not be loaded. Check your connection and try again.</p>}
            {a && typeof a === "object" && <EastonBody body={a.body} />}
            <p className="mt-1"><SourceChip src={t.src} rec={t.rec} /></p>
          </article>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------- Cross-references
function XrefItem({ start, end, votes, rec }: { start: string; end: string; votes: number; rec: string }) {
  const [text, setText] = useState<string[] | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const show = () => {
    if (text) { setText(null); return; }
    const a = parseRef(start); const b = parseRef(end);
    if (!a) return;
    setState("loading");
    loadChapter(`${a.book}.${a.chapter}`).then((c) => {
      const last = b && b.chapter === a.chapter ? b.verse : Infinity;
      setText(c.verses.filter((v) => v.n >= a.verse && v.n <= last).map((v) => `${v.n} ${v.text}`));
      setState("idle");
    }).catch(() => setState("error"));
  };
  return (
    <li className="py-2 border-t border-stone-soft first:border-0">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <Link href={refHref(start)} className="underline">{formatRange(start, end)}</Link>
        <span className="meta">{votes} {votes === 1 ? "vote" : "votes"}</span>
        <button type="button" className="text-sm text-muted underline" aria-expanded={!!text} onClick={show}>{text ? "Hide text" : "Read here"}</button>
        <SourceChip src="openbible_xrefs" rec={rec} />
      </div>
      {state === "loading" && <p className="meta mt-1">Loading…</p>}
      {state === "error" && <p className="meta mt-1">Could not load this passage. Check your connection and try again.</p>}
      {text && <p className="article mt-1">{text.join(" ")}</p>}
    </li>
  );
}

export function XrefTab({ chapter, focus }: TabProps) {
  if (focus !== null) {
    const list = chapter.xrefs[String(focus)] ?? [];
    if (!list.length) return <p className="empty">{NONE}</p>;
    return (
      <div>
        <p className="meta pt-1">Ranked by OpenBible.info votes. Up to 12 shown.</p>
        <ul className="mt-2">{list.map((x) => <XrefItem key={x[3]} start={x[0]} end={x[1]} votes={x[2]} rec={x[3]} />)}</ul>
      </div>
    );
  }
  const verses = Object.keys(chapter.xrefs).map(Number).sort((a, b) => a - b);
  if (!verses.length) return <p className="empty">{NONE}</p>;
  return (
    <div>
      <p className="meta pt-1">Top three per verse, ranked by OpenBible.info votes. Choose a verse number for more.</p>
      {verses.map((v) => (
        <section key={v} className="card">
          <h3 className="text-sm text-muted">Verse {v}</h3>
          <ul>{chapter.xrefs[String(v)].slice(0, 3).map((x) => <XrefItem key={x[3]} start={x[0]} end={x[1]} votes={x[2]} rec={x[3]} />)}</ul>
        </section>
      ))}
    </div>
  );
}
