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

- Everything comes from `BSB-osis.json`. Verse text is the verse with its `<title>` and
  `<note>` elements removed, tags stripped and whitespace collapsed. The build fails unless
  this text matches `BSB.json` (the plain edition) apart from psalm superscriptions and spacing.
- Psalm superscriptions (`<title type="psalm">`) are stored as verse 0, which maps to ORG verse 1.
  `BSB.json` joins them to verse 1; the OSIS file keeps them separate.
- Section headings (`<title>` with no type) and acrostic headings are kept verbatim. Parallel-passage
  and scope titles are not imported.
- Footnotes (`<note>`) are kept verbatim, as plain text, attached to their verse. The position of the
  note marker inside the verse is not kept.
- Word alignment is taken from the `<w>` tags: Strong's number, lemma, transliteration and the
  English words inside the tag. Tags with no Strong's number are skipped.

## OpenBible.info cross references

- Every row is imported with its vote count. Where the same from/to pair appears twice, the first is kept.
- References use English numbering. Most follow KJV numbering; a few follow the NRSV/ESV split
  (e.g. 3 John 1:15), so a reference resolves through either English scheme.
- The reader shows up to 12 per verse, highest votes first.

## OpenBible.info geocoding

- Every ancient place, the verses naming it, and every identification are imported in OpenBible's
  published order. Descriptions have their markup removed; wording is unchanged.
- The map point for an identification is the first of its resolutions that has coordinates.
- Confidence is OpenBible's `score.time_total` (a fraction of 1000). The reader shows it as a
  percentage. Styling: 500 or more (OpenBible's own "high confidence" threshold) solid; 100–499
  dashed; under 100 dotted. The 100 cut-off is this app's display choice.

## Theographic

- Theographic's KJV verse text and generated markup fields are not imported.
- `definitions.json` is not imported: its summaries carry AI model, batch and generation-date
  fields, so sourcing rule 1 excludes them.
- Easton's articles are linked to a chapter when the article itself cites a verse in it
  (its own scripture links). No other matching is done.
- Place coordinates are kept only when both latitude and longitude are present; five
  places with a latitude but no longitude are stored without coordinates (listed in
  the build report).
- Family links are imported from father, mother, children, siblings, partners and the
  two half-sibling fields.
- Every event is tagged with the chronology it follows so the app can label its dates.
