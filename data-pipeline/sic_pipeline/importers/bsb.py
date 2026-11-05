"""Berean Standard Bible: verse text, psalm titles, section headings, footnotes
and English-to-original word alignment, all from BSB-osis.json.

The OSIS file keeps headings, psalm superscriptions and footnotes as separate
elements, so they can be shown in their proper places:
  * verse text  = the verse with all <title> and <note> elements removed;
  * psalm title = <title canonical="true" type="psalm">, stored as verse 0
                  (the KJV-scheme "superscription" verse that maps to ORG verse 1);
  * headings    = <title> with no type (section) or type="acrostic", verbatim;
  * footnotes   = <note> contents, verbatim;
  * alignment   = <w> tags (Strong's number, lemma, transliteration, English).
Parallel-passage and scope titles are not imported.

BSB.json (the plain-text edition in the same mirror) is used only as a check:
the derived verse text must match it except for psalm titles, which BSB.json
joins to verse 1, and whitespace.
"""
from __future__ import annotations

import html
import json
import re

from ..common import BOOKS, KJV, osis_ref, source_file

SRC = "bsb"
TEXT_FILE = "sources/en/BSB/BSB.json"
OSIS_FILE = "sources/en/BSB/BSB-osis.json"

TITLE = re.compile(r"<title\b([^>]*)>(.*?)</title>", re.S)
NOTE = re.compile(r"<note\b[^>]*>(.*?)</note>", re.S)
W_TAG = re.compile(r'<w\s+([^>]*?)(?:/>|>(.*?)</w>)', re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def _plain(markup: str) -> str:
    return WS.sub(" ", html.unescape(TAG.sub("", markup))).strip()


def _words(markup: str, ref: str, start: int) -> list[tuple]:
    rows = []
    pos = start
    for m in W_TAG.finditer(markup):
        attrs = dict(ATTR.findall(m.group(1)))
        parts = attrs.get("lemma", "").split()
        strongs = " ".join(p.split(":", 1)[1] for p in parts if p.startswith("strong:"))
        if not strongs:
            continue
        pos += 1
        lemma = next((p.split(":", 1)[1] for p in parts if p.startswith("lemma.")), None)
        english = _plain(m.group(2) or "") or None
        translit = attrs.get("xlit", "").removeprefix("Latn:") or None
        rows.append((ref, pos, english, strongs, lemma, translit, SRC, f"{OSIS_FILE}#{ref}#w{pos}"))
    return rows


def _books(path: str) -> list:
    books = json.loads(source_file(SRC, path).read_text(encoding="utf-8"))["books"]
    if len(books) != len(BOOKS):
        raise SystemExit(f"BSB: expected 66 books in {path}, found {len(books)}")
    return books


def import_bsb(con, report: dict) -> None:
    text_rows, word_rows, heading_rows, note_rows = [], [], [], []
    ord_ = 0
    plain_check = {}
    for (osis, *_), book in zip(BOOKS, _books(TEXT_FILE)):
        for ch in book["chapters"]:
            for v in ch["verses"]:
                plain_check[osis_ref(osis, ch["chapter"], v["verse"])] = WS.sub(" ", v["text"]).strip()

    mismatches = []
    for (osis, *_), book in zip(BOOKS, _books(OSIS_FILE)):
        for ch in book["chapters"]:
            for v in ch["verses"]:
                markup = v["text"]
                ref = osis_ref(osis, ch["chapter"], v["verse"])
                rec = f"{OSIS_FILE}#{v['name']}"
                body = markup
                psalm_title = None
                seq = 0
                for m in TITLE.finditer(markup):
                    attrs = m.group(1)
                    if 'type="psalm"' in attrs:
                        psalm_title = m.group(2)
                    elif 'type=' not in attrs or 'type="acrostic"' in attrs:
                        seq += 1
                        kind = "acrostic" if "acrostic" in attrs else "section"
                        heading_rows.append((ref, seq, kind, _plain(m.group(2)), SRC, f"{rec}#title{seq}"))
                body = TITLE.sub(" ", body)
                for n, m in enumerate(NOTE.finditer(body), start=1):
                    note_rows.append((ref, n, _plain(m.group(1)), SRC, f"{rec}#note{n}"))
                body = NOTE.sub("", body)

                if psalm_title is not None:
                    tref = osis_ref(osis, ch["chapter"], 0)
                    for n, m in enumerate(NOTE.finditer(psalm_title), start=1):
                        note_rows.append((tref, n, _plain(m.group(1)), SRC, f"{rec}#psalm-title-note{n}"))
                    psalm_title = NOTE.sub("", psalm_title)
                    ord_ += 1
                    text_rows.append(("BSB", KJV, tref, ord_, _plain(psalm_title), SRC, f"{rec}#psalm-title"))
                    word_rows += _words(psalm_title, tref, 0)
                ord_ += 1
                text = _plain(body)
                text_rows.append(("BSB", KJV, ref, ord_, text, SRC, rec))
                word_rows += _words(body, ref, 0)

                expected = plain_check.get(ref, "")
                if psalm_title is not None:
                    expected = expected.removeprefix(_plain(psalm_title)).strip()
                if text.replace(" ", "") != expected.replace(" ", ""):
                    mismatches.append(ref)

    if mismatches:
        raise SystemExit(f"BSB: OSIS text differs from BSB.json in {len(mismatches)} verses, e.g. {mismatches[:5]}")

    con.executemany("INSERT INTO verse_text VALUES (?,?,?,?,?,?,?)", text_rows)
    con.executemany("INSERT INTO bsb_word VALUES (?,?,?,?,?,?,?,?)", word_rows)
    con.executemany("INSERT INTO bsb_heading VALUES (?,?,?,?,?,?)", heading_rows)
    con.executemany("INSERT INTO bsb_note VALUES (?,?,?,?,?)", note_rows)
    con.executemany(
        "INSERT INTO search_fts(kind, ref, title, body) VALUES ('verse', ?, 'BSB', ?)",
        [(r[2], r[4]) for r in text_rows],
    )
    report["bsb"] = {
        "verses": sum(1 for r in text_rows if not r[2].endswith(".0")),
        "psalm_titles": sum(1 for r in text_rows if r[2].endswith(".0")),
        "headings": len(heading_rows),
        "footnotes": len(note_rows),
        "aligned_words": len(word_rows),
        "text_matches_plain_edition": True,
    }
