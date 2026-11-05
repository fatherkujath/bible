# Scripture in Context (working title)

A personal web app for studying the Bible in its historical, geographic, cultural and
linguistic setting, then carrying that study into prayer and obedience. Built from the
spec "Scripture in Context — Build Spec v2".

**Scripture is the anchor. Nothing is invented.** The app shows only content from the
sources in [ATTRIBUTIONS.md](ATTRIBUTIONS.md) or content you write yourself. Every record
keeps a pointer back to where it came from.

## Status

| Phase | State |
| --- | --- |
| 0. NKJV licensing (owner) | Not started: request access from API.Bible / HarperCollins |
| 1. Foundations | Done |
| 2. Passage Lens | **Built, awaiting owner review** |
| 3. Daily Walk | Next |

Phase 2 exit check: every chapter of every book loads, and every context tab shows
sourced content or "No sourced material yet." Run `python3 tools/check_chapters.py`
against the built site to see it pass. Hosting: see [DEPLOY.md](DEPLOY.md).

## Build the whole site

```bash
bash scripts/build-site.sh       # data pipeline + web app; output in app/out/
```

To preview locally: `cd app/out && python3 -m http.server 4173`, then open http://localhost:4173.

## Quick start (data only)

Requirements: Python 3.11+ and git. No Python packages to install.

```bash
cd data-pipeline
python -m sic_pipeline all        # fetch pinned sources, build, validate, write attributions
```

The first run downloads about 200 MB of source files into `data-pipeline/.cache/` and
takes a minute or two. Output:

- `data-pipeline/build/reference.db`: the SQLite reference database (about 190 MB)
- `data-pipeline/build/build-report.json`: counts, skipped items and validation results
- `data-pipeline/build/attributions.json`: data for the in-app Attributions page

Other commands: `fetch`, `build`, `validate`, `attributions`, `lock` (after editing
`sources.json`), and `reproduce` (builds twice and compares content hashes).

## Layout

```
data-pipeline/
  sources.json                 data manifest: pinned commits, files, licenses, attribution
  sources.lock.json            SHA-256 of every source file (verified on every fetch)
  expected-content.sha256      content hash of a correct build (checked in CI)
  CHANGES-TO-SOURCE-DATA.md    every way the pipeline selects, skips or maps source data
  sic_pipeline/
    schema.sql                 reference database schema
    importers/                 one importer per source
    validate.py                validation checks (any failure fails the build)
licenses/                      license text or terms for each source
app/                           Next.js reader (static export to app/out/)
  public/data/                 per-chapter JSON written by the pipeline (not committed)
scripts/build-site.sh          one command that builds everything (used by Cloudflare Pages)
tools/check_chapters.py        Phase 2 exit check over every chapter
.github/workflows/             CI: fetch, build, validate, hash and attribution checks
ATTRIBUTIONS.md                generated from the manifest; do not edit by hand
```

## How references work

Every dataset is mapped to one canonical verse key: OSIS book codes with the Copenhagen
Alliance ORG versification (Hebrew numbering for the OT, Greek numbering for the NT).
Translations keep their own numbering (BSB, Theographic and NKJV use KJV-style numbering)
and reach canonical verses through `versification_map`. For example, BSB Joel 2:28 maps to
Joel 3:1, Malachi 4:1 to Malachi 3:19, and Psalm 3:1 to Psalm 3:2 (the superscription is 3:1).

## Data rules the pipeline enforces

- Source files are fetched at pinned commits and verified against `sources.lock.json`.
  They are not committed to this repo; STEPBible asks that its files not be re-posted.
- Share-alike (CC BY-SA) material lives in `sa_` tables.
- AI-written source content is excluded. STEPBible's TIPNR person and place descriptions
  are labeled by STEPBible as created by Claude 3, so they are not imported.
- Content needing separate permission is excluded: the TBESH "Meaning" column (Abridged
  BDB, © Online Bible).

## Known gaps

- **Study notes:** Tyndale Open Study Notes and Bible Dictionary are waiting for Tyndale's original
  files. The only copy reachable from the build environment is Mission Mutual's rewritten
  "Aquifer" adaptation, which the owner chose not to use. Until then, the World tab shows
  "No sourced material yet." for study notes, and Culture and terms uses Easton's (1897).
- **Rulers:** no listed source gives rulers by period yet; the World tab says so.
- **Greek definitions:** TBESG definitions are not imported (digitization license unchecked);
  glosses are available for Hebrew and Greek.
- **TIPNR:** three malformed reference tokens are skipped and listed in the build report;
  report them to STEPBible.
- **Offline:** chapters you have opened are cached for offline reading. A "download everything
  for offline" option is planned.
