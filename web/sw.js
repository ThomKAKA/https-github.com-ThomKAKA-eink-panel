const CACHE_NAME = "eink-shell-v5"; // Bump when shell assets or keys change.
const OFFLINE_URL = "/static/offline.html";
const SHELL_ASSETS = [
  "/manage",
  OFFLINE_URL,
  "/static/style.css",
  "/static/manage.css",
  "/static/manage.js",
  "/static/manage_logic.mjs",
  "/static/pwa_logic.mjs",
  "/static/firmware_logic.mjs",
  "/static/page_editor.js",
  "/static/page_logic.mjs",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];
const SHELL_PATHS = new Set(["/manage", OFFLINE_URL]);

// Cache only the static management shell. API responses and status are never
// stored: offline must show UNKNOWN rather than a stale device observation.
function isCacheable(requestUrl, method = "GET", origin = globalThis.location?.origin) {
  if (method !== "GET" || !origin) {
    return false;
  }
  let url;
  try {
    url = new URL(requestUrl, origin);
  } catch {
    return false;
  }
  if (url.origin !== origin) {
    return false;
  }
  return SHELL_PATHS.has(url.pathname) || url.pathname.startsWith("/static/");
}

function cacheKey(requestUrl, origin = globalThis.location?.origin) {
  const url = new URL(requestUrl, origin);
  return `${url.origin}${url.pathname}`;
}

async function cacheResponse(
  request,
  response,
  cacheStorage = caches,
  origin = globalThis.location?.origin,
) {
  if (!response || !response.ok || !isCacheable(request.url, request.method, origin)) {
    return response;
  }
  try {
    const cache = await cacheStorage.open(CACHE_NAME);
    // Canonical URL keys avoid duplicate navigation entries with query strings.
    await cache.put(cacheKey(request.url, origin), response.clone());
  } catch {
    // Best effort: a full or denied cache must not replace the live response.
  }
  return response;
}

async function offlineFallback(request, cacheStorage = caches) {
  try {
    const cached = await cacheStorage.match(request);
    if (cached) {
      return cached;
    }
    if (request.mode === "navigate") {
      return (
        (await cacheStorage.match("/manage")) ||
        (await cacheStorage.match(OFFLINE_URL)) ||
        Response.error()
      );
    }
    return Response.error();
  } catch {
    return Response.error();
  }
}

async function networkFirst(request, options = {}) {
  const fetchImpl = options.fetchImpl || fetch;
  const cacheStorage = options.cacheStorage || caches;
  let response;
  try {
    response = await fetchImpl(request, {cache: "no-cache"});
  } catch {
    return offlineFallback(request, cacheStorage);
  }
  return cacheResponse(request, response, cacheStorage);
}

function registerListeners() {
  self.addEventListener("install", (event) => {
    event.waitUntil(
      caches
        .open(CACHE_NAME)
        .then((cache) =>
          cache.addAll(
            SHELL_ASSETS.map((url) => new Request(url, {cache: "reload"})),
          ),
        )
        .then(() => self.skipWaiting()),
    );
  });

  self.addEventListener("activate", (event) => {
    event.waitUntil(
      caches
        .keys()
        .then((keys) =>
          Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
        )
        .then(() => self.clients.claim()),
    );
  });

  self.addEventListener("fetch", (event) => {
    const request = event.request;
    let sameOrigin = false;
    try {
      sameOrigin = new URL(request.url).origin === self.location.origin;
    } catch {
      sameOrigin = false;
    }
    if (request.mode === "navigate" && sameOrigin) {
      event.respondWith(networkFirst(request));
      return;
    }
    if (isCacheable(request.url, request.method)) {
      event.respondWith(networkFirst(request));
    }
  });
}

if (typeof self !== "undefined" && typeof self.addEventListener === "function") {
  registerListeners();
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    CACHE_NAME,
    OFFLINE_URL,
    SHELL_ASSETS,
    cacheKey,
    cacheResponse,
    isCacheable,
    networkFirst,
    offlineFallback,
  };
}
