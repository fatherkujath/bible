"""STEPBible TAHOT (Hebrew OT) and TAGNT (Greek NT): canonical verses,
versification maps and original-language words.

STEPBible reference format (from the file headers):
  * Base reference = English verse numbering as defined by the NRSV.
  * OT: Hebrew numbering in (round brackets) when it differs.
  * NT: KJV numbering in [square brackets], NA (Greek) numbering in (round
    brackets), other traditions in {curly brackets}, each only when it differs.

From this we take:
  * ORG (canonical) ref = Hebrew ref for the OT, NA ref for the NT.
  * NRSV ref            = the base ref.
  * KJV ref             = the [bracket] ref in the NT, else the base ref.
    For the OT, STEPBible gives no separate KJV numbering; the pipeline checks
    that the BSB/Theographic KJV verse set equals STEPBible's English OT set and
    records that assumption in CHANGES-TO-SOURCE-DATA.md.
"""
from __future__ import annotations

import re

from ..common import BOOKS, KJV, NRSV, STEP_TO_OSIS, osis_ref, source_file

SRC = "stepbible"
TAHOT = [
    "Translators Amalgamated OT+NT/TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
    "Translators Amalgamated OT+NT/TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
    "Translators Amalgamated OT+NT/TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
    "Translators Amalgamated OT+NT/TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
]
TAGNT = [
    "Translators Amalgamated OT+NT/TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
    "Translators Amalgamated OT+NT/TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
]

# Data lines start with a STEPBible book code and a reference, then '#NN=TYPE'.
LINE_START = re.compile(r"^([1-3A-Z][A-Za-z0-9]{2})\.\d")
REF_RE = re.compile(
    r"^(?P<book>[1-3A-Z][A-Za-z0-9]{2})\.(?P<c>\d+)\.(?P<v>\d+)"
    r"(?P<alts>(?:[\(\[\{]\d+\.\d+[\)\]\}])*)"
    r"#(?P<pos>\d+)=(?P<type>\S+)$"
)
ALT_RE = re.compile(r"([\(\[\{])(\d+)\.(\d+)[\)\]\}]")


def _parse_ref(token: str):
    m = REF_RE.match(token)
    if not m:
        return None
    alts = {open_: (int(c), int(v)) for open_, c, v in ALT_RE.findall(m.group("alts"))}
    return m, alts


def import_step_texts(con, report: dict) -> None:
    verse_rows: dict[str, tuple] = {}
    maps: set[tuple] = set()
    words: list[tuple] = []
    unparsed: list[str] = []

    def handle(path_rel: str, testament: str) -> None:
        with open(source_file(SRC, path_rel), encoding="utf-8-sig") as f:
            for line in f:
                if not LINE_START.match(line) or "#" not in line.split("\t", 1)[0]:
                    continue
                cols = line.rstrip("\n").split("\t")
                token = cols[0].strip()
                parsed = _parse_ref(token)
                if not parsed:
                    unparsed.append(token)
                    continue
                m, alts = parsed
                step_book = m.group("book")
                if step_book not in STEP_TO_OSIS:
                    unparsed.append(token)
                    continue
                book = STEP_TO_OSIS[step_book]
                base = (int(m.group("c")), int(m.group("v")))
                org = alts.get("(", base)
                kjv = alts.get("[", base) if testament == "NT" else base
                org_ref = osis_ref(book, *org)
                record_id = token.split("=", 1)[0]
                verse_rows.setdefault(org_ref, (book, org[0], org[1], record_id))
                maps.add((NRSV, osis_ref(book, *base), org_ref, record_id))
                maps.add((KJV, osis_ref(book, *kjv), org_ref, record_id))
                pos = int(m.group("pos"))
                if testament == "OT":
                    # Eng (Heb) Ref & Type | Hebrew | Transliteration | Translation | dStrongs | Grammar | ...
                    words.append((record_id, org_ref, pos, m.group("type"),
                                  cols[1].strip(), cols[2].strip() or None, cols[3].strip() or None,
                                  cols[4].strip() or None, cols[5].strip() or None, None, None, SRC))
                else:
                    # Word & Type | Greek (translit) | English | dStrongs=Grammar | Dictionary=Gloss | editions | ...
                    greek = cols[1].strip()
                    gm = re.match(r"^(.*?)\s*\((.*)\)\s*$", greek)
                    original, translit = (gm.group(1), gm.group(2)) if gm else (greek, None)
                    strongs, _, morph = cols[3].strip().partition("=")
                    lemma = cols[4].strip().partition("=")[0] or None
                    words.append((record_id, org_ref, pos, m.group("type"),
                                  original, translit, cols[2].strip() or None,
                                  strongs or None, morph or None, lemma, cols[5].strip() or None, SRC))

    for rel in TAHOT:
        handle(rel, "OT")
    for rel in TAGNT:
        handle(rel, "NT")

    if unparsed:
        raise SystemExit(f"STEPBible: {len(unparsed)} reference tokens not understood, e.g. {unparsed[:5]}")

    order = {osis: i for i, (osis, *_rest) in enumerate(BOOKS)}
    ordered = sorted(verse_rows.items(), key=lambda kv: (order[kv[1][0]], kv[1][1], kv[1][2]))
    con.executemany(
        "INSERT INTO verse VALUES (?,?,?,?,?,?,?)",
        [(ref, b, c, v, i, SRC, rid) for i, (ref, (b, c, v, rid)) in enumerate(ordered, start=1)],
    )
    con.executemany(
        "INSERT OR IGNORE INTO versification_map VALUES (?,?,?,?,?)",
        [(s, sref, oref, SRC, rid) for s, sref, oref, rid in sorted(maps)],
    )
    words.sort(key=lambda w: (w[11], w[0]))
    dupes = con.executemany("INSERT OR IGNORE INTO word VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", words).rowcount
    report["stepbible_texts"] = {
        "verses_org": len(ordered),
        "word_lines": len(words),
        "words_inserted": dupes,
        "map_rows": len(maps),
    }
