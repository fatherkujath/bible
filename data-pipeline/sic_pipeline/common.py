"""Shared constants and helpers for the Scripture in Context data pipeline.

Canonical verse key: OSIS book code + Copenhagen Alliance "ORG" versification
(Hebrew Bible numbering for the OT, Greek NT numbering for the NT), written as
"Gen.1.1". Every dataset is mapped onto this key at import time.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent          # data-pipeline/
REPO_DIR = PIPELINE_DIR.parent                                   # repo root
MANIFEST = PIPELINE_DIR / "sources.json"
LOCKFILE = PIPELINE_DIR / "sources.lock.json"
CACHE_DIR = PIPELINE_DIR / ".cache" / "sources"                  # downloaded, never committed
BUILD_DIR = PIPELINE_DIR / "build"                               # pipeline output
DB_PATH = BUILD_DIR / "reference.db"
REPORT_PATH = BUILD_DIR / "build-report.json"

# 66-book Protestant canon in canonical order.
# (OSIS code, STEPBible code, English name, testament)
BOOKS: list[tuple[str, str, str, str]] = [
    ("Gen", "Gen", "Genesis", "OT"), ("Exod", "Exo", "Exodus", "OT"),
    ("Lev", "Lev", "Leviticus", "OT"), ("Num", "Num", "Numbers", "OT"),
    ("Deut", "Deu", "Deuteronomy", "OT"), ("Josh", "Jos", "Joshua", "OT"),
    ("Judg", "Jdg", "Judges", "OT"), ("Ruth", "Rut", "Ruth", "OT"),
    ("1Sam", "1Sa", "1 Samuel", "OT"), ("2Sam", "2Sa", "2 Samuel", "OT"),
    ("1Kgs", "1Ki", "1 Kings", "OT"), ("2Kgs", "2Ki", "2 Kings", "OT"),
    ("1Chr", "1Ch", "1 Chronicles", "OT"), ("2Chr", "2Ch", "2 Chronicles", "OT"),
    ("Ezra", "Ezr", "Ezra", "OT"), ("Neh", "Neh", "Nehemiah", "OT"),
    ("Esth", "Est", "Esther", "OT"), ("Job", "Job", "Job", "OT"),
    ("Ps", "Psa", "Psalms", "OT"), ("Prov", "Pro", "Proverbs", "OT"),
    ("Eccl", "Ecc", "Ecclesiastes", "OT"), ("Song", "Sng", "Song of Songs", "OT"),
    ("Isa", "Isa", "Isaiah", "OT"), ("Jer", "Jer", "Jeremiah", "OT"),
    ("Lam", "Lam", "Lamentations", "OT"), ("Ezek", "Ezk", "Ezekiel", "OT"),
    ("Dan", "Dan", "Daniel", "OT"), ("Hos", "Hos", "Hosea", "OT"),
    ("Joel", "Jol", "Joel", "OT"), ("Amos", "Amo", "Amos", "OT"),
    ("Obad", "Oba", "Obadiah", "OT"), ("Jonah", "Jon", "Jonah", "OT"),
    ("Mic", "Mic", "Micah", "OT"), ("Nah", "Nam", "Nahum", "OT"),
    ("Hab", "Hab", "Habakkuk", "OT"), ("Zeph", "Zep", "Zephaniah", "OT"),
    ("Hag", "Hag", "Haggai", "OT"), ("Zech", "Zec", "Zechariah", "OT"),
    ("Mal", "Mal", "Malachi", "OT"),
    ("Matt", "Mat", "Matthew", "NT"), ("Mark", "Mrk", "Mark", "NT"),
    ("Luke", "Luk", "Luke", "NT"), ("John", "Jhn", "John", "NT"),
    ("Acts", "Act", "Acts", "NT"), ("Rom", "Rom", "Romans", "NT"),
    ("1Cor", "1Co", "1 Corinthians", "NT"), ("2Cor", "2Co", "2 Corinthians", "NT"),
    ("Gal", "Gal", "Galatians", "NT"), ("Eph", "Eph", "Ephesians", "NT"),
    ("Phil", "Php", "Philippians", "NT"), ("Col", "Col", "Colossians", "NT"),
    ("1Thess", "1Th", "1 Thessalonians", "NT"), ("2Thess", "2Th", "2 Thessalonians", "NT"),
    ("1Tim", "1Ti", "1 Timothy", "NT"), ("2Tim", "2Ti", "2 Timothy", "NT"),
    ("Titus", "Tit", "Titus", "NT"), ("Phlm", "Phm", "Philemon", "NT"),
    ("Heb", "Heb", "Hebrews", "NT"), ("Jas", "Jas", "James", "NT"),
    ("1Pet", "1Pe", "1 Peter", "NT"), ("2Pet", "2Pe", "2 Peter", "NT"),
    ("1John", "1Jn", "1 John", "NT"), ("2John", "2Jn", "2 John", "NT"),
    ("3John", "3Jn", "3 John", "NT"), ("Jude", "Jud", "Jude", "NT"),
    ("Rev", "Rev", "Revelation", "NT"),
]
STEP_TO_OSIS = {step: osis for osis, step, _, _ in BOOKS}
OSIS_ORDER = {osis: i for i, (osis, _, _, _) in enumerate(BOOKS, start=1)}
OSIS_TESTAMENT = {osis: t for osis, _, _, t in BOOKS}

# Versification schemes used in this database.
ORG = "ORG"      # canonical key (Copenhagen Alliance original-language scheme)
KJV = "KJV"      # English KJV-style scheme used by BSB, Theographic (and NKJV)
NRSV = "NRSV"    # English scheme STEPBible uses as its base reference

STEP_REF_RE = re.compile(r"^([1-3A-Z][A-Za-z0-9]{2})\.(\d+)\.(\d+)([a-z]?)$")


def osis_ref(book: str, chapter: int, verse: int) -> str:
    return f"{book}.{chapter}.{verse}"


def step_ref_to_osis(ref: str) -> str | None:
    """'Exo.7.10a' -> 'Exod.7.10' (sub-verse letter dropped). None if not a ref."""
    m = STEP_REF_RE.match(ref.strip())
    if not m or m.group(1) not in STEP_TO_OSIS:
        return None
    return osis_ref(STEP_TO_OSIS[m.group(1)], int(m.group(2)), int(m.group(3)))


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def source_dir(source_id: str) -> Path:
    return CACHE_DIR / source_id


def source_file(source_id: str, rel: str) -> Path:
    return source_dir(source_id) / rel


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    return con
