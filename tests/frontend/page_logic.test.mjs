import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCourseDraft,
  buildMemoDraft,
  buildTakeoutDraft,
  calendarPreviewMatch,
  codexPreviewMatch,
  codexSummary,
  courseSaveReport,
  formatTokens,
  memoSaveReport,
  normalizeDue,
  pageSwitchState,
  parseWeeks,
  resolveOverrideCourse,
  takeoutSaveReport,
  weatherSummary,
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
      {id: "a", name: "高等数学", weekday: 7, weeks: "1-8,9,10-18", period: 1, room: "A-101"},
      {id: "", name: "大学英语", weekday: 7, weeks: "9", period: 2, room: "B-202"},
    ],
    overrides: [],
    ...overrides,
  };
}


test("buildCourseDraft normalizes weeks, periods and generated course ids", () => {
  const draft = buildCourseDraft(courseValues(), {newId: (index) => `new-${index}`});

  assert.equal(draft.semester_start, "2026-09-07");
  assert.equal(draft.total_weeks, 18);
  assert.deepEqual(draft.courses.map((course) => course.id), ["a", "new-1"]);
  assert.deepEqual(draft.courses[0].weeks, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]);
  assert.equal(draft.courses[0].period, 1);
  assert.equal(draft.courses[1].name, "大学英语");
  assert.equal(draft.courses[1].period, 2);
});


test("buildCourseDraft keeps action-specific overrides only", () => {
  const draft = buildCourseDraft(courseValues({
    overrides: [
      {date: "2026-11-08", course_id: "a", action: "cancel", room: "", period: 1, name: ""},
      {date: "2026-11-09", course_id: "a", action: "move_room", room: "C-303", period: 1, name: ""},
      {date: "2026-11-10", course_id: "a", action: "move_period", room: "", period: 4, name: ""},
      {date: "2026-11-11", course_id: "extra-1", action: "add", room: "报告厅", period: 3, name: "临时讲座"},
    ],
  }));

  assert.deepEqual(draft.overrides, [
    {date: "2026-11-08", course_id: "a", action: "cancel"},
    {date: "2026-11-09", course_id: "a", action: "move_room", room: "C-303"},
    {date: "2026-11-10", course_id: "a", action: "move_period", period: 4},
    {date: "2026-11-11", course_id: "extra-1", action: "add", name: "临时讲座", period: 3, room: "报告厅"},
  ]);
});


