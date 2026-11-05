// Shapes of the static JSON written by `python -m sic_pipeline export`.
// Every card-level object carries `src` (source id) and `rec` (upstream record id).

export type Book = { osis: string; name: string; testament: "OT" | "NT"; chapters: number[] };

export type Source = {
  id: string;
  name: string;
  license: string;
  license_group: string;
  attribution: string;
  homepage: string;
  repo: string;
  commit: string;
  notes?: string;
};

/** BSB alignment word: [english, strongs, lemma, translit, ...lexiconKeys] */
export type AlignedWord = [string | null, string, string | null, string | null, ...string[]];

export type Verse = {
  n: number; // 0 = psalm superscription
  ref: string;
  text: string;
  rec: string;
  org: string[];
  h: { kind: "section" | "acrostic"; text: string }[];
  notes: string[];
  w: AlignedWord[];
};

export type OriginalWord = {
  o: string; x: string | null; g: string | null; s: string | null;
  m: string | null; l: string | null; t: string; e: string | null; rec: string;
};

export type OriginalVerse = { org: string; lang: "Hebrew" | "Greek"; kjv: number[]; words: OriginalWord[] };

export type LexEntry = {
  lemma: string; tr: string | null; morph: string | null; gloss: string | null;
  lang: "Hebrew" | "Greek"; src: string; rec: string;
};

export type WorldEvent = {
  id: string; title: string; start: string | null; duration: string | null;
  verses: number[]; src: string; rec: string;
};

export type Person = {
  id: string; name: string; type: string | null; verses: number[];
  rel: Partial<Record<"parent" | "sibling" | "partner" | "offspring", string[]>>;
  src: string; rec: string;
};

export type Identification = {
  rank: number; desc: string; conf: number | null; lat: number | null; lon: number | null;
  pt: string | null; rec: string;
};

export type Place = {
  id: string; name: string; slug: string | null; types: string | null; verses: number[];
  ids: Identification[]; src: string; rec: string; url: string | null;
};

export type Term = { id: string; term: string; verses: number[]; src: string; rec: string };

/** [toStart, toEnd, votes, rec] */
export type XRef = [string, string, number, string];

export type Chapter = {
  book: string;
  chapter: number;
  prev: string | null;
  next: string | null;
  verses: Verse[];
  original: OriginalVerse[];
  lex: Record<string, LexEntry>;
  world: {
    years: { year: number; verses: number[] }[];
    chronology: string;
    events: WorldEvent[];
    studyNotes: null;
  };
  people: Person[];
  names: Person[];
  places: Place[];
  terms: Term[];
  xrefs: Record<string, XRef[]>;
};

export type EastonArticle = { id: string; term: string; body: string; src: string; rec: string };
