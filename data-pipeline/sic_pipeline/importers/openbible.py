"""OpenBible.info cross references and Bible geocoding data.

Cross references: every row of cross_references.txt, with OpenBible's vote count.

Geocoding: every ancient place, the verses that name it, and every candidate
identification in the order OpenBible publishes them (sorted by its score).
Confidence is OpenBible's score.time_total, "best viewed as a fraction of 1000";
OpenBible states 500 or higher represents high confidence. For each
identification, the first resolution with coordinates supplies the map point.
"""
from __future__ import annotations

import html
import json
import re

from ..common import source_file

XREF_SRC = "openbible_xrefs"
XREF_FILE = "sources/extras/cross_references.txt"
GEO_SRC = "openbible_geo"
GEO_FILE = "data/ancient.jsonl"
TAG = re.compile(r"<[^>]+>")


def import_xrefs(con, report: dict) -> None:
    rows = {}
    with open(source_file(XREF_SRC, XREF_FILE), encoding="utf-8") as f:
        header = f.readline()
        if "openbible.info" not in header:
            raise SystemExit("OpenBible cross references: unexpected header line")
        for n, line in enumerate(f, start=2):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or not parts[0]:
                continue
            frm, to, votes = parts[0], parts[1], int(parts[2])
            start, _, end = to.partition("-")
            key = (frm, start, end or start)
            if key not in rows:
                rows[key] = (frm, start, end or start, votes, XREF_SRC, f"{XREF_FILE}:{n}")
    con.executemany("INSERT INTO xref VALUES (?,?,?,?,?,?)", sorted(rows.values()))
    report["openbible_xrefs"] = {"rows": len(rows)}


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG.sub("", text or ""))).strip()


def import_geo(con, report: dict) -> None:
    places, verses, idents = [], [], []
    no_point = 0
    with open(source_file(GEO_SRC, GEO_FILE), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            pid = r["id"]
            places.append((pid, r["friendly_id"], r.get("url_slug"), ",".join(r.get("types") or []) or None,
                           GEO_SRC, f"{GEO_FILE}#{pid}"))
            for v in r.get("verses") or []:
                verses.append((pid, v["osis"], GEO_SRC, f"{GEO_FILE}#{pid}.verses"))
            for rank, ident in enumerate(r.get("identifications") or [], start=1):
                lon = lat = point_type = None
                for res in ident.get("resolutions") or []:
                    if res.get("lonlat"):
                        lon_s, lat_s = res["lonlat"].split(",")
                        lon, lat, point_type = float(lon_s), float(lat_s), res.get("lonlat_type")
                        break
                if lon is None:
                    no_point += 1
                score = (ident.get("score") or {}).get("time_total")
                idents.append((pid, rank, _plain(ident.get("description")) or "(no description)",
                               score, lon, lat, point_type, GEO_SRC, f"{GEO_FILE}#{pid}.identifications[{rank - 1}]"))
    con.executemany("INSERT INTO geo_place VALUES (?,?,?,?,?,?)", sorted(places))
    con.executemany("INSERT OR IGNORE INTO geo_place_verse VALUES (?,?,?,?)", sorted(verses))
    con.executemany("INSERT INTO geo_identification VALUES (?,?,?,?,?,?,?,?,?)", sorted(idents))
    report["openbible_geo"] = {
        "places": len(places), "place_verse_links": len(set((v[0], v[1]) for v in verses)),
        "identifications": len(idents), "identifications_without_point": no_point,
    }