test("buildCourseDraft rejects unsafe or ambiguous schedules", () => {
  const rows = Array.from({length: 13}, (_, index) => ({
    id: `c${index}`, name: "课", weekday: 1, weeks: "1", period: 1, room: "A-1",
  }));
  assert.throws(() => buildCourseDraft(courseValues({courses: rows})), /12/);
  assert.throws(
    () => buildCourseDraft(courseValues({courses: [
      {id: "a", name: "课", weekday: 1, weeks: "1", period: 1, room: "A-1"},
      {id: "a", name: "课", weekday: 2, weeks: "1", period: 1, room: "A-1"},
    ]})),
    /重复/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({courses: [
      {id: "a", name: "课", weekday: 1, weeks: "19", period: 1, room: "A-1"},
    ]})),
    /周/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({courses: [
      {id: "a", name: "课", weekday: 1, weeks: "1", period: 6, room: "A-1"},
    ]})),
    /节次/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({courses: [
      {id: "a", name: "课", weekday: 1, weeks: "1", period: 1, room: "A-1"},
      {id: "b", name: "课", weekday: 1, weeks: "1", period: 1, room: "B-1"},
    ]})),
    /时段/,
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
  assert.throws(
    () => buildCourseDraft(courseValues({overrides: [
      {date: "2026-11-08", course_id: "extra-1", action: "add", name: "", period: 3, room: "报告厅"},
    ]})),
    /课程名/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({overrides: [
      {date: "2026-11-08", course_id: "a", action: "add", name: "讲座", period: 3, room: "报告厅"},
    ]})),
    /临时课程标识/,
  );
  assert.throws(
    () => buildCourseDraft(courseValues({overrides: [
      {date: "2026-11-08", course_id: "e1", action: "add", name: "一", period: 3, room: "报告厅"},
      {date: "2026-11-08", course_id: "e2", action: "add", name: "二", period: 4, room: "报告厅"},
    ]})),
    /临时加一节课/,
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


test("resolveOverrideCourse preserves loaded ids and clears deleted courses", () => {
  const courses = [{id: "a", name: "高数"}, {id: "b", name: "英语"}];

  assert.equal(resolveOverrideCourse({course_id: "a"}, courses), "a");
  assert.equal(resolveOverrideCourse({course_id: "gone"}, courses), "");
  assert.equal(resolveOverrideCourse({}, courses), "");
  assert.equal(resolveOverrideCourse({course_id: "a"}, []), "");
  assert.equal(resolveOverrideCourse({action: "add", course_id: "extra-1"}, courses), "");
});


test("weatherSummary distinguishes waiting, stale and ready documents", () => {
  assert.equal(
    weatherSummary({data: {hourly: [], stale: true}}).state,
    "waiting",
  );
  assert.equal(
    weatherSummary({data: {current_temp: null, hourly: [{}], stale: false}}).state,
    "waiting",
  );

  const stale = weatherSummary({
    revision: 2,
    updated_at: "2026-11-08 14:20",
    data: {current_temp: 15, hourly: [{hour: 14}], stale: true},
  });
  assert.equal(stale.state, "stale");
  assert.match(stale.label, /2026-11-08 14:20/);
  assert.equal(stale.canRefresh, true);

  const ready = weatherSummary({
    revision: 3,
    updated_at: "2026-11-08 15:20",
    data: {current_temp: 16, hourly: [{hour: 15}], stale: false},
  });
  assert.equal(ready.state, "ready");
  assert.match(ready.label, /2026-11-08 15:20/);
});


test("formatTokens mirrors the panel labels", () => {
  assert.equal(formatTokens(0), "0");
  assert.equal(formatTokens(999), "999");
  assert.equal(formatTokens(1000), "1.0k");
  assert.equal(formatTokens(352081), "352.1k");
  assert.equal(formatTokens(22646123), "22.6M");
  assert.equal(formatTokens(132173864), "132.2M");
  assert.equal(formatTokens(1387112797), "1.39B");
});


test("codexSummary distinguishes waiting, ready and stale documents", () => {
  assert.equal(codexSummary({data: {}}).state, "waiting");
  assert.equal(codexSummary({data: {today_tokens: null}}).state, "waiting");

  const ready = codexSummary({
    revision: 3,
    updated_at: "2026-11-08 15:20",
    data: {today_tokens: 0, week_tokens: 22646123, total_tokens: 132173864, stale: false},
  });
  assert.equal(ready.state, "ready");
  assert.match(ready.label, /2026-11-08 15:20/);
  assert.match(ready.label, /今日 0/);
  assert.match(ready.label, /22\.6M/);
  assert.match(ready.label, /132\.2M/);

  const stale = codexSummary({
    updated_at: "2026-11-08 14:00",
    data: {today_tokens: 0, week_tokens: 1, total_tokens: 2, stale: true},
  });
  assert.equal(stale.state, "stale");
  assert.match(stale.label, /^STALE/);
});


test("codexPreviewMatch only matches the served codex frame", () => {
  const version = "f".repeat(64);
  assert.equal(codexPreviewMatch({page: "codex", frame_version: version}, version), true);
  assert.equal(codexPreviewMatch({page: "codex", frame_version: "e".repeat(64)}, version), false);
  assert.equal(codexPreviewMatch({page: "calendar", frame_version: version}, version), false);
  assert.equal(codexPreviewMatch(null, version), false);
});


test("calendarPreviewMatch only matches the served calendar frame", () => {
  const version = "f".repeat(64);
  assert.equal(calendarPreviewMatch({page: "calendar", frame_version: version}, version), true);
  assert.equal(calendarPreviewMatch({page: "calendar", frame_version: "e".repeat(64)}, version), false);
  assert.equal(calendarPreviewMatch({page: "memo", frame_version: version}, version), false);
  assert.equal(calendarPreviewMatch(null, version), false);
  assert.equal(calendarPreviewMatch({page: "calendar", frame_version: version}, ""), false);
});


test("buildTakeoutDraft normalizes rows and drops empty names", () => {
  const draft = buildTakeoutDraft([
    {id: "t1", name: " 牛肉面 ", status: "delivering", expected_at: "12:30", note: " 放前台 "},
    {id: "t2", name: "  ", status: "waiting", expected_at: "", note: ""},
    {id: "", name: "水果", status: "arrived", expected_at: "12:05", note: ""},
  ], {newId: (index) => `new-${index}`});

  assert.deepEqual(draft.orders, [
    {id: "t1", name: "牛肉面", status: "delivering", expected_at: "12:30", note: "放前台"},
    {id: "new-2", name: "水果", status: "arrived", expected_at: "12:05"},
  ]);
});


test("buildTakeoutDraft enforces the takeout contract", () => {
  const row = {id: "t1", name: "面", status: "waiting", expected_at: "12:30", note: ""};

  assert.deepEqual(buildTakeoutDraft([]), {orders: []});
  assert.throws(() => buildTakeoutDraft(Array(7).fill({...row})), /最多 6 单/);
  assert.throws(() => buildTakeoutDraft([{...row, id: "bad id"}]), /标识/);
  assert.throws(() => buildTakeoutDraft([{...row, status: "late"}]), /状态/);
  assert.throws(() => buildTakeoutDraft([{...row, expected_at: "9:05"}]), /HH:MM/);
  assert.throws(() => buildTakeoutDraft([{...row, expected_at: "24:00"}]), /HH:MM/);
  assert.throws(() => buildTakeoutDraft([{...row, note: "123456789"}]), /备注/);
  assert.throws(() => buildTakeoutDraft([{...row, name: "x".repeat(21)}]), /名称/);
  assert.throws(() => buildTakeoutDraft([row, {...row}]), /重复/);
});


test("takeoutSaveReport reflects the served takeout frame", () => {
  assert.deepEqual(takeoutSaveReport(null, null), {label: "状态未知", tone: "idle"});
  assert.match(
    takeoutSaveReport({}, {page: "memo"}).label,
    /设备当前显示其他页面/,
  );
  assert.match(
    takeoutSaveReport({}, {page: "takeout", frame_version: null}).label,
    /等待设备下一次轮询/,
  );
  const accepted = takeoutSaveReport(
    {},
    {page: "takeout", frame_version: "a".repeat(64), device: {accepted_frame_version: "a".repeat(64)}},
  );
  assert.equal(accepted.tone, "ok");
});
