"""STEPBible brief lexicons: TBESH (Hebrew) and TBESG (Greek).

Imported: Strong's numbers, lemma, transliteration, morph and gloss. The gloss
column was "created by Tyndale scholars" (TBESH header) and is CC BY 4.0.

NOT imported (Phase 1):
  * TBESH "Meaning" column: based on the Abridged BDB by Online Bible, and the
    file header says permission should be gained from Online Bible before use.
  * TBESG definitions: Abbott-Smith via a separate digitization whose license
    has not yet been checked. Revisit before the Passage Lens needs definitions.
"""
from __future__ import annotations

import re

from ..common import source_file

SRC = "stepbible"
FILES = {
    "Hebrew": "Lexicons/TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt",
    "Greek": "Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt",
}
DATA = re.compile(r"^[HG]\d{4}")


def import_lexicons(con, report: dict) -> None:
    stats = {}
    for language, rel in FILES.items():
        rows, seen = [], set()
        with open(source_file(SRC, rel), encoding="utf-8-sig") as f:
            for n, line in enumerate(f, start=1):
                if not DATA.match(line):
                    continue
                cols = line.rstrip("\n").split("\t")
                if len(cols) < 7:
                    continue
                estrong = cols[0].strip()
                dstrong = cols[1].strip().split(" ")[0].strip()
                if not dstrong or dstrong in seen:
                    continue
                seen.add(dstrong)
                rows.append((dstrong, estrong, cols[2].strip().rstrip(",").strip() or None, language,
                             cols[3].strip(), cols[4].strip() or None, cols[5].strip() or None,
                             cols[6].strip() or None, SRC, f"{rel.split('/')[-1].split(' ')[0]}:{dstrong}"))
        con.executemany("INSERT INTO lexicon VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        stats[language] = len(rows)
    report["lexicon"] = stats
