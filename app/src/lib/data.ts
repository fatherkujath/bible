import type { Book, Chapter, EastonArticle, Source } from "./types";

// Simple in-memory cache on top of the browser/service-worker cache.
const memo = new Map<string, Promise<unknown>>();

function getJSON<T>(path: string): Promise<T> {
  if (!memo.has(path)) {
    const p = fetch(path).then((r) => {
      if (!r.ok) throw new Error(`Could not load ${path} (${r.status})`);
      return r.json();
    });
    p.catch(() => memo.delete(path));
    memo.set(path, p);
  }
  return memo.get(path) as Promise<T>;
}

export const loadBooks = () => getJSON<Book[]>("/data/books.json");
export const loadSources = () => getJSON<Source[]>("/data/attributions.json");
export const loadChapter = (id: string) => getJSON<Chapter>(`/data/ch/${id}.json`);
export const loadEaston = (id: string) => getJSON<EastonArticle>(`/data/easton/${id}.json`);
