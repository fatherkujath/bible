"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { chapterHref } from "@/lib/refs";
import { useAppData } from "./AppProviders";

/** Two-step picker: book, then chapter. Used in the top bar dialog and on the home page. */
export function BookPicker({ current, onPick }: { current: string | null; onPick?: () => void }) {
  const { books } = useAppData();
  const currentBook = current?.split(".")[0] ?? null;
  const [book, setBook] = useState<string | null>(currentBook);
  useEffect(() => setBook(currentBook), [currentBook]);

  const chosen = books.find((b) => b.osis === book);

  return (
    <div className="p-4 sm:p-6">
      {chosen ? (
        <>
          <div className="flex items-baseline gap-3 mb-4">
            <button type="button" className="text-sm underline text-muted" onClick={() => setBook(null)}>All books</button>
            <h2 className="font-serif text-xl">{chosen.name}</h2>
          </div>
          <ul className="grid grid-cols-[repeat(auto-fill,minmax(3rem,1fr))] gap-2" aria-label={`${chosen.name} chapters`}>
            {chosen.chapters.map((c) => {
              const id = `${chosen.osis}.${c}`;
              return (
                <li key={c}>
                  <Link href={chapterHref(id)} onClick={onPick}
                    aria-current={id === current ? "page" : undefined}
                    className={`flex items-center justify-center h-11 rounded-md border text-sm ${id === current ? "border-olive bg-olive-soft" : "border-stone hover:border-olive"}`}>
                    {c}
                  </Link>
                </li>
              );
            })}
          </ul>
        </>
      ) : (
        <div className="grid sm:grid-cols-2 gap-6">
          {(["OT", "NT"] as const).map((t) => (
            <section key={t}>
              <h2 className="font-serif text-lg mb-2">{t === "OT" ? "Old Testament" : "New Testament"}</h2>
              <ul className="grid grid-cols-2 gap-x-3">
                {books.filter((b) => b.testament === t).map((b) => (
                  <li key={b.osis}>
                    <button type="button" onClick={() => setBook(b.osis)}
                      className={`w-full text-left py-1.5 text-[0.9375rem] hover:text-olive ${b.osis === currentBook ? "text-olive" : ""}`}>
                      {b.name}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
