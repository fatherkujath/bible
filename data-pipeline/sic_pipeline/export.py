"""Export the reference database as static JSON for the web app.

Writes to app/public/data/:
  books.json                 book list with chapter counts
  attributions.json          source list for the Attributions page and source chips
  ch/<Book>.<chapter>.json   everything the Passage Lens needs for one chapter
  easton/<id>.json           one Easton's Bible Dictionary article (loaded on demand)
  manifest.json              build hash and counts

Chapters follow the BSB's (KJV-style) numbering, because that is how the reader
displays them. Context data keyed to canonical (ORG) verses is mapped back to
BSB verse numbers through versification_map.

Every card carries `src` (source id) and `rec` (upstream record id) so the app can
show a source chip for it. No text is generated here: every string is copied from
the database, which is copied verbatim from the sources.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict

from .common import BOOKS, KJV, NRSV, OSIS_TESTAMENT, REPO_DIR, connect, load_manifest

OUT = REPO_DIR / "app" / "public" / "data"
XREFS_PER_VERSE = 12
REF_IN_TEXT = re.compile(r"\((/[^)#]*)#([1-3]?[A-Za-z]+\.\d+\.\d+)\)")


def _dump(path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _lex_key(strong: str) -> str:
    """'H430' -> 'H0430'; 'G3056' -> 'G3056' (BSB tags use plain Strong's)."""
    m = re.match(r"^([HG])0*(\d+)([A-Za-z]?)$", strong.strip())
    return f"{m.group(1)}{int(m.group(2)):04d}{m.group(3)}" if m else strong.strip()


def _root_dstrongs(tag: str) -> list[str]:
    """STEPBible dStrong cell -> the tags worth looking up ('H9003/{H7225G}' -> ['H7225G', 'H9003'])."""
    roots = re.findall(r"\{([HG]\d{4}[A-Za-z]?)\}", tag or "")
    others = [t for t in re.findall(r"[HG]\d{4}[A-Za-z]?", tag or "") if t not in roots]
    return roots + others


def export() -> dict:
    con = connect()
    con.row_factory = None
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # --- lookups loaded once -------------------------------------------------
    kjv_to_org: dict[str, list[str]] = defaultdict(list)
    org_to_kjv: dict[str, list[str]] = defaultdict(list)
    nrsv_to_org: dict[str, list[str]] = defaultdict(list)
    for scheme, sref, oref in con.execute("SELECT scheme, scheme_ref, osis_ref FROM versification_map ORDER BY scheme_ref"):
        if scheme == KJV:
            kjv_to_org[sref].append(oref)
            org_to_kjv[oref].append(sref)
        elif scheme == NRSV:
            nrsv_to_org[sref].append(oref)

    def english_to_kjv(ref: str) -> list[str]:
        """A ref in English numbering (KJV, or NRSV where they differ) -> KJV refs."""
        if ref in kjv_to_org:
            return [ref]
        out = []
        for o in nrsv_to_org.get(ref, []):
            out += org_to_kjv.get(o, [])
        return sorted(set(out))

    lexicon = {}
    lex_by_estrong = {}
    for d, e, u, lang, lemma, tr, morph, gloss, src, rec in con.execute("SELECT * FROM lexicon ORDER BY dstrong"):
        entry = {"lemma": lemma, "tr": tr, "morph": morph, "gloss": gloss, "lang": lang, "src": src, "rec": rec}
        lexicon[d] = entry
        lex_by_estrong.setdefault(e, d)

    words_by_org: dict[str, list] = defaultdict(list)
    for rec, oref, pos, typ, orig, tr, gloss, strongs, morph, lemma, eds, src in con.execute(
            "SELECT * FROM word ORDER BY osis_ref, position, record_id"):
        words_by_org[oref].append({"o": orig, "x": tr, "g": gloss, "s": strongs, "m": morph,
                                   "l": lemma, "t": typ, "e": eds, "rec": rec})

    # Theographic: verse years and events by KJV ref.
    theo_verse = {tid: (kref, year) for tid, kref, year in con.execute("SELECT theo_id, kjv_ref, year_num FROM sa_theo_verse")}
    events = {r[0]: r for r in con.execute("SELECT theo_id, title, start_date, duration, sort_key, chronology, record_id FROM sa_theo_event")}
    year_by_kjv = {k: y for k, y in theo_verse.values()}
    events_by_kjv: dict[str, set] = defaultdict(set)
    for kind, tid, vid in con.execute("SELECT kind, theo_id, theo_verse_id FROM sa_theo_link WHERE kind='event'"):
        events_by_kjv[theo_verse[vid][0]].add(tid)

    # TIPNR names by canonical ref.
    names = {u: (k, us, t, rec) for u, k, us, t, src, rec in con.execute("SELECT * FROM name_entity")}
    names_by_org: dict[str, set] = defaultdict(set)
    for u, oref in con.execute("SELECT unique_name, osis_ref FROM name_ref"):
        names_by_org[oref].add(u)
    relations: dict[str, dict] = defaultdict(lambda: defaultdict(list))
    for u, rel, other in con.execute("SELECT unique_name, relation, other_name FROM name_relation ORDER BY unique_name, relation, other_name"):
        relations[u][rel].append(other)

    # OpenBible places by English ref.
    geo_places = {p: (n, slug, types, rec) for p, n, slug, types, src, rec in con.execute("SELECT * FROM geo_place")}
    geo_idents: dict[str, list] = defaultdict(list)
    for pid, rank, desc, conf, lon, lat, ptype, src, rec in con.execute("SELECT * FROM geo_identification ORDER BY place_id, rank"):
        geo_idents[pid].append({"rank": rank, "desc": desc, "conf": conf, "lat": lat, "lon": lon, "pt": ptype, "rec": rec})
    places_by_kjv: dict[str, set] = defaultdict(set)
    for pid, ref in con.execute("SELECT place_id, kjv_ref FROM geo_place_verse"):
        for k in english_to_kjv(ref):
            places_by_kjv[k].add(pid)

    # Cross references by KJV ref.
    xrefs_by_kjv: dict[str, list] = defaultdict(list)
    for frm, a, b, votes, rec in con.execute("SELECT from_ref, to_start, to_end, votes, record_id FROM xref ORDER BY from_ref, votes DESC, to_start"):
        for k in english_to_kjv(frm):
            if len(xrefs_by_kjv[k]) < XREFS_PER_VERSE:
                xrefs_by_kjv[k].append([a, b, votes, rec])

    # Easton's articles: index the verses each article cites, and write each article.
    easton_by_kjv: dict[str, set] = defaultdict(set)
    easton_meta = {}
    for tid, term_id, term, body, person_ids, place_ids, src, rec in con.execute("SELECT * FROM sa_easton ORDER BY theo_id"):
        cited = {m.group(2) for m in REF_IN_TEXT.finditer(body)}
        for ref in cited:
            for k in english_to_kjv(ref):
                easton_by_kjv[k].add(tid)
        easton_meta[tid] = term
        _dump(OUT / "easton" / f"{tid}.json", {"id": tid, "term": term, "body": body, "src": src, "rec": rec})

    # BSB text, headings, notes, alignment.
    bsb_text = {}
    for ref, text, rec in con.execute("SELECT scheme_ref, text, record_id FROM verse_text WHERE translation='BSB' ORDER BY ord"):
        bsb_text[ref] = (text, rec)
    headings: dict[str, list] = defaultdict(list)
    for ref, seq, kind, text in con.execute("SELECT scheme_ref, seq, kind, text FROM bsb_heading ORDER BY scheme_ref, seq"):
        headings[ref].append({"kind": kind, "text": text})
    notes: dict[str, list] = defaultdict(list)
    for ref, seq, text in con.execute("SELECT scheme_ref, seq, text FROM bsb_note ORDER BY scheme_ref, seq"):
        notes[ref].append(text)
    align: dict[str, list] = defaultdict(list)
    for ref, pos, eng, strongs, lemma, tr in con.execute(
            "SELECT scheme_ref, position, english, strongs, lemma, translit FROM bsb_word ORDER BY scheme_ref, position"):
        align[ref].append([eng, strongs, lemma, tr])

    # --- chapters ------------------------------------------------------------
    chapters_by_book: dict[str, list[int]] = defaultdict(list)
    refs_by_chapter: dict[tuple, list[str]] = defaultdict(list)
    for ref in bsb_text:
        b, c, v = ref.split(".")
        if int(c) not in chapters_by_book[b]:
            chapters_by_book[b].append(int(c))
        refs_by_chapter[(b, int(c))].append(ref)
    order = [(b, c) for b, *_ in BOOKS for c in sorted(chapters_by_book[b])]
    stats = defaultdict(int)

    for i, (book, chap) in enumerate(order):
        verse_refs = list(refs_by_chapter[(book, chap)])
        verse_refs.sort(key=lambda r: int(r.split(".")[2]))
        orgs_in_chapter: list[str] = []
        for r in verse_refs:
            for o in kjv_to_org.get(r, []):
                if o not in orgs_in_chapter:
                    orgs_in_chapter.append(o)

        def vnums(org_refs) -> list[int]:
            out = set()
            for o in org_refs:
                for k in org_to_kjv.get(o, []):
                    if k in verse_refs:
                        out.add(int(k.split(".")[2]))
            return sorted(out)

        verses = []
        lex_used = set()
        for r in verse_refs:
            n = int(r.split(".")[2])
            text, rec = bsb_text[r]
            for w in align.get(r, []):
                for s in w[1].split():
                    k = _lex_key(s)
                    d = lexicon.get(k) and k or lex_by_estrong.get(k)
                    if d:
                        lex_used.add(d)
                        w.append(d)
            verses.append({"n": n, "ref": r, "text": text, "rec": rec, "org": kjv_to_org.get(r, []),
                           "h": headings.get(r, []), "notes": notes.get(r, []), "w": align.get(r, [])})

        original = []
        for o in orgs_in_chapter:
            ws = words_by_org.get(o, [])
            for w in ws:
                for d in _root_dstrongs(w["s"]):
                    if d in lexicon:
                        lex_used.add(d)
            original.append({"org": o, "lang": "Hebrew" if OSIS_TESTAMENT[book] == "OT" else "Greek",
                             "kjv": vnums([o]), "words": ws})

        # World: Theographic years and events.
        by_year: dict[int, list[int]] = defaultdict(list)
        for r in verse_refs:
            if year_by_kjv.get(r) is not None:
                by_year[year_by_kjv[r]].append(int(r.split(".")[2]))
        evs = set()
        ev_verses: dict[str, set] = defaultdict(set)
        for r in verse_refs:
            for e in events_by_kjv.get(r, ()):
                evs.add(e)
                ev_verses[e].add(int(r.split(".")[2]))
        world = {
            "years": [{"year": y, "verses": by_year[y]} for y in sorted(by_year, key=lambda y: by_year[y][0])],
            "chronology": "Theographic (single chronology; Ussher-style, creation 4003 BC)",
            "events": [{"id": e, "title": events[e][1], "start": events[e][2], "duration": events[e][3],
                        "verses": sorted(ev_verses[e]), "src": "theographic", "rec": events[e][6]}
                       for e in sorted(evs, key=lambda e: (events[e][4] or 0, events[e][1]))],
            "studyNotes": None,
        }

        # People and other names (TIPNR).
        name_hits: dict[str, set] = defaultdict(set)
        for o in orgs_in_chapter:
            for u in names_by_org.get(o, ()):
                name_hits[u].add(o)
        people, other_names = [], []
        for u in sorted(name_hits, key=lambda u: (min(vnums(name_hits[u]) or [0]), u)):
            kind, ustrong, etype, rec = names[u]
            entry = {"id": u, "name": u.split("@")[0], "type": etype, "verses": vnums(name_hits[u]),
                     "rel": {k: v for k, v in relations.get(u, {}).items()}, "src": "stepbible", "rec": rec}
            if kind == "person":
                people.append(entry)
            elif kind == "other":
                other_names.append(entry)

        # Places (OpenBible).
        place_hits: dict[str, set] = defaultdict(set)
        for r in verse_refs:
            for p in places_by_kjv.get(r, ()):
                place_hits[p].add(int(r.split(".")[2]))
        places = []
        for p in sorted(place_hits, key=lambda p: (min(place_hits[p]), geo_places[p][0])):
            name, slug, types, rec = geo_places[p]
            places.append({"id": p, "name": name, "slug": slug, "types": types, "verses": sorted(place_hits[p]),
                           "ids": geo_idents.get(p, []), "src": "openbible_geo", "rec": rec,
                           "url": f"https://www.openbible.info/geo/ancient/{p}/{slug}" if slug else None})

        # Culture and terms: Easton's articles citing these verses.
        term_hits: dict[str, set] = defaultdict(set)
        for r in verse_refs:
            for t in easton_by_kjv.get(r, ()):
                term_hits[t].add(int(r.split(".")[2]))
        terms = [{"id": t, "term": easton_meta[t], "verses": sorted(term_hits[t]), "src": "theographic", "rec": f"easton.json#{t}"}
                 for t in sorted(term_hits, key=lambda t: (-len(term_hits[t]), easton_meta[t]))]

        xrefs = {str(int(r.split(".")[2])): xrefs_by_kjv[r] for r in verse_refs if xrefs_by_kjv.get(r)}

        prev_ = order[i - 1] if i > 0 else None
        next_ = order[i + 1] if i + 1 < len(order) else None
        data = {
            "book": book, "chapter": chap,
            "prev": f"{prev_[0]}.{prev_[1]}" if prev_ else None,
            "next": f"{next_[0]}.{next_[1]}" if next_ else None,
            "verses": verses, "original": original,
            "lex": {d: lexicon[d] for d in sorted(lex_used)},
            "world": world, "people": people, "names": other_names, "places": places,
            "terms": terms, "xrefs": xrefs,
        }
        _dump(OUT / "ch" / f"{book}.{chap}.json", data)
        stats["chapters"] += 1
        for key in ("people", "places", "terms"):
            if data[key]:
                stats[f"chapters_with_{key}"] += 1
        if world["events"]:
            stats["chapters_with_events"] += 1
        if xrefs:
            stats["chapters_with_xrefs"] += 1

    books = [{"osis": o, "name": n, "testament": t, "chapters": sorted(chapters_by_book[o])} for o, _, n, t in BOOKS]
    _dump(OUT / "books.json", books)
    manifest = load_manifest()
    _dump(OUT / "attributions.json", [
        {k: s.get(k) for k in ("id", "name", "license", "license_group", "attribution", "homepage", "repo", "commit", "notes")}
        for s in manifest["sources"]])
    build_hash = dict(con.execute("SELECT key, value FROM build_info"))
    con.close()
    summary = dict(stats)
    _dump(OUT / "manifest.json", {"sources": json.loads(build_hash["sources"]), **summary})
    print(f"  exported {summary['chapters']} chapters to {OUT.relative_to(REPO_DIR)}")
    return summary
