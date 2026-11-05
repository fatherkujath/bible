"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { chapterHref, chapterLabel } from "@/lib/refs";
import { BookPicker } from "./BookPicker";

export function TopBar({ current, prev, next }: { current: string | null; prev: string | null; next: string | null }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");

  useEffect(() => {
    const t = document.documentElement.dataset.theme;
    setTheme(t === "light" || t === "dark" ? t : "system");
  }, []);

  const cycleTheme = () => {
    const nextTheme = theme === "system" ? "dark" : theme === "dark" ? "light" : "system";
    setTheme(nextTheme);
    try {
      if (nextTheme === "system") { delete document.documentElement.dataset.theme; localStorage.removeItem("sic-theme"); }
      else { document.documentElement.dataset.theme = nextTheme; localStorage.setItem("sic-theme", nextTheme); }
    } catch {}
  };

  return (
    <header className="sticky top-0 z-20 bg-vellum/95 backdrop-blur border-b border-stone-soft">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2">Skip to the text</a>
      <div className="mx-auto max-w-[78rem] px-3 sm:px-6 h-14 flex items-center gap-2">
        <Link href="/" className="font-serif text-[1.0625rem] mr-auto whitespace-nowrap" aria-label="Scripture in Context, home">
          <span className="hidden sm:inline">Scripture in Context</span><span className="sm:hidden">In Context</span>
        </Link>
        {prev && (
          <Link href={chapterHref(prev)} className="px-2 py-2 text-muted hover:text-ink" aria-label={`Previous: ${chapterLabel(prev)}`}>
            <Arrow dir="left" />
          </Link>
        )}
        <button type="button" onClick={() => dialog.current?.showModal()}
          className="px-3 py-1.5 rounded-md border border-stone text-sm hover:border-olive min-h-[44px] whitespace-nowrap">
          {current ? chapterLabel(current) : "Choose a chapter"}
        </button>
        {next && (
          <Link href={chapterHref(next)} className="px-2 py-2 text-muted hover:text-ink" aria-label={`Next: ${chapterLabel(next)}`}>
            <Arrow dir="right" />
          </Link>
        )}
        <button type="button" onClick={cycleTheme} className="ml-1 px-2 py-2 text-sm text-muted hover:text-ink min-h-[44px]"
          title="Change color theme">
          {theme === "system" ? "Auto" : theme === "dark" ? "Dark" : "Light"}<span className="sr-only"> theme. Change color theme</span>
        </button>
      </div>
      <dialog ref={dialog} className="m-auto w-[min(44rem,94vw)] max-h-[85vh] rounded-lg border border-stone bg-page text-ink p-0 backdrop:bg-black/40"
        onClick={(e) => { if (e.target === dialog.current) dialog.current?.close(); }}>
        <BookPicker current={current} onPick={() => dialog.current?.close()} />
      </dialog>
    </header>
  );
}

function Arrow({ dir }: { dir: "left" | "right" }) {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      {dir === "left" ? <path d="M12.5 4 6.5 10l6 6" /> : <path d="M7.5 4l6 6-6 6" />}
    </svg>
  );
}
