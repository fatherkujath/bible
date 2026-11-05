# Changes to source data

STEPBible asks anyone who changes its data to publish a note of those changes. This
file lists every way the pipeline transforms, skips or reinterprets source data, for
all sources. Content is never reworded; changes are limited to structure, selection
and reference mapping.

## All sources

- Records are reshaped into the tables in `sic_pipeline/schema.sql`. Each row keeps the
  upstream record's identifier in `record_id`.
- Verse references are converted to OSIS book codes and mapped to the Copenhagen
  Alliance ORG versification (Hebrew numbering for the OT, Greek NA numbering for the NT).

## STEPBible (TAHOT, TAGNT, TBESH, TBESG, TIPNR)

- **Canonical verses and versification** are derived from TAHOT/TAGNT reference columns:
  base reference = NRSV English numbering; OT Hebrew numbering in `( )`; NT KJV numbering
  in `[ ]`, NA numbering in `( )`. Curly-bracket `{ }` traditions are not used.
- **OT KJV numbering** is taken to equal STEPBible's English (NRSV-based) numbering.
  Validation proves the two OT verse sets are identical for the BSB; it does not prove
  that every verse boundary falls on the same word. A TVTMS cross-check is planned with
  the NKJV integration phase.
- **TAGNT** fields are split: `Greek (translit)` into two columns, `dStrongs=Grammar` into
  Strong's and morphology, `Dictionary=Gloss` keeps the dictionary form only (the English
  column is used as the gloss). Spanish translation, sub-meaning and alternate Strong's
  columns are not imported.
- **TBESH / TBESG**: only Strong's numbers, lemma, transliteration, morph and gloss are
  imported. Not imported:
  - TBESH `Meaning` (Abridged BDB, © Online Bible; the file header asks for Online Bible's
    permission before use).
  - TBESG definitions (Abbott-Smith digitization; license not yet checked).
  When a dStrong appears on several lines, the first line is kept.
- **TIPNR**: unique names, name forms, references and family links are imported. Not imported:
  - The Description column, `#Summary description`, and the `@Briefest`, `@Brief`,
    `@Short`, `@Article` lines. STEPBible's README says these descriptions were created by
    Claude 3 AI; sourcing rule 1 excludes AI-written content.
  - Place header fields (map links, geographical area). Place coordinates will come from
    OpenBible.info directly in the Atlas phase.
  - Septuagint references (`LXX.…`), which fall outside the 66-book canon's numbering.
    The build report counts them.
  - Three tokens in reference columns that are not references at the pinned commit:
    `@` (Achaicus), `16` (Joshua), `etc` (LORD). These are listed in the build report
    and should be reported to STEPBible. Any new non-reference token fails validation.
  - Six references to `2Co.13.14` use KJV numbering where STEPBible's base is NRSV
    (which has 13 verses in 2 Corinthians 13). They are resolved through the KJV
    mapping and listed in the build report.

## Berean Standard Bible

- Verse text is taken from `BSB.json` as published (whitespace trimmed).
- Word alignment is taken from the `<w>` tags in `BSB-osis.json`: Strong's number, lemma,
  transliteration and the English words inside the tag. Tags with no Strong's number are skipped.
- **Known issue:** in `BSB.json`, psalm superscriptions are joined to the start of
  verse 1 (e.g. Ps 3:1 begins "A Psalm of David, when he fled…"). The superscription
  belongs to ORG verse 1 and the rest to ORG verse 2. The Passage Lens phase will split
  them using the `<title>` element in `BSB-osis.json`.

## Theographic

- Theographic's KJV verse text and generated markup fields are not imported.
- Place coordinates are kept only when both latitude and longitude are present; five
  places with a latitude but no longitude are stored without coordinates (listed in
  the build report).
- Family links are imported from father, mother, children, siblings, partners and the
  two half-sibling fields.
- Every event is tagged with the chronology it follows so the app can label its dates.
