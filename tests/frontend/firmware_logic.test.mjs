import test from "node:test";
import assert from "node:assert/strict";

import {
  confirmationText,
  firmwareView,
  formatBytes,
  shortSha,
} from "../../web/firmware_logic.mjs";

const BASE = {
  configured: true, armed: false, version: "round2-r6-2", size: 840800,
  sha256: "a".repeat(64), expires_at: null, served_at: null,
  device_version: "round2-r6-1",
};

test("unconfigured and unknown states disable arming", () => {
  assert.equal(firmwareView(null).state, "unknown");
  assert.equal(firmwareView({...BASE, configured: false}).state, "unconfigured");
  assert.equal(firmwareView({...BASE, configured: false}).canArm, false);
  assert.equal(firmwareView(null).canArm, false);
});

test("ready, armed, served and current states", () => {
  assert.equal(firmwareView(BASE).state, "ready");
  assert.equal(firmwareView(BASE).canArm, true);
  assert.equal(firmwareView({...BASE, armed: true}).state, "armed");
  assert.equal(firmwareView({...BASE, armed: true}).canDisarm, true);
  assert.equal(firmwareView({...BASE, served_at: "2026-11-07T10:00:00Z"}).state, "served");
  assert.equal(firmwareView({...BASE, device_version: "round2-r6-2"}).state, "current");
  assert.equal(firmwareView({...BASE, device_version: "round2-r6-2"}).canArm, false);
});

test("confirmation names the target and the reboot", () => {
  const text = confirmationText(BASE);
  assert.match(text, /round2-r6-2/);
  assert.match(text, /重启/);
});

test("size and sha formatting", () => {
  assert.equal(formatBytes(840800), "822 KiB");
  assert.equal(formatBytes(0), "--");
  assert.equal(shortSha("a".repeat(64)), "aaaaaaaaaaaa…");
  assert.equal(shortSha(""), "—");
});
