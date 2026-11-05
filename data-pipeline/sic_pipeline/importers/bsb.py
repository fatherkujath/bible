"""Berean Standard Bible: verse text and English-to-original word alignment.

* Plain verse text comes from BSB.json (one string per verse, as published).
* Word alignment comes from the <w> tags in BSB-osis.json, which pair each
  English phrase with a Strong's number, lemma and transliteration. Tags with no
  English text (original words left untranslated) are kept with english = NULL.

Both files use KJV-style versification, so references are stored in the KJV
scheme and reach canonical (ORG) verses through versification_map.
"""
from __future__ import annotations

import html
import json
import re

from ..common import BOOKS, KJV, osis_ref, source_file

SRC = "bsb"
TEXT_FILE = "sources/en/BSB/BSB.json"
OSIS_FILE = "sources/en/BSB/BSB-osis.json"
W_TAG = re.compile(r'<w\s+([^>]*?)(?:/>|>(.*?)</w>)', re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')
TAG = re.compile(r"<[^>]+>")


def _books(path: str) -> list:
    data = json.loads(source_file(SRC, path).read_text(encoding="utf-8"))
    books = data["books"]
    if len(books) != len(BOOKS):
        raise SystemExit(f"BSB: expected 66 books in {path}, found {len(books)}")
    return books


def import_bsb(con, report: dict) -> None:
    text_rows, ord_ = [], 0
    for (osis, *_), book in zip(BOOKS, _books(TEXT_FILE)):
        for ch in book["chapters"]:
            for v in ch["verses"]:
                ord_ += 1
                ref = osis_ref(osis, ch["chapter"], v["verse"])
                text_rows.append(("BSB", KJV, ref, ord_, v["text"].strip(), SRC, f"{TEXT_FILE}#{v['name']}"))
    con.executemany("INSERT INTO verse_text VALUES (?,?,?,?,?,?,?)", text_rows)

    word_rows = []
    for (osis, *_), book in zip(BOOKS, _books(OSIS_FILE)):
        for ch in book["chapters"]:
            for v in ch["verses"]:
                ref = osis_ref(osis, ch["chapter"], v["verse"])
                for pos, m in enumerate(W_TAG.finditer(v["text"]), start=1):
                    attrs = dict(ATTR.findall(m.group(1)))
                    lemma_attr = attrs.get("lemma", "")
                    strongs = " ".join(p.split(":", 1)[1] for p in lemma_attr.split() if p.startswith("strong:"))
                    lemma = next((p.split(":", 1)[1] for p in lemma_attr.split() if p.startswith("lemma.")), None)
                    english = html.unescape(TAG.sub("", m.group(2) or "")).strip() or None
                    translit = attrs.get("xlit", "").removeprefix("Latn:") or None
                    if not strongs:
                        continue
                    word_rows.append((ref, pos, english, strongs, lemma, translit, SRC, f"{OSIS_FILE}#{v['name']}#{pos}"))
    con.executemany("INSERT INTO bsb_word VALUES (?,?,?,?,?,?,?,?)", word_rows)
    con.executemany(
        "INSERT INTO search_fts(kind, ref, title, body) VALUES ('verse', ?, 'BSB', ?)",
        [(r[2], r[4]) for r in text_rows],
    )
    report["bsb"] = {"verses": len(text_rows), "aligned_words": len(word_rows)}
