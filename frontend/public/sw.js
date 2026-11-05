// A deliberately small service worker: it only gives a page visit a friendly "no internet" page.
// It never stores or replays the API, sign-in, bookings or photos (those requests are not touched at all),
// so nobody can be shown another person's data or stale prices.
const CACHE = 'tickbron-offline-v1'
const OFFLINE_URL = '/offline.html'

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll([OFFLINE_URL, '/brand/tickbron-mark.webp']))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(names => Promise.all(names.filter(name => name !== CACHE).map(name => caches.delete(name))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', event => {
  if (event.request.mode !== 'navigate') return
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE_URL)))
})
