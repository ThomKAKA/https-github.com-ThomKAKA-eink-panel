import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const sw = require("../../web/sw.js");

const ORIGIN = "http://127.0.0.1:8000";
const WEB_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../../web");


// Relative specifiers only: the shell is plain ES modules served from /static.
function relativeImports(file) {
  const source = readFileSync(file, "utf8");
  const pattern = /^\s*import[\s\S]*?from\s*["'](\.[^"']+)["']/gm;
  return [...source.matchAll(pattern)].map((match) => match[1]);
}


function shellModuleClosure(entry = "manage.js") {
  const seen = new Set();
  const pending = [resolve(WEB_DIR, entry)];
  while (pending.length > 0) {
    const file = pending.pop();
    if (seen.has(file)) {
      continue;
    }
    seen.add(file);
    for (const specifier of relativeImports(file)) {
      pending.push(resolve(dirname(file), specifier));
    }
  }
  return seen;
}


test("service worker caches only same-origin GET shell requests", () => {
  assert.equal(sw.isCacheable(`${ORIGIN}/manage`, "GET", ORIGIN), true);
  assert.equal(sw.isCacheable(`${ORIGIN}/static/manage.js`, "GET", ORIGIN), true);
  assert.equal(sw.isCacheable(`${ORIGIN}/static/icons/icon-192.png`, "GET", ORIGIN), true);
});


test("service worker never caches API, registration, or non-GET requests", () => {
  assert.equal(sw.isCacheable(`${ORIGIN}/api/panels/progress/status`, "GET", ORIGIN), false);
  assert.equal(sw.isCacheable(`${ORIGIN}/api/events`, "POST", ORIGIN), false);
  assert.equal(sw.isCacheable(`${ORIGIN}/sw.js`, "GET", ORIGIN), false);
  assert.equal(sw.isCacheable(`${ORIGIN}/manifest.webmanifest`, "GET", ORIGIN), false);
  assert.equal(sw.isCacheable(`${ORIGIN}/`, "GET", ORIGIN), false);
  assert.equal(sw.isCacheable("https://example.com/manage", "GET", ORIGIN), false);
});


test("service worker shell includes the management page and offline fallback", () => {
  assert.ok(sw.SHELL_ASSETS.includes("/manage"));
  assert.ok(sw.SHELL_ASSETS.includes("/static/offline.html"));
  assert.ok(sw.SHELL_ASSETS.includes("/static/manage.js"));
  assert.ok(sw.SHELL_ASSETS.includes("/static/pwa_logic.mjs"));
  assert.ok(sw.SHELL_ASSETS.every((asset) => !asset.startsWith("/api/")));
});


test("every module the management shell imports is precached", () => {
  const modules = shellModuleClosure("manage.js");

  assert.ok(modules.size >= 4, "import walk should reach manage.js and its modules");
  for (const file of modules) {
    const asset = `/static/${basename(file)}`;
    assert.ok(
      sw.SHELL_ASSETS.includes(asset),
      `${asset} is imported by the shell but missing from SHELL_ASSETS`,
    );
  }
  assert.ok(
    modules.has(resolve(WEB_DIR, "firmware_logic.mjs")),
    "the walk must cover the firmware module imported by manage.js",
  );
});


test("cache version was bumped for the current shell asset set", () => {
  assert.equal(sw.CACHE_NAME, "eink-shell-v3");
});


test("cache writes use canonical URL keys without query strings", async () => {
  const puts = [];
  const request = {url: `${ORIGIN}/manage?mobile-check=1`, method: "GET", mode: "navigate"};
  const cacheStorage = {
    open: async () => ({
      put: async (key, value) => puts.push({key, value}),
    }),
  };

  const result = await sw.cacheResponse(
    request,
    new Response("fresh", {status: 200}),
    cacheStorage,
    ORIGIN,
  );

  assert.equal(puts.length, 1);
  assert.equal(puts[0].key, `${ORIGIN}/manage`);
  assert.equal(await result.text(), "fresh");
});


test("a cache write failure still returns the live network response", async () => {
  const request = {url: `${ORIGIN}/manage`, method: "GET", mode: "navigate"};
  const fresh = new Response("fresh", {status: 200});
  const cacheStorage = {
    open: async () => ({
      put: async () => {
        throw new Error("quota");
      },
    }),
    match: async () => new Response("stale", {status: 200}),
  };

  const result = await sw.networkFirst(request, {
    fetchImpl: async () => fresh,
    cacheStorage,
  });

  assert.equal(await result.text(), "fresh");
});


test("offline navigation falls back to the cached management shell", async () => {
  const request = {url: `${ORIGIN}/other`, method: "GET", mode: "navigate"};
  const shell = new Response("shell", {status: 200});
  const cacheStorage = {
    match: async (key) => (key === "/manage" ? shell : undefined),
  };

  const result = await sw.networkFirst(request, {
    fetchImpl: async () => {
      throw new Error("offline");
    },
    cacheStorage,
  });

  assert.equal(await result.text(), "shell");
});


test("offline shell assets are served from the cache", async () => {
  const request = {url: `${ORIGIN}/static/manage.js`, method: "GET", mode: "no-cors"};
  const script = new Response("cached-script", {status: 200});
  const cacheStorage = {
    match: async (key) => (key === request ? script : undefined),
  };

  const result = await sw.networkFirst(request, {
    fetchImpl: async () => {
      throw new Error("offline");
    },
    cacheStorage,
  });

  assert.equal(await result.text(), "cached-script");
});


test("offline assets without a cache entry return a network error", async () => {
  const request = {url: `${ORIGIN}/static/manage.js`, method: "GET", mode: "no-cors"};
  const result = await sw.networkFirst(request, {
    fetchImpl: async () => {
      throw new Error("offline");
    },
    cacheStorage: {match: async () => undefined},
  });

  assert.equal(result.type, "error");
});
