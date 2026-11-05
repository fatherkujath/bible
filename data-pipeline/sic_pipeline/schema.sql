-- Scripture in Context reference database (read-only in the app).
-- Rebuilt from scratch by `python -m sic_pipeline build`; never holds user data.
--
-- Conventions
--   * osis_ref columns use OSIS book codes and the ORG (original-language) versification,
--     e.g. 'Ps.3.2'. Translations keep their own numbering in *_ref columns and reach
--     ORG through versification_map.
--   * Every content row carries source_id (-> source) and record_id (the upstream
--     record's own identifier), so any value in the app can be traced to its origin.
--   * Tables prefixed sa_ hold CC BY-SA (share-alike) material, kept apart so its
--     obligations are easy to honor if the app is ever shared.

CREATE TABLE source (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  repo          TEXT NOT NULL,
  version       TEXT NOT NULL,            -- pinned git commit
  license       TEXT NOT NULL,
  license_group TEXT NOT NULL CHECK (license_group IN ('open','share-alike','licensed','isolated')),
  attribution   TEXT NOT NULL,
  homepage      TEXT NOT NULL
);

CREATE TABLE book (
  osis      TEXT PRIMARY KEY,
  step_code TEXT NOT NULL UNIQUE,
  name      TEXT NOT NULL,
  ord       INTEGER NOT NULL UNIQUE,
  testament TEXT NOT NULL CHECK (testament IN ('OT','NT'))
);

-- Canonical verses (ORG scheme). Derived from the STEPBible original-language texts.
CREATE TABLE verse (
  osis_ref  TEXT PRIMARY KEY,
  book      TEXT NOT NULL REFERENCES book(osis),
  chapter   INTEGER NOT NULL,
  verse     INTEGER NOT NULL,
  ord       INTEGER NOT NULL UNIQUE,
  source_id TEXT NOT NULL REFERENCES source(id),
  record_id TEXT NOT NULL
);

-- Maps a reference in a translation's own numbering to one or more ORG verses.
-- scheme: 'KJV' (BSB, Theographic, NKJV) or 'NRSV' (STEPBible base refs).
-- Verse 0 in an English scheme is a psalm superscription (title).
CREATE TABLE versification_map (
  scheme     TEXT NOT NULL,
  scheme_ref TEXT NOT NULL,
  osis_ref   TEXT NOT NULL REFERENCES verse(osis_ref),
  source_id  TEXT NOT NULL REFERENCES source(id),
  record_id  TEXT NOT NULL,
  PRIMARY KEY (scheme, scheme_ref, osis_ref)
);
CREATE INDEX versification_map_org ON versification_map(osis_ref);

-- Verse text per translation, in that translation's numbering.
CREATE TABLE verse_text (
  translation TEXT NOT NULL,
  scheme      TEXT NOT NULL,
  scheme_ref  TEXT NOT NULL,
  ord         INTEGER NOT NULL,
  text        TEXT NOT NULL,
  source_id   TEXT NOT NULL REFERENCES source(id),
  record_id   TEXT NOT NULL,
  PRIMARY KEY (translation, scheme_ref)
);

-- BSB English-to-original word alignment (from the BSB OSIS word tags).
CREATE TABLE bsb_word (
  scheme_ref TEXT NOT NULL,
  position   INTEGER NOT NULL,
  english    TEXT,                       -- NULL when the original word is untranslated
  strongs    TEXT NOT NULL,
  lemma      TEXT,
  translit   TEXT,
  source_id  TEXT NOT NULL REFERENCES source(id),
  record_id  TEXT NOT NULL,
  PRIMARY KEY (scheme_ref, position)
);

-- Original-language words (STEPBible TAHOT / TAGNT).
CREATE TABLE word (
  record_id  TEXT NOT NULL,              -- e.g. 'Gen.31.55(32.1)#01'
  osis_ref   TEXT NOT NULL REFERENCES verse(osis_ref),
  position   INTEGER NOT NULL,
  text_type  TEXT NOT NULL,              -- L/Q/K/R/X (OT) or NKO etc. (NT), see STEPBible docs
  original   TEXT NOT NULL,
  translit   TEXT,
  gloss      TEXT,
  strongs    TEXT,                       -- dStrong tag(s) as published
  morph      TEXT,
  lemma      TEXT,                       -- NT dictionary form
  editions   TEXT,                       -- NT editions containing the word
  source_id  TEXT NOT NULL REFERENCES source(id),
  PRIMARY KEY (source_id, record_id)
);
CREATE INDEX word_verse ON word(osis_ref, position);

-- Brief lexicons (STEPBible TBESH / TBESG). Gloss only in Phase 1; see notes.
CREATE TABLE lexicon (
  dstrong   TEXT PRIMARY KEY,
  estrong   TEXT NOT NULL,
  ustrong   TEXT,
  language  TEXT NOT NULL CHECK (language IN ('Hebrew','Greek')),
  lemma     TEXT NOT NULL,
  translit  TEXT,
  morph     TEXT,
  gloss     TEXT,
  source_id TEXT NOT NULL REFERENCES source(id),
  record_id TEXT NOT NULL
);

-- Proper names (STEPBible TIPNR). Descriptions are deliberately not imported.
CREATE TABLE name_entity (
  unique_name TEXT PRIMARY KEY,           -- e.g. 'Aaron@Exo.4.14-Heb'
  kind        TEXT NOT NULL CHECK (kind IN ('person','place','other')),
  ustrong     TEXT,
  type        TEXT,                       -- e.g. Male / Female / place type as published
  source_id   TEXT NOT NULL REFERENCES source(id),
  record_id   TEXT NOT NULL
);
CREATE TABLE name_form (
  unique_name  TEXT NOT NULL REFERENCES name_entity(unique_name),
  significance TEXT NOT NULL,
  dstrong      TEXT,
  original     TEXT,
  translated   TEXT,
  source_id    TEXT NOT NULL REFERENCES source(id),
  record_id    TEXT NOT NULL
);
CREATE TABLE name_ref (
  unique_name TEXT NOT NULL REFERENCES name_entity(unique_name),
  osis_ref    TEXT NOT NULL REFERENCES verse(osis_ref),
  source_id   TEXT NOT NULL REFERENCES source(id),
  record_id   TEXT NOT NULL,
  PRIMARY KEY (unique_name, osis_ref)
);
CREATE INDEX name_ref_verse ON name_ref(osis_ref);
CREATE TABLE name_relation (
  unique_name TEXT NOT NULL REFERENCES name_entity(unique_name),
  relation    TEXT NOT NULL CHECK (relation IN ('parent','sibling','partner','offspring')),
  other_name  TEXT NOT NULL,              -- TIPNR unique name as published
  source_id   TEXT NOT NULL REFERENCES source(id),
  record_id   TEXT NOT NULL,
  PRIMARY KEY (unique_name, relation, other_name)
);

-- ---------------------------------------------------------------- share-alike
-- Theographic Bible Metadata (CC BY-SA 4.0). Dates follow Theographic's single
-- chronology and must be labeled as such in the app.
CREATE TABLE sa_theo_verse (
  theo_id    TEXT PRIMARY KEY,
  kjv_ref    TEXT NOT NULL,
  year_num   INTEGER,                     -- per Theographic chronology; negative = BC
  source_id  TEXT NOT NULL REFERENCES source(id),
  record_id  TEXT NOT NULL
);
CREATE TABLE sa_theo_person (
  theo_id     TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  display     TEXT,
  gender      TEXT,
  birth_year  INTEGER,
  death_year  INTEGER,
  also_called TEXT,
  source_id   TEXT NOT NULL REFERENCES source(id),
  record_id   TEXT NOT NULL
);
CREATE TABLE sa_theo_place (
  theo_id      TEXT PRIMARY KEY,
  slug         TEXT NOT NULL UNIQUE,
  name         TEXT NOT NULL,
  feature_type TEXT,
  latitude     REAL,
  longitude    REAL,
  precision    TEXT,
  comment      TEXT,
  source_id    TEXT NOT NULL REFERENCES source(id),
  record_id    TEXT NOT NULL
);
CREATE TABLE sa_theo_event (
  theo_id    TEXT PRIMARY KEY,
  title      TEXT NOT NULL,
  start_date TEXT,
  duration   TEXT,
  sort_key   REAL,
  chronology TEXT NOT NULL,
  source_id  TEXT NOT NULL REFERENCES source(id),
  record_id  TEXT NOT NULL
);
-- Links from Theographic records to verses (kept in the KJV scheme Theographic uses).
CREATE TABLE sa_theo_link (
  kind      TEXT NOT NULL CHECK (kind IN ('person','place','event')),
  theo_id   TEXT NOT NULL,
  theo_verse_id TEXT NOT NULL REFERENCES sa_theo_verse(theo_id),
  source_id TEXT NOT NULL REFERENCES source(id),
  record_id TEXT NOT NULL,
  PRIMARY KEY (kind, theo_id, theo_verse_id)
);
CREATE TABLE sa_theo_relation (
  person_id TEXT NOT NULL REFERENCES sa_theo_person(theo_id),
  relation  TEXT NOT NULL,
  other_id  TEXT NOT NULL REFERENCES sa_theo_person(theo_id),
  source_id TEXT NOT NULL REFERENCES source(id),
  record_id TEXT NOT NULL,
  PRIMARY KEY (person_id, relation, other_id)
);
CREATE TABLE sa_theo_event_part (
  event_id  TEXT NOT NULL REFERENCES sa_theo_event(theo_id),
  role      TEXT NOT NULL CHECK (role IN ('participant','location')),
  other_id  TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES source(id),
  record_id TEXT NOT NULL,
  PRIMARY KEY (event_id, role, other_id)
);
-- Easton's Bible Dictionary entries as distributed by Theographic. Verbatim.
CREATE TABLE sa_easton (
  theo_id    TEXT PRIMARY KEY,
  term_id    TEXT NOT NULL,
  term       TEXT NOT NULL,
  body       TEXT NOT NULL,
  person_ids TEXT,                      -- Theographic person record ids, comma-separated
  place_ids  TEXT,                      -- Theographic place record ids, comma-separated
  source_id  TEXT NOT NULL REFERENCES source(id),
  record_id  TEXT NOT NULL
);

-- Full-text search over reference text (translation text and dictionary articles).
CREATE VIRTUAL TABLE search_fts USING fts5(kind, ref, title, body, tokenize = 'unicode61');

CREATE TABLE build_info (key TEXT PRIMARY KEY, value TEXT NOT NULL);
