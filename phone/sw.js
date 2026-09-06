/*
sw.js - service worker: makes the phone app work with no internet connection.

On install it stores the app shell (html, css, js, catalog, placeholder) in the
browser cache. Afterwards every request is answered from the cache first, and
anything fetched from the network (exercise pictures, the demo file) is added
to the cache on the way through, so pictures you have seen once stay available
offline. Bump CACHE_NAME whenever the app files change.
*/
const CACHE_NAME = "sbs-trainer-v25";
// Only the app's own files are stored up front. The exercise catalog, the
// pictures and the demo file are stored the first time the app asks for them,
// which happens right after a program is created or imported.
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./defaults.js",
  "./program_logic.js",
  "./exercise_library.js",
  "./app.js",
  "./manifest.webmanifest",
  "./icons/icon-180.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) { return cache.addAll(APP_SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (names) {
      return Promise.all(names.filter(function (name) { return name !== CACHE_NAME; })
        .map(function (name) { return caches.delete(name); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (event) {
  const request = event.request;
  if (request.method !== "GET") return;
  event.respondWith(
    // ignoreSearch: a request for app.js?v=2 is answered by the cached app.js.
    caches.match(request, { ignoreSearch: true }).then(function (cached) {
      if (cached) return cached;
      return fetch(request).then(function (response) {
        if (response && response.ok && new URL(request.url).origin === self.location.origin) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) { cache.put(request, copy); });
        }
        return response;
      }).catch(function () {
        if (request.mode === "navigate") return caches.match("./index.html");
        return new Response("", { status: 503, statusText: "offline" });
      });
    })
  );
});
