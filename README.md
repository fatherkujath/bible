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
| 1. Foundations | **Done, awaiting owner review** |
| 2. Passage Lens | Next |

Phase 1 exit check: BSB, STEPBible and Theographic import with zero unresolved verse
references. Run `python -m sic_pipeline all` to see it pass.

## Quick start

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
app/                           Next.js app (from Phase 2)
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

## Known issues for Phase 2

- BSB psalm superscriptions are joined to verse 1 in `BSB.json`; the reader will split them
  using the `<title>` element in `BSB-osis.json`.
- TBESG Greek definitions are not yet imported (their upstream digitization license needs checking);
  glosses are available for both Hebrew and Greek.
- Three malformed tokens in TIPNR reference columns are skipped and listed in the build report;
  they should be reported to STEPBible.
