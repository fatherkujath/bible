"""Build reference.db from the pinned, verified sources."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .common import BOOKS, BUILD_DIR, DB_PATH, REPORT_PATH, connect, load_manifest
from .importers.bsb import import_bsb
from .importers.openbible import import_geo, import_xrefs
from .importers.step_lexicon import import_lexicons
from .importers.step_texts import import_step_texts
from .importers.theographic import import_theographic
from .importers.tipnr import import_tipnr

SCHEMA = Path(__file__).with_name("schema.sql")


def build() -> dict:
    manifest = load_manifest()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for p in (DB_PATH, DB_PATH.with_suffix(".db-journal")):
        p.unlink(missing_ok=True)
    con = connect()
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    report: dict = {"sources": {}}

    with con:
        for s in manifest["sources"]:
            con.execute("INSERT INTO source VALUES (?,?,?,?,?,?,?,?)",
                        (s["id"], s["name"], s["repo"], s["commit"], s["license"],
                         s["license_group"], s["attribution"], s["homepage"]))
            report["sources"][s["id"]] = s["commit"]
        con.executemany("INSERT INTO book VALUES (?,?,?,?,?)",
                        [(o, st, n, i, t) for i, (o, st, n, t) in enumerate(BOOKS, start=1)])
        print("  importing STEPBible original-language texts (verses, versification, words)")
        import_step_texts(con, report)
        print("  importing STEPBible lexicons")
        import_lexicons(con, report)
        print("  importing STEPBible TIPNR proper names")
        import_tipnr(con, report)
        print("  importing Berean Standard Bible")
        import_bsb(con, report)
        print("  importing Theographic")
        import_theographic(con, report)
        print("  importing OpenBible cross references and places")
        import_xrefs(con, report)
        import_geo(con, report)
        con.executemany("INSERT INTO build_info VALUES (?,?)", [
            ("schema_sha256", hashlib.sha256(SCHEMA.read_bytes()).hexdigest()),
            ("sources", json.dumps(report["sources"], sort_keys=True)),
        ])
    con.execute("VACUUM")
    con.close()
    report["content_sha256"] = content_hash()
    return report


def content_hash() -> str:
    """Hash of the database's logical content (SQL dump), used to prove that a
    rebuild from scratch produces the same data."""
    con = connect()
    h = hashlib.sha256()
    for line in con.iterdump():
        h.update(line.encode("utf-8"))
        h.update(b"\n")
    con.close()
    return h.hexdigest()


def write_report(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
