import { readFileSync } from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import { Reader } from "@/components/Reader";
import { chapterLabel } from "@/lib/refs";
import type { Book } from "@/lib/types";

// One static page per chapter (1,189), generated from the pipeline's book list.
export function generateStaticParams() {
  const books: Book[] = JSON.parse(readFileSync(path.join(process.cwd(), "public/data/books.json"), "utf-8"));
  return books.flatMap((b) => b.chapters.map((c) => ({ ch: `${b.osis}.${c}` })));
}

export const dynamicParams = false;

export async function generateMetadata({ params }: { params: Promise<{ ch: string }> }): Promise<Metadata> {
  const { ch } = await params;
  return { title: `${chapterLabel(ch)} | Scripture in Context` };
}

export default async function ReadPage({ params }: { params: Promise<{ ch: string }> }) {
  const { ch } = await params;
  return <Reader id={ch} />;
}
