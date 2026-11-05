"""STEPBible TIPNR: every proper name, separated into individual people,
places and other entities, with all references and family links.

Imported: unique names, name forms (dStrong, original, translated), every
reference, and parent/sibling/partner/offspring links.

NOT imported: the Description column, the '#Summary description' column and
the @Briefest/@Brief/@Short/@Article lines. STEPBible's README states that
these descriptions were created by Claude 3 AI, which sourcing rule 1 excludes.
"""
from __future__ import annotations

import re

from ..common import KJV, NRSV, STEP_REF_RE, step_ref_to_osis, source_file

SRC = "stepbible"
REL = "Proper Nouns/TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt"
BLOCK = re.compile(r"^\$=+ (PERSON\(s\)|PLACE|OTHER)")
KIND = {"PERSON(s)": "person", "PLACE": "place", "OTHER": "other"}
NAME_TOKEN = re.compile(r"[^,+;]+?@[^,+;\s]+")

# Tokens in TIPNR's reference columns that are not references at all (upstream
# data issues at the pinned commit). They are skipped and listed in the build
# report; any NEW malformed token fails validation. Report these to STEPBible.
KNOWN_MALFORMED = {
    "Achaicus@1Co.16.17-: @",
    "Joshua@Exo.17.9-Heb: 16",
    "LORD@Gen.1.1-Rev: etc",
}


def _names(cell: str) -> list[str]:
    return [t.strip() for t in NAME_TOKEN.findall(cell or "") if "@" in t]


def import_tipnr(con, report: dict) -> None:
    nrsv_to_org: dict[str, list[str]] = {}
    kjv_to_org: dict[str, list[str]] = {}
    for scheme, sref, oref in con.execute(
            "SELECT scheme, scheme_ref, osis_ref FROM versification_map WHERE scheme IN (?,?)", (NRSV, KJV)):
        (nrsv_to_org if scheme == NRSV else kjv_to_org).setdefault(sref, []).append(oref)

    entities, forms, refs, relations = [], [], set(), set()
    unresolved: list[str] = []
    lxx: list[str] = []
    malformed: list[str] = []
    kjv_fallback: list[str] = []
    kind = None
    current = None
    with open(source_file(SRC, REL), encoding="utf-8-sig") as f:
        for line in f:
            text = line.rstrip("\n")
            m = BLOCK.match(text)
            if m:
                kind, current = KIND[m.group(1)], None
                continue
            if kind is None or not text.strip():
                continue
            cols = text.split("\t")
            head = cols[0].strip()
            if current is None:
                if "@" not in head or "=" not in head:
                    continue
                unique, _, ustrong = head.partition("=")
                current = unique.strip()
                etype = cols[8].strip() if kind == "person" and len(cols) > 8 else None
                entities.append((current, kind, ustrong.strip() or None, etype or None, SRC, head))
                if kind == "person":
                    parents = (cols[2] if len(cols) > 2 else "")
                    for rel, cell in (("parent", parents), ("sibling", cols[3] if len(cols) > 3 else ""),
                                      ("partner", cols[4] if len(cols) > 4 else ""),
                                      ("offspring", cols[5] if len(cols) > 5 else "")):
                        for other in _names(cell):
                            relations.add((current, rel, other, SRC, head))
                continue
            if head.startswith("$"):
                continue
            if head.startswith("–") and not head.startswith("– Total"):
                significance = head.lstrip("–").strip()
                dcol = next((i for i, c in enumerate(cols) if "«" in c), None)
                if dcol is None:
                    continue
                dstrong_cell = cols[dcol].strip()
                dstrong = dstrong_cell.split("«")[0].strip() or None
                original = dstrong_cell.partition("=")[2].strip() or None
                translated = cols[dcol + 1].strip() if len(cols) > dcol + 1 else None
                ref_cell = next((c for c in reversed(cols[dcol + 2:]) if c.strip()), "")
                forms.append((current, significance, dstrong, original, translated, SRC, f"{current}|{significance}|{dstrong}"))
                for tok in re.split(r"[;,]", ref_cell):
                    tok = tok.strip()
                    if not tok:
                        continue
                    if tok.startswith("LXX."):
                        # Septuagint reference: outside the 66-book canon's numbering.
                        lxx.append(f"{current}: {tok}")
                        continue
                    if not STEP_REF_RE.match(tok):
                        key = f"{current}: {tok}"
                        (malformed if key in KNOWN_MALFORMED else unresolved).append(key)
                        continue
                    osis = step_ref_to_osis(tok)
                    orgs = nrsv_to_org.get(osis) if osis else None
                    if not orgs and osis:
                        # A few TIPNR refs use KJV numbering where it differs from
                        # STEPBible's NRSV base (e.g. 2Co.13.14).
                        orgs = kjv_to_org.get(osis)
                        if orgs:
                            kjv_fallback.append(f"{current}: {tok}")
                    if not orgs:
                        unresolved.append(f"{current}: {tok}")
                        continue
                    for o in orgs:
                        refs.add((current, o, SRC, f"{current}|{tok}"))

    con.executemany("INSERT INTO name_entity VALUES (?,?,?,?,?,?)", entities)
    con.executemany("INSERT INTO name_form VALUES (?,?,?,?,?,?,?)", forms)
    ref_rows = sorted(refs)
    seen = set()
    deduped = []
    for r in ref_rows:
        if (r[0], r[1]) not in seen:
            seen.add((r[0], r[1]))
            deduped.append(r)
    con.executemany("INSERT INTO name_ref VALUES (?,?,?,?)", deduped)
    con.executemany("INSERT INTO name_relation VALUES (?,?,?,?,?)", sorted(relations))
    report["tipnr"] = {
        "entities": len(entities),
        "name_forms": len(forms),
        "refs": len(deduped),
        "relations": len(relations),
        "refs_resolved_via_kjv_numbering": kjv_fallback,
        "lxx_refs_skipped": len(lxx),
        "known_malformed_tokens_skipped": malformed,
        "unresolved_refs": len(unresolved),
        "unresolved_examples": unresolved[:200],
    }
