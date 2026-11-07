import test from "node:test";
import assert from "node:assert/strict";

import {
  canRegisterServiceWorker,
  installationHint,
  shouldOfferInstall,
} from "../../web/pwa_logic.mjs";


test("service worker registration requires a secure context and browser support", () => {
  assert.equal(
    canRegisterServiceWorker({hasServiceWorker: true, secureContext: true}),
    true,
  );
  assert.equal(
    canRegisterServiceWorker({hasServiceWorker: true, secureContext: false}),
    false,
  );
  assert.equal(
    canRegisterServiceWorker({hasServiceWorker: false, secureContext: true}),
    false,
  );
});


test("install prompt is offered only on an installable secure connection", () => {
  assert.equal(
    shouldOfferInstall({standalone: false, hasServiceWorker: true, secureContext: true}),
    true,
  );
  assert.equal(
    shouldOfferInstall({standalone: true, hasServiceWorker: true, secureContext: true}),
    false,
  );
  assert.equal(
    shouldOfferInstall({standalone: false, hasServiceWorker: true, secureContext: false}),
    false,
  );
  assert.equal(
    shouldOfferInstall({standalone: false, hasServiceWorker: false, secureContext: true}),
    false,
  );
});


test("installation hint is honest on LAN HTTP and in standalone mode", () => {
  assert.equal(
    installationHint({standalone: true, hasServiceWorker: true, secureContext: true}),
    null,
  );
  assert.equal(
    installationHint({standalone: false, hasServiceWorker: true, secureContext: false}),
    "当前 HTTP 连接不支持安装或离线；可先收藏本页。",
  );
  assert.equal(
    installationHint({standalone: false, hasServiceWorker: false, secureContext: true}),
    "当前浏览器不支持安装；可先收藏本页。",
  );
  assert.equal(
    installationHint({standalone: false, hasServiceWorker: true, secureContext: true}),
    "浏览器菜单 → 安装应用 / 添加到主屏幕。",
  );
});
