const CACHE_NAME = "movego-v1";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Let the network handle requests.
  // Avoid caching live rides, payments, authentication or GPS data.
});