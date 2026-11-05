"use client";

import "maplibre-gl/dist/maplibre-gl.css";
import maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";
import { splitPlaceName } from "@/lib/refs";
import type { Place } from "@/lib/types";

// Base map tiles: OpenFreeMap (no account needed). Credits show on the map.
const STYLE = "https://tiles.openfreemap.org/styles/positron";

function confClass(conf: number | null) {
  if (conf !== null && conf >= 500) return "high";
  if (conf !== null && conf >= 100) return "medium";
  return "low";
}

/** Plots each place's top-ranked identification. The full candidate list is in the card below. */
export default function MiniMap({ places }: { places: Place[] }) {
  const el = useRef<HTMLDivElement>(null);
  // Each place's top-ranked location, plus any other candidate at 10% confidence or more,
  // so contested places (e.g. Mount Sinai) show their main alternatives.
  const points = places.flatMap((p) => {
    const located = p.ids.filter((i) => i.lat !== null && i.lon !== null);
    return located.filter((i, k) => k === 0 || (i.conf ?? 0) >= 100).map((id) => ({ p, id }));
  });

  useEffect(() => {
    if (!el.current || points.length === 0) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const map = new maplibregl.Map({
      container: el.current,
      style: STYLE,
      center: [points[0].id.lon!, points[0].id.lat!],
      zoom: 6,
      cooperativeGestures: true,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    const bounds = new maplibregl.LngLatBounds();
    for (const { p, id } of points) {
      const dot = document.createElement("span");
      dot.className = `conf conf-${confClass(id.conf)}`;
      dot.style.background = confClass(id.conf) === "high" ? "var(--olive)" : "var(--page)";
      dot.setAttribute("role", "img");
      dot.setAttribute("aria-label", splitPlaceName(p.name).base);
      new maplibregl.Marker({ element: dot })
        .setLngLat([id.lon!, id.lat!])
        .setPopup(new maplibregl.Popup({ offset: 10, closeButton: false }).setText(
          `${splitPlaceName(p.name).base}: ${id.desc}${id.conf !== null ? ` (${Math.max(0, Math.round(id.conf / 10))}% confidence)` : ""}`))
        .addTo(map);
      bounds.extend([id.lon!, id.lat!]);
    }
    if (points.length > 1) map.fitBounds(bounds, { padding: 36, maxZoom: 9, duration: reduce ? 0 : 400 });
    return () => map.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [places]);

  if (points.length === 0) return <p className="empty">None of these places has a map point.</p>;
  return (
    <div ref={el} className="h-56 rounded-md overflow-hidden border border-stone-soft"
      role="region" aria-label={`Map of ${places.length} ${places.length === 1 ? "place" : "places"} in this passage`} />
  );
}
