/* Service worker — Phase 7 offline architecture (design §09):
   - precache app shell + offline fallback
   - network-first with cache fallback for same-origin GETs (rosters, schemes,
     sheets stay available offline)
   - never caches mutations — those go through the IndexedDB outbox +
     POST /api/v1/sync/mutations with replay-safe semantics. */
const SHELL_CACHE = "sms-shell-v2";
const API_CACHE = "sms-api-v2";
const OFFLINE_URL = "/offline";
const SHELL_ASSETS = ["/", "/login", "/marks", "/attendance", "/offline"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_ASSETS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => ![SHELL_CACHE, API_CACHE].includes(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return; // mutations: outbox → sync endpoint
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/")) {
    // network-first API reads; fall back to last-known response offline
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(API_CACHE).then((c) => c.put(req, copy)).catch(() => {});
          }
          return res;
        })
        .catch(async () => {
          const cached = await caches.match(req);
          return cached || new Response(
            JSON.stringify({ error: { code: "OFFLINE", message: "No cached data available." } }),
            { status: 503, headers: { "Content-Type": "application/json" } });
        })
    );
    return;
  }

  // page navigations: network-first with shell fallback
  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok && req.mode === "navigate") {
          const copy = res.clone();
          caches.open(SHELL_CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(async () => {
        const cached = await caches.match(req);
        if (cached) return cached;
        const fallback = await caches.match(OFFLINE_URL);
        return fallback || new Response("Offline", { status: 503 });
      })
  );
});
