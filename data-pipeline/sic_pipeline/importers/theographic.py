"""Theographic Bible Metadata (CC BY-SA 4.0) into the sa_ (share-alike) tables.

Imported: people, places, events, their verse links, family links, event
participants and locations, per-verse years, and the Easton's Bible Dictionary
entries Theographic distributes. Theographic's own KJV verse text is not used.

Dates follow Theographic's single chronology; every event row records that in
its `chronology` column so the app can label it (sourcing rule 4).
"""
from __future__ import annotations

import json

from ..common import source_file

SRC = "theographic"
CHRONOLOGY = "Theographic (single chronology; Ussher-style, creation 4003 BC)"
FAMILY = {
    "father": "father", "mother": "mother", "children": "child", "siblings": "sibling",
    "partners": "partner", "halfSiblingsSameMother": "half-sibling (same mother)",
    "halfSiblingsSameFather": "half-sibling (same father)",
}


def _load(name: str) -> list:
    return json.loads(source_file(SRC, f"json/{name}.json").read_text(encoding="utf-8"))


def _int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _coords(f: dict):
    """Theographic latitude/longitude, only when both are present."""
    lat, lon = _float(f.get("latitude")), _float(f.get("longitude"))
    return (lat, lon) if lat is not None and lon is not None else (None, None)


def import_theographic(con, report: dict) -> None:
    verses = _load("verses")
    con.executemany(
        "INSERT INTO sa_theo_verse VALUES (?,?,?,?,?)",
        sorted((r["id"], r["fields"]["osisRef"], _int(r["fields"].get("yearNum")), SRC, f"verses.json#{r['id']}")
               for r in verses),
    )

    people = _load("people")
    con.executemany("INSERT INTO sa_theo_person VALUES (?,?,?,?,?,?,?,?,?,?)", sorted(
        (r["id"], f["slug"], f["name"], f.get("displayTitle"), f.get("gender"),
         _int(f.get("birthYear")), _int(f.get("deathYear")), f.get("alsoCalled"),
         SRC, f"people.json#{r['id']}")
        for r in people for f in [r["fields"]]))

    places = _load("places")
    con.executemany("INSERT INTO sa_theo_place VALUES (?,?,?,?,?,?,?,?,?,?)", sorted(
        (r["id"], f["slug"], f.get("displayTitle") or f.get("kjvName"), f.get("featureType"),
         *_coords(f), f.get("precision"), f.get("comment"),
         SRC, f"places.json#{r['id']}")
        for r in places for f in [r["fields"]]))

    events = _load("events")
    con.executemany("INSERT INTO sa_theo_event VALUES (?,?,?,?,?,?,?,?)", sorted(
        (r["id"], f["title"], f.get("startDate"), f.get("duration"), _float(f.get("sortKey")),
         CHRONOLOGY, SRC, f"events.json#{r['id']}")
        for r in events for f in [r["fields"]]))

    links = set()
    for kind, rows in (("person", people), ("place", places), ("event", events)):
        for r in rows:
            for vid in r["fields"].get("verses", []):
                links.add((kind, r["id"], vid, SRC, f"{kind}:{r['id']}"))
    con.executemany("INSERT INTO sa_theo_link VALUES (?,?,?,?,?)", sorted(links))

    person_ids = {r["id"] for r in people}
    relations, dangling = set(), 0
    for r in people:
        for field, rel in FAMILY.items():
            for other in r["fields"].get(field, []) or []:
                if other in person_ids:
                    relations.add((r["id"], rel, other, SRC, f"people.json#{r['id']}.{field}"))
                else:
                    dangling += 1
    con.executemany("INSERT INTO sa_theo_relation VALUES (?,?,?,?,?)", sorted(relations))

    parts = set()
    for r in events:
        for pid in r["fields"].get("participants", []) or []:
            parts.add((r["id"], "participant", pid, SRC, f"events.json#{r['id']}.participants"))
        for lid in r["fields"].get("locations", []) or []:
            parts.add((r["id"], "location", lid, SRC, f"events.json#{r['id']}.locations"))
    con.executemany("INSERT INTO sa_theo_event_part VALUES (?,?,?,?,?)", sorted(parts))

    easton = _load("easton")
    erows = sorted(
        (r["id"], f["termID"], f["termLabel"], f["dictText"], ",".join(f.get("personLookup") or []) or None, ",".join(f.get("placeLookup") or []) or None,
         SRC, f"easton.json#{r['id']}")
        for r in easton for f in [r["fields"]] if f.get("dictText"))
    con.executemany("INSERT INTO sa_easton VALUES (?,?,?,?,?,?,?,?)", erows)
    con.executemany(
        "INSERT INTO search_fts(kind, ref, title, body) VALUES ('easton', ?, ?, ?)",
        [(r[0], r[2], r[3]) for r in erows],
    )
    report["theographic"] = {
        "verses": len(verses), "people": len(people), "places": len(places), "events": len(events),
        "verse_links": len(links), "family_links": len(relations), "family_links_to_missing_people": dangling,
        "places_with_incomplete_coordinates_dropped": sorted(
            r["fields"]["slug"] for r in places
            if ("latitude" in r["fields"]) != ("longitude" in r["fields"])),
        "event_parts": len(parts), "easton_entries": len(erows),
        "easton_entries_without_text": len(easton) - len(erows),
    }
