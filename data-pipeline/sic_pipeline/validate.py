"""Validation checks run after every build (and in CI). Any failure fails the build.

Phase 1 exit check: BSB, STEPBible and Theographic import with zero unresolved
verse references.
"""
from __future__ import annotations

import json

from .common import KJV, NRSV, REPO_DIR, connect, load_manifest


def _tables_with_provenance(con) -> list[str]:
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'search_fts%'")]
    out = []
    for t in tables:
        cols = {r[1] for r in con.execute(f"PRAGMA table_info({t})")}
        if {"source_id", "record_id"} <= cols:
            out.append(t)
    return out


def run_checks(report: dict | None = None) -> dict:
    con = connect()
    checks: list[dict] = []

    def check(name: str, failures: list, detail: str = "") -> None:
        checks.append({"check": name, "passed": not failures, "failures": len(failures),
                       "examples": [str(x) for x in failures[:10]], "detail": detail})

    # 1. Referential integrity across the whole database.
    check("foreign keys resolve", list(con.execute("PRAGMA foreign_key_check")))

    # 2. Provenance on every content row.
    missing = []
    for t in _tables_with_provenance(con):
        n = con.execute(f"SELECT COUNT(*) FROM {t} WHERE source_id IS NULL OR record_id IS NULL OR TRIM(record_id)=''").fetchone()[0]
        if n:
            missing.append(f"{t}: {n} rows")
    check("every record has a source and record id", missing)

    # 3. Every source has a license, a license file and attribution text.
    bad_src = []
    for src in load_manifest()["sources"]:
        for key in ("license", "attribution", "license_file", "commit"):
            if not src.get(key):
                bad_src.append(f"{src['id']}: missing {key}")
        if src.get("license_file") and not (REPO_DIR / src["license_file"]).exists():
            bad_src.append(f"{src['id']}: {src['license_file']} not found")
    check("every source has license, license file and attribution", bad_src)

    # 4. Every BSB verse resolves to a canonical verse.
    unmapped_bsb = [r[0] for r in con.execute("""
        SELECT t.scheme_ref FROM verse_text t
        WHERE t.translation='BSB' AND NOT EXISTS (
          SELECT 1 FROM versification_map m WHERE m.scheme=? AND m.scheme_ref=t.scheme_ref)
        ORDER BY t.ord""", (KJV,))]
    check("every BSB verse resolves", unmapped_bsb)

    # 5. Every Theographic verse resolves.
    unmapped_theo = [r[0] for r in con.execute("""
        SELECT v.kjv_ref FROM sa_theo_verse v WHERE NOT EXISTS (
          SELECT 1 FROM versification_map m WHERE m.scheme=? AND m.scheme_ref=v.kjv_ref)""", (KJV,))]
    check("every Theographic verse resolves", unmapped_theo)

    # 6. Every Theographic person/place/event link points at a known verse.
    dangling_links = [r for r in con.execute("""
        SELECT l.kind, l.theo_id, l.theo_verse_id FROM sa_theo_link l
        LEFT JOIN sa_theo_verse v ON v.theo_id = l.theo_verse_id WHERE v.theo_id IS NULL""")]
    check("every Theographic verse link resolves", dangling_links)

    # 7. Every BSB word-alignment row belongs to a BSB verse.
    orphan_words = [r[0] for r in con.execute("""
        SELECT DISTINCT w.scheme_ref FROM bsb_word w WHERE NOT EXISTS (
          SELECT 1 FROM verse_text t WHERE t.translation='BSB' AND t.scheme_ref=w.scheme_ref)""")]
    check("every BSB word belongs to a BSB verse", orphan_words)

    # 8. Every TIPNR reference resolved.
    tipnr = (report or {}).get("tipnr", {})
    check("every TIPNR reference resolves", tipnr.get("unresolved_examples", []) if tipnr.get("unresolved_refs") else [],
          f"{tipnr.get('unresolved_refs', 'n/a')} unresolved")

    # 9. Coordinates are valid wherever present.
    bad_coords = [r for r in con.execute("""
        SELECT slug, latitude, longitude FROM sa_theo_place
        WHERE (latitude IS NULL) <> (longitude IS NULL)
           OR latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180""")]
    check("place coordinates are valid", bad_coords)

    # 10. Guard the OT versification assumption: STEPBible's English (NRSV-based) OT
    #     verse set equals the KJV-scheme OT verse set used by BSB and Theographic.
    nrsv_ot = {r[0] for r in con.execute("""
        SELECT DISTINCT m.scheme_ref FROM versification_map m JOIN book b ON m.scheme_ref LIKE b.osis || '.%'
        WHERE m.scheme=? AND b.testament='OT' AND m.scheme_ref NOT LIKE '%.0'""", (NRSV,))}
    bsb_ot = {r[0] for r in con.execute("""
        SELECT t.scheme_ref FROM verse_text t JOIN book b ON t.scheme_ref LIKE b.osis || '.%'
        WHERE t.translation='BSB' AND b.testament='OT' AND t.scheme_ref NOT LIKE '%.0'""")}
    diff = sorted(nrsv_ot ^ bsb_ot)
    check("OT English verse sets agree (STEPBible vs BSB)", diff,
          "OT KJV refs are taken from STEPBible's English refs; this check proves the two sets match.")

    # 11. Every canonical verse is reachable from the BSB (except psalm titles,
    #     which English Bibles print above verse 1 rather than numbering).
    unreachable = [r[0] for r in con.execute("""
        SELECT v.osis_ref FROM verse v WHERE NOT EXISTS (
          SELECT 1 FROM versification_map m JOIN verse_text t
            ON t.translation='BSB' AND t.scheme_ref = m.scheme_ref
          WHERE m.scheme=? AND m.osis_ref = v.osis_ref)
        AND NOT EXISTS (SELECT 1 FROM versification_map m2
          WHERE m2.scheme=? AND m2.osis_ref=v.osis_ref AND m2.scheme_ref LIKE '%.0')
        ORDER BY v.ord""", (KJV, KJV))]
    check("every canonical verse is reachable from a BSB verse or psalm title", unreachable)


    # 12. Psalm titles: every KJV-scheme superscription in the versification map
    #     has BSB title text, and every BSB title has a mapping.
    map_titles = {r[0] for r in con.execute(
        "SELECT DISTINCT scheme_ref FROM versification_map WHERE scheme=? AND scheme_ref LIKE 'Ps.%.0'", (KJV,))}
    bsb_titles = {r[0] for r in con.execute(
        "SELECT scheme_ref FROM verse_text WHERE translation='BSB' AND scheme_ref LIKE '%.0'")}
    check("psalm titles line up (BSB vs STEPBible)", sorted(map_titles ^ bsb_titles))

    # 13. Every cross reference endpoint resolves.
    # OpenBible uses English numbering; a few refs follow the NRSV/ESV split
    # (e.g. 3 John 1:15), so a ref may resolve through either English scheme.
    kjv_refs = {r[0] for r in con.execute(
        "SELECT DISTINCT scheme_ref FROM versification_map WHERE scheme IN (?,?)", (KJV, NRSV))}
    bad_x = [f"{a} -> {b}-{c}" for a, b, c in con.execute("SELECT from_ref, to_start, to_end FROM xref")
             if a not in kjv_refs or b not in kjv_refs or c not in kjv_refs]
    check("every cross reference resolves", bad_x)

    # 14. Every OpenBible place-verse link resolves; every point is a valid coordinate.
    bad_geo_v = [f"{p}: {r}" for p, r in con.execute("SELECT place_id, kjv_ref FROM geo_place_verse")
                 if r not in kjv_refs]
    check("every OpenBible place verse resolves", bad_geo_v)
    bad_pts = list(con.execute("""SELECT place_id, rank, lat, lon FROM geo_identification
        WHERE (lat IS NULL) <> (lon IS NULL) OR lat NOT BETWEEN -90 AND 90 OR lon NOT BETWEEN -180 AND 180"""))
    check("OpenBible coordinates are valid", bad_pts)

    con.close()
    result = {"passed": all(c["passed"] for c in checks), "checks": checks}
    return result


def print_result(result: dict) -> None:
    for c in result["checks"]:
        mark = "PASS" if c["passed"] else "FAIL"
        extra = f"  ({c['detail']})" if c["detail"] else ""
        print(f"  [{mark}] {c['check']}{extra}")
        if not c["passed"]:
            print(f"         {c['failures']} failures, e.g. {json.dumps(c['examples'][:5], ensure_ascii=False)}")
    print("Validation", "PASSED" if result["passed"] else "FAILED")
