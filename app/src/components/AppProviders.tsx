"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { loadBooks, loadSources } from "@/lib/data";
import type { Book, Source } from "@/lib/types";

type AppData = { books: Book[]; sources: Record<string, Source> };
const Ctx = createContext<AppData>({ books: [], sources: {} });

export function useAppData() {
  return useContext(Ctx);
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<AppData>({ books: [], sources: {} });

  useEffect(() => {
    Promise.all([loadBooks(), loadSources()])
      .then(([books, sources]) => setData({ books, sources: Object.fromEntries(sources.map((s) => [s.id, s])) }))
      .catch(() => {});
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, []);

  return <Ctx.Provider value={data}>{children}</Ctx.Provider>;
}
