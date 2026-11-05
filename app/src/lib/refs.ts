import type { Book } from "./types";

// Display names for OSIS book codes (BSB naming).
export const BOOK_NAMES: Record<string, string> = {
  Gen: "Genesis", Exod: "Exodus", Lev: "Leviticus", Num: "Numbers", Deut: "Deuteronomy",
  Josh: "Joshua", Judg: "Judges", Ruth: "Ruth", "1Sam": "1 Samuel", "2Sam": "2 Samuel",
  "1Kgs": "1 Kings", "2Kgs": "2 Kings", "1Chr": "1 Chronicles", "2Chr": "2 Chronicles",
  Ezra: "Ezra", Neh: "Nehemiah", Esth: "Esther", Job: "Job", Ps: "Psalms", Prov: "Proverbs",
  Eccl: "Ecclesiastes", Song: "Song of Songs", Isa: "Isaiah", Jer: "Jeremiah", Lam: "Lamentations",
  Ezek: "Ezekiel", Dan: "Daniel", Hos: "Hosea", Joel: "Joel", Amos: "Amos", Obad: "Obadiah",
  Jonah: "Jonah", Mic: "Micah", Nah: "Nahum", Hab: "Habakkuk", Zeph: "Zephaniah", Hag: "Haggai",
  Zech: "Zechariah", Mal: "Malachi", Matt: "Matthew", Mark: "Mark", Luke: "Luke", John: "John",
  Acts: "Acts", Rom: "Romans", "1Cor": "1 Corinthians", "2Cor": "2 Corinthians", Gal: "Galatians",
  Eph: "Ephesians", Phil: "Philippians", Col: "Colossians", "1Thess": "1 Thessalonians",
  "2Thess": "2 Thessalonians", "1Tim": "1 Timothy", "2Tim": "2 Timothy", Titus: "Titus",
  Phlm: "Philemon", Heb: "Hebrews", Jas: "James", "1Pet": "1 Peter", "2Pet": "2 Peter",
  "1John": "1 John", "2John": "2 John", "3John": "3 John", Jude: "Jude", Rev: "Revelation",
};

export function parseRef(ref: string): { book: string; chapter: number; verse: number } | null {
  const m = /^([1-3]?[A-Za-z]+)\.(\d+)\.(\d+)$/.exec(ref);
  return m ? { book: m[1], chapter: Number(m[2]), verse: Number(m[3]) } : null;
}

/** 'Prov.8.22','Prov.8.30' -> 'Proverbs 8:22–30' */
export function formatRange(start: string, end: string): string {
  const a = parseRef(start);
  const b = parseRef(end);
  if (!a) return start;
  const name = BOOK_NAMES[a.book] ?? a.book;
  const first = `${name} ${a.chapter}:${a.verse}`;
  if (!b || (a.book === b.book && a.chapter === b.chapter && a.verse === b.verse)) return first;
  if (a.book === b.book && a.chapter === b.chapter) return `${first}–${b.verse}`;
  if (a.book === b.book) return `${first}–${b.chapter}:${b.verse}`;
  return `${first} – ${BOOK_NAMES[b.book] ?? b.book} ${b.chapter}:${b.verse}`;
}

export function chapterLabel(id: string): string {
  const [book, ch] = id.split(".");
  return `${book === "Ps" ? "Psalm" : (BOOK_NAMES[book] ?? book)} ${ch}`;
}

export function chapterHref(id: string, verse?: number): string {
  return `/read/${id}/${verse ? `#v${verse}` : ""}`;
}

export function refHref(ref: string): string {
  const r = parseRef(ref);
  return r ? chapterHref(`${r.book}.${r.chapter}`, r.verse) : "/";
}

/** Verse list for display: [3,4,5,9] -> 'vv. 3–5, 9' */
export function verseList(vs: number[]): string {
  if (!vs.length) return "";
  const parts: string[] = [];
  let start = vs[0];
  let prev = vs[0];
  for (const v of [...vs.slice(1), Infinity]) {
    if (v === prev + 1) { prev = v; continue; }
    parts.push(start === prev ? (start === 0 ? "title" : `${start}`) : `${start}–${prev}`);
    start = prev = v;
  }
  return `${vs.length === 1 ? "v." : "vv."} ${parts.join(", ")}`;
}

export function yearLabel(y: number): string {
  return y < 0 ? `${-y} BC` : `AD ${y}`;
}

export function allChapterIds(books: Book[]): string[] {
  return books.flatMap((b) => b.chapters.map((c) => `${b.osis}.${c}`));
}

/** OpenBible name: 'Bethany 2' -> { base: 'Bethany', n: '2' } (disambiguation number as published). */
export function splitPlaceName(name: string): { base: string; n: string | null } {
  const m = /^(.*?)\s(\d+)$/.exec(name);
  return m ? { base: m[1], n: m[2] } : { base: name, n: null };
}

/** STEPBible unique name 'Aaron@Exo.4.14-Heb' -> 'Aaron' */
export function tipnrName(unique: string): string {
  return unique.split("@")[0];
}
