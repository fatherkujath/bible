"""Generate ATTRIBUTIONS.md (repo root) and build/attributions.json (for the
in-app Attributions page) from the data manifest."""
from __future__ import annotations

import json

from .common import BUILD_DIR, REPO_DIR, load_manifest

GROUP_LABEL = {
    "open": "Open (public domain, CC0 or CC BY)",
    "share-alike": "Share-alike (CC BY-SA) — kept in separate sa_ tables",
    "licensed": "Licensed (not bundled)",
    "isolated": "Isolated layer (separate license)",
}


def generate() -> None:
    sources = load_manifest()["sources"]
    lines = [
        "# Attributions",
        "",
        "Generated from `data-pipeline/sources.json` by `python -m sic_pipeline attributions`. Do not edit by hand.",
        "",
        "Scripture in Context displays only content from the sources below or written by the user.",
        "Each record in the reference database stores the source it came from.",
        "",
    ]
    for group in GROUP_LABEL:
        group_sources = [s for s in sources if s["license_group"] == group]
        if not group_sources:
            continue
        lines += [f"## {GROUP_LABEL[group]}", ""]
        for s in group_sources:
            lines += [
                f"### {s['name']}",
                "",
                f"- **License:** {s['license']} (full text: `{s['license_file']}`)",
                f"- **Credit:** {s['attribution']}",
                f"- **Source:** {s['repo']} at commit `{s['commit']}`",
                f"- **Homepage:** {s['homepage']}",
            ]
            if s.get("notes"):
                lines.append(f"- **Notes:** {s['notes']}")
            lines.append("")
    (REPO_DIR / "ATTRIBUTIONS.md").write_text("\n".join(lines), encoding="utf-8")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    public = [{k: s[k] for k in ("id", "name", "license", "license_group", "attribution", "homepage", "repo", "commit")}
              for s in sources]
    (BUILD_DIR / "attributions.json").write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("  wrote ATTRIBUTIONS.md and build/attributions.json")
