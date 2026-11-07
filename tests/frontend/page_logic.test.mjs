import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCourseDraft,
  buildMemoDraft,
  courseSaveReport,
  memoSaveReport,
  normalizeDue,
  pageSwitchState,
  parseWeeks,
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


test("parseWeeks expands ranges and rejects ambiguous input", () => {
  assert.deepEqual(parseWeeks("1-3,5", 8), [1, 2, 3, 5]);
  assert.deepEqual(parseWeeks(" 8 ", 8), [8]);
  for (const value of ["", "0", "9", "3-1", "1,,2", "1-3,2", "abc"]) {
    assert.throws(() => parseWeeks(value, 8), /周/);
  }
});


function courseValues(overrides = {}) {
  return {
    semester_start: "2026-09-07",
    total_weeks: 18,
    courses: [
      {id: "a", name: "高等数学", weekday: 7, weeks: "1-8,9,10-18",
       start: "08:00", end: "09:40", room: "A-101"},
      {id: "", name: "大学英语", weekday: 7, weeks: "9",
       start: "10:00", end: "11:40", room: "B-202"},
    ],
    overrides: [],
    ...overrides,
  };
}


test("buildCourseDraft normalizes weeks and generated course ids", () => {
  const draft = buildCourseDraft(courseValues(), {newId: (index) => `new-${index}`});

  assert.equal(draft.semester_start, "2026-09-07");
  assert.equal(draft.total_weeks, 18);
  assert.deepEqual(draft.courses.map((course) => course.id), ["a", "new-1"]);
  assert.deepEqual(draft.courses[0].weeks, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]);
  assert.equal(draft.courses[1].name, "大学英语");
});


test("buildCourseDraft keeps action-specific overrides only", () => {
  const draft = buildCourseDraft(courseValues({
    overrides: [
      {date: "2026-11-08", course_id: "a", action: "cancel", room: "", start: "", end: ""},
      {date: "2026-11-09", course_id: "a", action: "move_room", room: "C-303", start: "", end: ""},
      {date: "2026-11-10", course_id: "a", action: "move_time", room: "", start: "13:00", end: "14:40"},
    ],
  }));

  assert.deepEqual(draft.overrides, [
    {date: "2026-11-08", course_id: "a", action: "cancel"},
    {date: "2026-11-09", course_id: "a", action: "move_room", room: "C-303"},
    {date: "2026-11-10", course_id: "a", action: "move_time", start: "13:00", end: "14:40"},
  ]);
});


test("buildCourseDraft rejects unsafe or ambiguous schedules", () => {
  const rows = Array.from({length: 13}, (_, index) => ({
    id: `c${index}`, name: "课", weekday: 1, weeks: "1",
    start: "08:00", end: "09:00", room: "A-1",
  }));
  assert.throws(() => buildCourseDraft(courseValues({courses: rows})), /12/);
  assert.throws(
    () => buildCourseDraft(courseValues({courses: [
      {id: "a", name: "课", weekday: 1, weeks: "1", start: "08:00", end: "09:00", room: "A-1"},
      {id: "a", name: "课", weekday: 2, weeks: "1", start: "08:00", end: "09:00", room: "A-1"},
    ]})),
    /重复/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({courses: [
      {id: "a", name: "课", weekday: 1, weeks: "19", start: "08:00", end: "09:00", room: "A-1"},
    ]})),
    /周/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({courses: [
      {id: "a", name: "课", weekday: 1, weeks: "1", start: "10:00", end: "09:00", room: "A-1"},
    ]})),
    /时间/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({overrides: [
      {date: "2026-11-08", course_id: "missing", action: "cancel"},
    ]})),
    /课程/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({overrides: [
      {date: "2026-11-08", course_id: "a", action: "cancel"},
      {date: "2026-11-08", course_id: "a", action: "cancel"},
    ]})),
    /重复/,
  );
  assert.throws(() => buildCourseDraft(courseValues({semester_start: "2026-02-30"})), /日期/);
});


test("courseSaveReport mirrors the honest memo polling report", () => {
  const saved = {page: "course", revision: 3};
  assert.equal(courseSaveReport(saved, null).tone, "idle");
  assert.match(
    courseSaveReport(saved, {page: "course", frame_version: null, device: {}}).label,
    /60 s/,
  );
  assert.equal(
    courseSaveReport(saved, {
      page: "course",
      frame_version: "f".repeat(64),
      device: {accepted_frame_version: "f".repeat(64)},
    }).tone,
    "ok",
  );
  assert.equal(
    courseSaveReport(saved, {page: "memo", frame_version: null, device: {}}).tone,
    "warn",
  );
});
