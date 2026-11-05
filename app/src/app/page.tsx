"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BookPicker } from "@/components/BookPicker";
import { TopBar } from "@/components/TopBar";
import { chapterHref, chapterLabel } from "@/lib/refs";

export default function Home() {
  const [last, setLast] = useState<string | null>(null);
  useEffect(() => {
    try { setLast(localStorage.getItem("sic-last-read")); } catch {}
  }, []);

  return (
    <>
      <TopBar current={null} prev={null} next={null} />
      <main id="main" className="mx-auto max-w-[52rem] px-3 sm:px-6 py-10">
        <h1 className="font-serif text-[2.25rem] leading-tight">Open a chapter</h1>
        <p className="mt-2 text-muted max-w-[34rem]">
          Each chapter opens with its places, people, original words and cross-references alongside, all from cited sources.
        </p>
        {last && (
          <p className="mt-6">
            <Link href={chapterHref(last)} className="inline-block px-4 py-2.5 rounded-md bg-olive text-page font-bold">
              Continue reading {chapterLabel(last)}
            </Link>
          </p>
        )}
        <div className="mt-8 bg-page rounded-lg border border-stone-soft">
          <BookPicker current={null} />
        </div>
        <p className="mt-8 text-sm text-muted">
          <Link href="/attributions/" className="underline">Sources and licenses</Link>
        </p>
      </main>
    </>
  );
}
