// Scripture in Context service worker.
// Pages and data you open are cached, so they keep working offline.
const VERSION = "sic-v2";
const CORE = ["/", "/manifest.webmanifest", "/icons/icon.svg", "/data/books.json", "/data/attributions.json"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;

  // Build assets and fonts never change once published: cache first.
  if (url.pathname.startsWith("/_next/static/")) {
    e.respondWith(cacheFirst(e.request));
    return;
  }
  // Pages and data: network first, cached copy when offline.
  e.respondWith(networkFirst(e.request));
});

async function cacheFirst(req) {
  const hit = await caches.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok) (await caches.open(VERSION)).put(req, res.clone());
  return res;
}

async function networkFirst(req) {
  try {
    const res = await fetch(req);
    if (res.ok) (await caches.open(VERSION)).put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await caches.match(req, { ignoreSearch: true });
    if (hit) return hit;
    if (req.mode === "navigate") {
      const home = await caches.match("/");
      if (home) return home;
    }
    throw err;
  }
}
