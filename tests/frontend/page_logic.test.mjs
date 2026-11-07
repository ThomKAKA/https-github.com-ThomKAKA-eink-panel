import test from "node:test";
import assert from "node:assert/strict";

import {
  buildMemoDraft,
  memoSaveReport,
  normalizeDue,
  pageSwitchState,
} from "../../web/page_logic.mjs";


test("normalizeDue accepts browser datetime-local values and empty input", () => {
  assert.equal(normalizeDue("2026-11-08T18:30"), "2026-11-08 18:30");
  assert.equal(normalizeDue("2026-11-08 18:30"), "2026-11-08 18:30");
  assert.equal(normalizeDue(""), null);
  assert.equal(normalizeDue(null), null);
  assert.equal(normalizeDue("not-a-date"), null);
});


test("buildMemoDraft trims text, drops empty rows and reuses stable ids", () => {
  const draft = buildMemoDraft([
    {id: "a", text: "  买牛奶  ", due: "2026-11-08T18:00", face: "todo"},
    {id: "b", text: "   ", due: "", face: "done"},
    {id: "", text: "交报告", due: "", face: "doing"},
  ], {newId: (index) => `new-${index}`});

  assert.deepEqual(draft.items, [
    {id: "a", text: "买牛奶", due: "2026-11-08 18:00", face: "todo"},
    {id: "new-2", text: "交报告", due: null, face: "doing"},
  ]);
});


test("buildMemoDraft enforces the eight item and identifier contracts", () => {
  const rows = Array.from({length: 9}, (_, index) => ({
    id: `i${index}`, text: `事项${index}`, due: "", face: "todo",
  }));
  assert.throws(() => buildMemoDraft(rows), /8/);
  assert.throws(
    () => buildMemoDraft([{id: "a", text: "一"}, {id: "a", text: "二"}]),
    /重复/,
  );
  assert.throws(() => buildMemoDraft([{id: "坏 id", text: "x"}]), /标识/);
});


test("pageSwitchState distinguishes active, pending and expired frames", () => {
  const status = {page: "memo", frame_version: "f".repeat(64)};
  assert.equal(pageSwitchState(status, "memo"), "active");
  assert.equal(pageSwitchState(status, "course"), "pending");
  assert.equal(pageSwitchState({...status, frame_version: null}, "memo"), "expired");
  assert.equal(pageSwitchState(null, "memo"), "expired");
});


test("memoSaveReport is honest about polling and device acceptance", () => {
  const saved = {page: "memo", revision: 2};
  assert.equal(memoSaveReport(saved, null).tone, "idle");
  assert.match(
    memoSaveReport(saved, {page: "memo", frame_version: null, device: {}}).label,
    /60 s/,
  );
  assert.equal(
    memoSaveReport(saved, {page: "memo", frame_version: "f".repeat(64), device: {}}).tone,
    "warn",
  );
  assert.equal(
    memoSaveReport(saved, {
      page: "memo",
      frame_version: "f".repeat(64),
      device: {accepted_frame_version: "f".repeat(64)},
    }).tone,
    "ok",
  );
  assert.equal(
    memoSaveReport(saved, {page: "course", frame_version: null, device: {}}).tone,
    "warn",
  );
});
