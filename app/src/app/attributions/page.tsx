"use client";

import { useAppData } from "@/components/AppProviders";
import { TopBar } from "@/components/TopBar";

const GROUPS: Record<string, string> = {
  open: "Open sources (public domain, CC0 or CC BY)",
  "share-alike": "Share-alike sources (CC BY-SA)",
  licensed: "Licensed sources",
  isolated: "Separately licensed layers",
};

export default function Attributions() {
  const { sources } = useAppData();
  const list = Object.values(sources);
  return (
    <>
      <TopBar current={null} prev={null} next={null} />
      <main id="main" className="mx-auto max-w-[46rem] px-3 sm:px-6 py-10">
        <h1 className="font-serif text-[2.25rem] leading-tight">Sources and licenses</h1>
        <p className="mt-2 text-muted">
          Everything in this app comes from these sources or from you. Each card’s source chip names the exact record it came from.
        </p>
        {Object.entries(GROUPS).map(([g, label]) => {
          const items = list.filter((s) => s.license_group === g);
          if (!items.length) return null;
          return (
            <section key={g} className="mt-8">
              <h2 className="font-serif text-xl">{label}</h2>
              {items.map((s) => (
                <article key={s.id} className="card">
                  <h3 className="card-title">{s.name}</h3>
                  <p className="meta">{s.license}</p>
                  <p className="mt-1 text-[0.9375rem]">{s.attribution}</p>
                  {s.notes && <p className="meta mt-1">{s.notes}</p>}
                  <p className="meta mt-1 break-all">Version: <a className="underline" href={`${s.repo}/tree/${s.commit}`}>{s.commit.slice(0, 12)}</a></p>
                  <p className="mt-1"><a className="underline text-sm" href={s.homepage}>{s.homepage}</a></p>
                </article>
              ))}
            </section>
          );
        })}
        <section className="mt-8">
          <h2 className="font-serif text-xl">Map and fonts</h2>
          <article className="card">
            <h3 className="card-title">Base map</h3>
            <p className="text-[0.9375rem]">OpenFreeMap, with map data © OpenMapTiles and © OpenStreetMap contributors.</p>
          </article>
          <article className="card">
            <h3 className="card-title">Fonts</h3>
            <p className="text-[0.9375rem]">Literata, Public Sans and Noto Serif Hebrew, under the SIL Open Font License.</p>
          </article>
        </section>
      </main>
    </>
  );
}
