/* MoveGo app image cache: public bundled artwork only; never cache authenticated APIs. */
const IMAGE_CACHE = 'movego-images-3b0fc2dee2ef3968';
const IMAGE_PREFIX = 'movego-images-';
const PRELOAD_IMAGES = ["/app/assets/icons/icon-192.png","/app/assets/icons/icon-512.png","/app/assets/icons/icon-maskable-512.png","/app/assets/icons/ride-categories/comfort.webp","/app/assets/icons/ride-categories/couriers.webp","/app/assets/icons/ride-categories/inhurry.webp","/app/assets/icons/ride-categories/keke.webp","/app/assets/icons/ride-categories/ride.webp","/app/assets/images/onboarding-ride.jpg","/app/assets/images/onboarding-safety.jpg","/app/assets/images/onboarding-services.jpg","/app/assets/images/otp-whatsapp-art.jpg","/app/assets/images/profile-welcome-art.jpg","/app/assets/images/role-driver.jpg","/app/assets/images/role-passenger.jpg","/app/assets/maps/demo-city.svg","/app/assets/movego-original-logo.png"];
const ALLOWED_EXT = /\.(?:png|jpe?g|webp|gif|svg|avif|ico)$/i;
function publicImage(url) {
  const u = new URL(url);
  return u.origin === self.location.origin &&
    u.pathname.startsWith('/app/') &&
    ALLOWED_EXT.test(u.pathname) &&
    !u.pathname.includes('/private/') &&
    !u.pathname.includes('/avatar');
}
function normalizedKey(input) {
  const url = new URL(input, self.location.origin);
  url.search = '';
  url.hash = '';
  return url.toString();
}
async function fetchAndCache(cache, url) {
  try {
    const response = await fetch(url, { credentials: 'same-origin', cache: 'no-cache' });
    if (response.ok && response.type === 'basic') await cache.put(normalizedKey(url), response.clone());
    return response.ok;
  } catch (_) { return false; }
}
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(IMAGE_CACHE);
    // Four concurrent downloads keeps the first visit usable on slow connections.
    let i=0;
    const runner=async()=>{
      while (i < PRELOAD_IMAGES.length) {
        const url=PRELOAD_IMAGES[i++];
        await fetchAndCache(cache, url);
      }
    };
    await Promise.all([runner(),runner(),runner(),runner()]);
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', event => {
  event.waitUntil((async()=>{
    const keys = await caches.keys();
    await Promise.all(keys.filter(k=>k.startsWith(IMAGE_PREFIX)&&k!==IMAGE_CACHE).map(k=>caches.delete(k)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || !publicImage(event.request.url)) return;
  event.respondWith((async()=>{
    const key = normalizedKey(event.request.url);
    const cache = await caches.open(IMAGE_CACHE);
    const stored=await cache.match(key);
    if (stored) return stored;
    try {
      const response=await fetch(event.request);
      if (response.ok && response.type==='basic') {
        await cache.put(key,response.clone());
      }
      return response;
    } catch (err) {
      return Response.error();
    }
  })());
});
