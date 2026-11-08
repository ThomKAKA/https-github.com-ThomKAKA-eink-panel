import {
  buildCourseDraft,
  buildMemoDraft,
  buildTakeoutDraft,
  calendarPreviewMatch,
  codexPreviewMatch,
  codexSummary,
  courseSaveReport,
  memoSaveReport,
  pageSwitchLabel,
  pageSwitchState,
  petSummary,
  resolveOverrideCourse,
  takeoutSaveReport,
  weatherSummary,
} from "./page_logic.mjs";
import { formatVersion, operatorErrorMessage } from "./manage_logic.mjs";

const elements = {
  switcher: document.querySelector("#page-switcher"),
  title: document.querySelector("#manage-title"),
  pageLabel: document.querySelector("#page-state-label"),
  pageMessage: document.querySelector("#page-switch-message"),
  pagePublishId: document.querySelector("#page-publish-id"),
  pageFrameVersion: document.querySelector("#page-frame-version"),
  pageAccepted: document.querySelector("#page-accepted"),
  pageRefresh: document.querySelector("#page-refresh"),
  pageRefreshCount: document.querySelector("#page-refresh-count"),
  pageLastSeen: document.querySelector("#page-last-seen"),
  rows: document.querySelector("#memo-rows"),
  add: document.querySelector("#memo-add"),
  save: document.querySelector("#memo-save"),
  preview: document.querySelector("#memo-preview"),
  message: document.querySelector("#memo-message"),
  previewImage: document.querySelector("#memo-preview-image"),
  previewVersion: document.querySelector("#memo-preview-version"),
  previewMatch: document.querySelector("#memo-preview-match"),
  semesterStart: document.querySelector("#semester-start"),
  totalWeeks: document.querySelector("#total-weeks"),
  courseRows: document.querySelector("#course-rows"),
  courseAdd: document.querySelector("#course-add"),
  courseSave: document.querySelector("#course-save"),
  coursePreview: document.querySelector("#course-preview"),
  courseMessage: document.querySelector("#course-message"),
  overrideRows: document.querySelector("#override-rows"),
  overrideAdd: document.querySelector("#override-add"),
  coursePreviewImage: document.querySelector("#course-preview-image"),
  coursePreviewVersion: document.querySelector("#course-preview-version"),
  coursePreviewMatch: document.querySelector("#course-preview-match"),
  weatherSummary: document.querySelector("#weather-summary"),
  weatherRefresh: document.querySelector("#weather-refresh"),
  weatherPreview: document.querySelector("#weather-preview"),
  weatherMessage: document.querySelector("#weather-message"),
  weatherPreviewImage: document.querySelector("#weather-preview-image"),
  weatherPreviewVersion: document.querySelector("#weather-preview-version"),
  weatherPreviewMatch: document.querySelector("#weather-preview-match"),
  calendarSummary: document.querySelector("#calendar-summary"),
  calendarPreview: document.querySelector("#calendar-preview"),
  calendarMessage: document.querySelector("#calendar-message"),
  calendarPreviewImage: document.querySelector("#calendar-preview-image"),
  calendarPreviewVersion: document.querySelector("#calendar-preview-version"),
  calendarPreviewMatch: document.querySelector("#calendar-preview-match"),
  codexSummary: document.querySelector("#codex-summary"),
  codexPreview: document.querySelector("#codex-preview"),
  codexMessage: document.querySelector("#codex-message"),
  codexPreviewImage: document.querySelector("#codex-preview-image"),
  codexPreviewVersion: document.querySelector("#codex-preview-version"),
  codexPreviewMatch: document.querySelector("#codex-preview-match"),
  takeoutRows: document.querySelector("#takeout-rows"),
  takeoutAdd: document.querySelector("#takeout-add"),
  takeoutSave: document.querySelector("#takeout-save"),
  takeoutPreview: document.querySelector("#takeout-preview"),
  takeoutMessage: document.querySelector("#takeout-message"),
  takeoutPreviewImage: document.querySelector("#takeout-preview-image"),
  takeoutPreviewVersion: document.querySelector("#takeout-preview-version"),
  takeoutPreviewMatch: document.querySelector("#takeout-preview-match"),
  petSummary: document.querySelector("#pet-summary"),
  petName: document.querySelector("#pet-name"),
  petLevel: document.querySelector("#pet-level"),
  petSatiety: document.querySelector("#pet-satiety"),
  petMood: document.querySelector("#pet-mood"),
  petAffinity: document.querySelector("#pet-affinity"),
  petLast: document.querySelector("#pet-last"),
  petFeed: document.querySelector("#pet-feed"),
  petPet: document.querySelector("#pet-pet"),
  petPlay: document.querySelector("#pet-play"),
  petPreview: document.querySelector("#pet-preview"),
  petMessage: document.querySelector("#pet-message"),
  petPreviewImage: document.querySelector("#pet-preview-image"),
  petPreviewVersion: document.querySelector("#pet-preview-version"),
  petPreviewMatch: document.querySelector("#pet-preview-match"),
};

let pageStatus = null;
let memoDocument = null;
let memoRows = [];
let memoLoading = false;
let memoPreviewUrl = null;
let courseDocument = null;
let courseRows = [];
let overrideRows = [];
let courseLoading = false;
let coursePreviewUrl = null;
let weatherDocument = null;
let weatherLoading = false;
let weatherPreviewUrl = null;
let calendarPreviewUrl = null;
let calendarShownPage = null;
let codexPreviewUrl = null;
let codexShownPage = null;
let takeoutDocument = null;
let takeoutRows = [];
let takeoutLoading = false;
let takeoutPreviewUrl = null;
let petStateBody = null;
let petLoading = false;
let petPreviewUrl = null;
let petShownPage = null;
let switching = false;
let pageEpoch = 0;
let pollTimer = null;

function setMessage(element, value, tone = "") {
  if (!element) return;
  element.textContent = value;
  element.dataset.tone = tone;
}

function allocateId() {
  if (globalThis.crypto?.randomUUID) {
    return `m-${globalThis.crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;
  }
  return `m-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e9).toString(36)}`;
}

function pageTitle(pageId) {
  return pageStatus?.pages?.find((page) => page.id === pageId)?.title || pageId;
}

function renderSwitcher() {
  if (!elements.switcher) return;
  elements.switcher.replaceChildren();
  for (const page of pageStatus?.pages || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = page.title;
    button.dataset.page = page.id;
    button.disabled = switching;
    const active = page.id === pageStatus.page;
    button.setAttribute("aria-pressed", active ? "true" : "false");
    if (active) {
      button.dataset.state = pageSwitchState(pageStatus, page.id);
    }
    button.addEventListener("click", () => selectPage(page.id));
    elements.switcher.append(button);
  }
}

function applySections() {
  const current = pageStatus?.page;
  for (const section of document.querySelectorAll("[data-page-section]")) {
    section.hidden = section.dataset.pageSection !== current;
  }
  if (elements.title && current) {
    elements.title.textContent = `${pageTitle(current)} 管理`;
  }
}

function renderPageStatus() {
  if (!pageStatus) return;
  renderSwitcher();
  applySections();
  const state = pageSwitchState(pageStatus, pageStatus.page);
  elements.pageLabel.textContent = `${pageTitle(pageStatus.page)} · ${pageSwitchLabel(state)}`;
  elements.pageLabel.dataset.tone = state === "active" ? "ok" : "warn";
  elements.pagePublishId.textContent = pageStatus.publish_id || "--";
  elements.pageFrameVersion.textContent = pageStatus.frame_version
    ? formatVersion(pageStatus.frame_version)
    : "--";
  elements.pageAccepted.textContent = pageStatus.device?.accepted_frame_version
    ? formatVersion(pageStatus.device.accepted_frame_version)
    : "--";
  elements.pageRefresh.textContent = pageStatus.device?.refresh_stage || "--";
  elements.pageRefreshCount.textContent = Number.isInteger(pageStatus.device?.refresh_count)
    ? String(pageStatus.device.refresh_count)
    : "--";
  elements.pageLastSeen.textContent = pageStatus.device?.last_seen || "未通信";
  if (pageStatus.page === "memo" && memoDocument === null && !memoLoading) {
    loadMemo();
  }
  if (pageStatus.page === "course" && courseDocument === null && !courseLoading) {
    loadCourse();
  }
  if (pageStatus.page === "weather" && weatherDocument === null && !weatherLoading) {
    loadWeather();
  }
  if (pageStatus.page === "calendar") {
    if (calendarShownPage !== "calendar") {
      calendarShownPage = "calendar";
      requestCalendarPreview({silent: true});
    }
  } else {
    calendarShownPage = null;
  }
  if (pageStatus.page === "codex") {
    if (codexShownPage !== "codex") {
      codexShownPage = "codex";
      loadCodex();
    }
  } else {
    codexShownPage = null;
  }
  if (pageStatus.page === "takeout" && takeoutDocument === null && !takeoutLoading) {
    loadTakeout();
  }
  if (pageStatus.page === "pet") {
    if (petShownPage !== "pet") {
      petShownPage = "pet";
      loadPet();
    }
  } else {
    petShownPage = null;
  }
}

async function loadPageStatus(options = {}) {
  const epoch = pageEpoch;
  try {
    const response = await fetch("/api/pages/status", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const body = await response.json();
    if (epoch !== pageEpoch) return false;
    pageStatus = body;
    renderPageStatus();
    return true;
  } catch {
    if (!options.quiet && epoch === pageEpoch && elements.pageLabel) {
      elements.pageLabel.textContent = "页面状态读取失败";
      elements.pageLabel.dataset.tone = "error";
    }
    return false;
  }
}

async function selectPage(pageId) {
  if (switching || !pageStatus || pageId === pageStatus.page) return;
  switching = true;
  pageEpoch += 1;
  renderSwitcher();
  setMessage(elements.pageMessage, `正在切换到 ${pageTitle(pageId)}…`);
  try {
    const response = await fetch(`/api/pages/${encodeURIComponent(pageId)}/select`, {
      method: "POST",
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(operatorErrorMessage(body.detail, `HTTP ${response.status}`));
    }
    pageEpoch += 1;
    pageStatus = body;
    renderPageStatus();
    setMessage(
      elements.pageMessage,
      `已切换到 ${pageTitle(pageId)}；设备最迟在 60 s 轮询时取帧。`,
      "ok",
    );
  } catch (error) {
    setMessage(elements.pageMessage, `切换失败：${error.message}`, "error");
  } finally {
    switching = false;
    renderSwitcher();
  }
}

function makeRow(item, index) {
  const row = document.createElement("div");
  row.className = "memo-row";

  const face = document.createElement("select");
  face.setAttribute("aria-label", "事项状态");
  for (const [value, label] of [
    ["todo", "待办"],
    ["doing", "进行"],
    ["done", "完成"],
    ["note", "笔记"],
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    option.selected = item.face === value;
    face.append(option);
  }
  face.addEventListener("change", () => {
    memoRows[index].face = face.value;
  });

  const text = document.createElement("input");
  text.type = "text";
  text.maxLength = 60;
  text.value = item.text || "";
  text.autocomplete = "off";
  text.setAttribute("aria-label", "事项内容");
  text.addEventListener("input", () => {
    memoRows[index].text = text.value;
  });

  const due = document.createElement("input");
  due.type = "datetime-local";
  due.value = item.due ? item.due.replace(" ", "T") : "";
  due.setAttribute("aria-label", "截止时间");
  due.addEventListener("change", () => {
    memoRows[index].due = due.value;
  });

  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "删除";
  remove.setAttribute("aria-label", "删除事项");
  remove.addEventListener("click", () => {
    memoRows.splice(index, 1);
    renderRows();
    setMessage(elements.message, "已移除事项；保存后生效。", "warn");
  });

  row.append(face, text, due, remove);
  return row;
}

function renderRows() {
  elements.rows.replaceChildren();
  if (memoRows.length === 0) {
    const empty = document.createElement("p");
    empty.className = "fineprint";
    empty.textContent = "暂无事项。点击“添加事项”。";
    elements.rows.append(empty);
  }
  memoRows.forEach((item, index) => elements.rows.append(makeRow(item, index)));
  elements.add.disabled = memoRows.length >= 8;
}

function showMemo(documentBody) {
  memoDocument = documentBody;
  memoRows = (documentBody?.data?.items || []).map((item) => ({...item}));
  renderRows();
}

async function loadMemo() {
  if (memoLoading) return;
  memoLoading = true;
  try {
    const response = await fetch("/api/pages/memo", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showMemo(await response.json());
  } catch {
    setMessage(elements.message, "备忘录读取失败；保存功能暂不可用。", "error");
  } finally {
    memoLoading = false;
  }
}

function memoDraft() {
  return buildMemoDraft(memoRows);
}

function invalidatePreview() {
  if (memoPreviewUrl) {
    URL.revokeObjectURL(memoPreviewUrl);
    memoPreviewUrl = null;
  }
  elements.previewImage.hidden = true;
  elements.previewImage.removeAttribute("src");
  elements.previewVersion.textContent = "尚未预览";
  elements.previewMatch.textContent = "保存后 Host 会用同一数据生成设备帧。";
}

async function requestMemoPreview(options = {}) {
  let data = options.data;
  if (!data) {
    try {
      data = memoDraft();
    } catch (error) {
      setMessage(elements.message, error.message, "error");
      return;
    }
  }
  elements.preview.disabled = true;
  if (!options.silent) {
    setMessage(elements.message, "正在生成预览…");
  }
  try {
    const body = {
      ...data,
      revision: options.revision ?? memoDocument?.revision,
      updated_at: options.updated_at ?? memoDocument?.updated_at,
    };
    const response = await fetch("/api/pages/memo/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(operatorErrorMessage(detail.detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const version = response.headers.get("x-frame-version") || "";
    if (memoPreviewUrl) {
      URL.revokeObjectURL(memoPreviewUrl);
    }
    memoPreviewUrl = URL.createObjectURL(blob);
    elements.previewImage.src = memoPreviewUrl;
    elements.previewImage.hidden = false;
    elements.previewVersion.textContent = `帧版本 ${formatVersion(version)}`;
    elements.previewMatch.textContent =
      pageStatus?.page === "memo" && pageStatus.frame_version === version
        ? "与 Host 当前提供给设备的帧一致。"
        : "保存后 Host 将用同一数据生成设备帧。";
    if (!options.silent) {
      setMessage(elements.message, "预览已生成。", "ok");
    }
  } catch (error) {
    setMessage(elements.message, `预览失败：${error.message}`, "error");
  } finally {
    elements.preview.disabled = false;
  }
}

async function saveMemo(event) {
  event.preventDefault();
  let draft;
  try {
    draft = memoDraft();
  } catch (error) {
    setMessage(elements.message, error.message, "error");
    return;
  }
  if (!memoDocument) {
    setMessage(elements.message, "尚未载入备忘录，请稍后重试。", "error");
    return;
  }
  elements.save.disabled = true;
  setMessage(elements.message, "正在保存…");
  try {
    const response = await fetch("/api/pages/memo", {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({revision: memoDocument.revision, data: draft}),
    });
    const body = await response.json().catch(() => ({}));
    if (response.status === 409) {
      showMemo(body);
      invalidatePreview();
      setMessage(elements.message, "保存冲突：已载入最新版本，请重新编辑。", "warn");
      return;
    }
    if (!response.ok) {
      throw new Error(operatorErrorMessage(body.detail, `HTTP ${response.status}`));
    }
    showMemo(body);
    invalidatePreview();
    const refreshed = await loadPageStatus({quiet: true});
    const report = refreshed
      ? memoSaveReport(body, pageStatus)
      : {label: "已保存；页面状态读取失败。", tone: "warn"};
    setMessage(elements.message, report.label, report.tone);
    await requestMemoPreview({
      data: body.data,
      revision: body.revision,
      updated_at: body.updated_at,
      silent: true,
    });
  } catch (error) {
    setMessage(elements.message, `保存失败：${error.message}`, "error");
  } finally {
    elements.save.disabled = false;
  }
}

function weeksText(weeks) {
  const sorted = [...new Set(weeks || [])].sort((left, right) => left - right);
  const parts = [];
  let start = null;
  let previous = null;
  for (const week of sorted) {
    if (start === null) {
      start = week;
      previous = week;
    } else if (week === previous + 1) {
      previous = week;
    } else {
      parts.push(start === previous ? `${start}` : `${start}-${previous}`);
      start = week;
      previous = week;
    }
  }
  if (start !== null) {
    parts.push(start === previous ? `${start}` : `${start}-${previous}`);
  }
  return parts.join(",");
}

function courseField(tag, type, value, label, maxLength) {
  const field = document.createElement(tag);
  if (type) field.type = type;
  if (maxLength) field.maxLength = maxLength;
  field.value = value ?? "";
  field.setAttribute("aria-label", label);
  if (tag === "input" && type === "text") field.autocomplete = "off";
  return field;
}

function makeCourseRow(course, index) {
  const row = document.createElement("div");
  row.className = "course-row";

  const name = courseField("input", "text", course.name, "课程名", 24);
  name.addEventListener("input", () => {
    courseRows[index].name = name.value;
    refreshOverrideOptions();
  });

  const weekday = document.createElement("select");
  weekday.setAttribute("aria-label", "星期");
  for (const [value, label] of [
    [1, "周一"], [2, "周二"], [3, "周三"], [4, "周四"],
    [5, "周五"], [6, "周六"], [7, "周日"],
  ]) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = label;
    option.selected = Number(course.weekday) === value;
    weekday.append(option);
  }
  weekday.addEventListener("change", () => {
    courseRows[index].weekday = Number(weekday.value);
  });

  const weeks = courseField("input", "text", course.weeks, "周次，例如 1-8,10", 80);
  weeks.placeholder = "1-8,10";
  weeks.addEventListener("input", () => {
    courseRows[index].weeks = weeks.value;
  });

  const period = document.createElement("select");
  period.setAttribute("aria-label", "节次");
  for (let value = 1; value <= 5; value += 1) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = `第${value}节`;
    option.selected = Number(course.period) === value;
    period.append(option);
  }
  period.addEventListener("change", () => {
    courseRows[index].period = Number(period.value);
  });
  const room = courseField("input", "text", course.room, "教室", 16);
  room.addEventListener("input", () => {
    courseRows[index].room = room.value;
  });

  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "删除";
  remove.setAttribute("aria-label", "删除课程");
  remove.addEventListener("click", () => {
    const removed = courseRows[index].id;
    courseRows.splice(index, 1);
    overrideRows = overrideRows.filter((override) => override.course_id !== removed);
    renderCourseRows();
    renderOverrideRows();
    invalidateCoursePreview();
    setMessage(elements.courseMessage, "已移除课程及其调课；保存后生效。", "warn");
  });

  row.append(name, weekday, weeks, period, room, remove);
  return row;
}

function refreshOverrideOptions() {
  for (const select of elements.overrideRows.querySelectorAll(".override-course")) {
    const index = Number(select.dataset.index);
    if (overrideRows[index]?.action === "add") {
      select.replaceChildren();
      select.value = "";
      continue;
    }
    const desired = resolveOverrideCourse(overrideRows[index], courseRows);
    select.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "选择课程";
    select.append(placeholder);
    for (const course of courseRows) {
      const option = document.createElement("option");
      option.value = course.id;
      option.textContent = course.name || course.id;
      option.selected = course.id === desired;
      select.append(option);
    }
    select.value = desired;
    if (overrideRows[index]) overrideRows[index].course_id = desired;
  }
}

function makeOverrideRow(override, index) {
  const row = document.createElement("div");
  row.className = "override-row";

  const date = courseField("input", "date", override.date, "调课日期");
  date.addEventListener("change", () => {
    overrideRows[index].date = date.value;
  });

  const course = document.createElement("select");
  course.className = "override-course";
  course.dataset.index = String(index);
  course.setAttribute("aria-label", "调课课程");
  course.addEventListener("change", () => {
    overrideRows[index].course_id = course.value;
  });

  const action = document.createElement("select");
  action.setAttribute("aria-label", "调课动作");
  for (const [value, label] of [
    ["cancel", "取消"], ["move_room", "换教室"],
    ["move_period", "调节次"], ["add", "临时加课"],
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    option.selected = override.action === value;
    action.append(option);
  }

  const name = courseField("input", "text", override.name, "临时课程名", 24);
  name.addEventListener("input", () => {
    overrideRows[index].name = name.value;
  });

  const room = courseField("input", "text", override.room, "调课教室", 16);
  room.addEventListener("input", () => {
    overrideRows[index].room = room.value;
  });

  const period = document.createElement("select");
  period.setAttribute("aria-label", "调课节次");
  for (let value = 1; value <= 5; value += 1) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = `第${value}节`;
    option.selected = Number(override.period) === value;
    period.append(option);
  }
  period.addEventListener("change", () => {
    overrideRows[index].period = Number(period.value);
  });

  const updateVisibility = () => {
    const isAdd = action.value === "add";
    course.hidden = isAdd;
    name.hidden = !isAdd;
    room.hidden = !(action.value === "move_room" || isAdd);
    period.hidden = !(action.value === "move_period" || isAdd);
  };
  action.addEventListener("change", () => {
    overrideRows[index].action = action.value;
    if (action.value === "add") {
      const current = String(overrideRows[index].course_id || "");
      if (!current || courseRows.some((row) => row.id === current)) {
        overrideRows[index].course_id = `extra-${Date.now().toString(36)}-${index}`;
      }
    }
    updateVisibility();
  });
  updateVisibility();

  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "删除";
  remove.setAttribute("aria-label", "删除调课");
  remove.addEventListener("click", () => {
    overrideRows.splice(index, 1);
    renderOverrideRows();
    invalidateCoursePreview();
    setMessage(elements.courseMessage, "已移除调课；保存后生效。", "warn");
  });

  row.append(date, course, action, name, period, room, remove);
  return row;
}

function renderCourseRows() {
  elements.courseRows.replaceChildren();
  if (courseRows.length === 0) {
    const empty = document.createElement("p");
    empty.className = "fineprint";
    empty.textContent = "暂无课程。点击“添加课程”。";
    elements.courseRows.append(empty);
  }
  courseRows.forEach((course, index) => elements.courseRows.append(makeCourseRow(course, index)));
  elements.courseAdd.disabled = courseRows.length >= 12;
  refreshOverrideOptions();
}

function renderOverrideRows() {
  elements.overrideRows.replaceChildren();
  if (overrideRows.length === 0) {
    const empty = document.createElement("p");
    empty.className = "fineprint";
    empty.textContent = "暂无调课。";
    elements.overrideRows.append(empty);
  }
  overrideRows.forEach((override, index) => {
    elements.overrideRows.append(makeOverrideRow(override, index));
  });
  elements.overrideAdd.disabled = overrideRows.length >= 16;
  refreshOverrideOptions();
}

function showCourse(documentBody) {
  courseDocument = documentBody;
  const data = documentBody?.data || {};
  elements.semesterStart.value = data.semester_start || "";
  elements.totalWeeks.value = data.total_weeks ?? 18;
  courseRows = (data.courses || []).map((course) => ({
    ...course,
    weeks: weeksText(course.weeks || []),
    period: course.period ?? 1,
  }));
  overrideRows = (data.overrides || []).map((override) => ({
    ...override,
    room: override.room || "",
    period: override.period ?? 1,
    name: override.name || "",
  }));
  renderCourseRows();
  renderOverrideRows();
}

async function loadCourse() {
  if (courseLoading) return;
  courseLoading = true;
  try {
    const response = await fetch("/api/pages/course", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showCourse(await response.json());
  } catch {
    setMessage(elements.courseMessage, "课表读取失败；保存功能暂不可用。", "error");
  } finally {
    courseLoading = false;
  }
}

function courseDraft() {
  return buildCourseDraft({
    semester_start: elements.semesterStart.value,
    total_weeks: elements.totalWeeks.value,
    courses: courseRows,
    overrides: overrideRows,
  });
}

function invalidateCoursePreview() {
  if (coursePreviewUrl) {
    URL.revokeObjectURL(coursePreviewUrl);
    coursePreviewUrl = null;
  }
  elements.coursePreviewImage.hidden = true;
  elements.coursePreviewImage.removeAttribute("src");
  elements.coursePreviewVersion.textContent = "尚未预览";
  elements.coursePreviewMatch.textContent = "保存后 Host 会用同一数据生成设备帧。";
}

async function requestCoursePreview(options = {}) {
  let data = options.data;
  if (!data) {
    try {
      data = courseDraft();
    } catch (error) {
      setMessage(elements.courseMessage, error.message, "error");
      return;
    }
  }
  elements.coursePreview.disabled = true;
  if (!options.silent) {
    setMessage(elements.courseMessage, "正在生成预览…");
  }
  try {
    const body = {
      ...data,
      revision: options.revision ?? courseDocument?.revision,
      updated_at: options.updated_at ?? courseDocument?.updated_at,
    };
    const response = await fetch("/api/pages/course/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(operatorErrorMessage(detail.detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const version = response.headers.get("x-frame-version") || "";
    if (coursePreviewUrl) {
      URL.revokeObjectURL(coursePreviewUrl);
    }
    coursePreviewUrl = URL.createObjectURL(blob);
    elements.coursePreviewImage.src = coursePreviewUrl;
    elements.coursePreviewImage.hidden = false;
    elements.coursePreviewVersion.textContent = `帧版本 ${formatVersion(version)}`;
    elements.coursePreviewMatch.textContent =
      pageStatus?.page === "course" && pageStatus.frame_version === version
        ? "与 Host 当前提供给设备的帧一致。"
        : "保存后 Host 将用同一数据生成设备帧。";
    if (!options.silent) {
      setMessage(elements.courseMessage, "预览已生成。", "ok");
    }
  } catch (error) {
    setMessage(elements.courseMessage, `预览失败：${error.message}`, "error");
  } finally {
    elements.coursePreview.disabled = false;
  }
}

async function saveCourse(event) {
  event.preventDefault();
  let draft;
  try {
    draft = courseDraft();
  } catch (error) {
    setMessage(elements.courseMessage, error.message, "error");
    return;
  }
  if (!courseDocument) {
    setMessage(elements.courseMessage, "尚未载入课表，请稍后重试。", "error");
    return;
  }
  elements.courseSave.disabled = true;
  setMessage(elements.courseMessage, "正在保存…");
  try {
    const response = await fetch("/api/pages/course", {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({revision: courseDocument.revision, data: draft}),
    });
    const body = await response.json().catch(() => ({}));
    if (response.status === 409) {
      showCourse(body);
      invalidateCoursePreview();
      setMessage(elements.courseMessage, "保存冲突：已载入最新版本，请重新编辑。", "warn");
      return;
    }
    if (!response.ok) {
      throw new Error(operatorErrorMessage(body.detail, `HTTP ${response.status}`));
    }
    showCourse(body);
    invalidateCoursePreview();
    const refreshed = await loadPageStatus({quiet: true});
    const report = refreshed
      ? courseSaveReport(body, pageStatus)
      : {label: "已保存；页面状态读取失败。", tone: "warn"};
    setMessage(elements.courseMessage, report.label, report.tone);
    await requestCoursePreview({
      data: body.data,
      revision: body.revision,
      updated_at: body.updated_at,
      silent: true,
    });
  } catch (error) {
    setMessage(elements.courseMessage, `保存失败：${error.message}`, "error");
  } finally {
    elements.courseSave.disabled = false;
  }
}

function showWeather(documentBody) {
  weatherDocument = documentBody;
  const summary = weatherSummary(documentBody);
  elements.weatherSummary.textContent = summary.label;
  elements.weatherSummary.dataset.tone =
    summary.state === "ready" ? "ok" : summary.state === "stale" ? "warn" : "idle";
}

async function loadWeather() {
  if (weatherLoading) return;
  weatherLoading = true;
  try {
    const response = await fetch("/api/pages/weather", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showWeather(await response.json());
    await requestWeatherPreview({silent: true});
  } catch {
    setMessage(elements.weatherMessage, "天气文档读取失败。", "error");
  } finally {
    weatherLoading = false;
  }
}

async function requestWeatherPreview(options = {}) {
  elements.weatherPreview.disabled = true;
  if (!options.silent) {
    setMessage(elements.weatherMessage, "正在生成预览…");
  }
  try {
    const response = await fetch("/api/pages/weather/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: "{}",
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(operatorErrorMessage(detail.detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const version = response.headers.get("x-frame-version") || "";
    if (weatherPreviewUrl) {
      URL.revokeObjectURL(weatherPreviewUrl);
    }
    weatherPreviewUrl = URL.createObjectURL(blob);
    elements.weatherPreviewImage.src = weatherPreviewUrl;
    elements.weatherPreviewImage.hidden = false;
    elements.weatherPreviewVersion.textContent = `帧版本 ${formatVersion(version)}`;
    elements.weatherPreviewMatch.textContent =
      pageStatus?.page === "weather" && pageStatus.frame_version === version
        ? "与 Host 当前提供给设备的帧一致。"
        : "预览使用 Host 缓存的天气文档。";
    if (!options.silent) {
      setMessage(elements.weatherMessage, "预览已生成。", "ok");
    }
  } catch (error) {
    setMessage(elements.weatherMessage, `预览失败：${error.message}`, "error");
  } finally {
    elements.weatherPreview.disabled = false;
  }
}

async function refreshWeather() {
  elements.weatherRefresh.disabled = true;
  setMessage(elements.weatherMessage, "正在刷新天气…");
  try {
    const response = await fetch("/api/pages/weather/refresh", {method: "POST"});
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(operatorErrorMessage(body.detail, `HTTP ${response.status}`));
    if (body.ok) {
      setMessage(elements.weatherMessage, "天气已更新。", "ok");
    } else {
      setMessage(
        elements.weatherMessage,
        `刷新失败：${body.error || "未知错误"}；继续使用缓存。`,
        "warn",
      );
    }
    weatherDocument = null;
    await loadWeather();
  } catch (error) {
    setMessage(elements.weatherMessage, `刷新失败：${error.message}`, "error");
  } finally {
    elements.weatherRefresh.disabled = false;
  }
}

function showPet(stateBody) {
  petStateBody = stateBody;
  const summary = petSummary(stateBody);
  elements.petName.textContent = summary.name;
  elements.petLevel.textContent = summary.levelLabel;
  elements.petSatiety.textContent = summary.satietyLabel;
  elements.petMood.textContent = summary.moodLabel;
  elements.petAffinity.textContent = summary.affinityLabel;
  elements.petLast.textContent = stateBody?.last_interaction || "--";
  elements.petSummary.textContent =
    `${summary.fedLabel} · ${summary.satietyLabel} · ${summary.moodLabel}`;
  elements.petSummary.dataset.tone = summary.tone;
}

async function loadPet() {
  if (petLoading) return;
  petLoading = true;
  try {
    const response = await fetch("/api/pet/state", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showPet(await response.json());
    await requestPetPreview({silent: true});
  } catch {
    setMessage(elements.petMessage, "宠物状态读取失败。", "error");
  } finally {
    petLoading = false;
  }
}

async function requestPetPreview(options = {}) {
  elements.petPreview.disabled = true;
  try {
    const response = await fetch("/api/pages/pet/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: "{}",
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(operatorErrorMessage(detail.detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const version = response.headers.get("x-frame-version") || "";
    if (petPreviewUrl) {
      URL.revokeObjectURL(petPreviewUrl);
    }
    petPreviewUrl = URL.createObjectURL(blob);
    elements.petPreviewImage.src = petPreviewUrl;
    elements.petPreviewImage.hidden = false;
    elements.petPreviewVersion.textContent = `帧版本 ${formatVersion(version)}`;
    elements.petPreviewMatch.textContent =
      pageStatus?.page === "pet" && pageStatus.frame_version === version
        ? "与 Host 当前提供给设备的帧一致。"
        : "预览使用 Host 当前的宠物文档。";
    if (!options.silent) {
      setMessage(elements.petMessage, "预览已生成。", "ok");
    }
  } catch (error) {
    setMessage(elements.petMessage, `预览失败：${error.message}`, "error");
  } finally {
    elements.petPreview.disabled = false;
  }
}

const PET_ACTION_LABELS = {feed: "喂食", pet: "摸摸", play: "玩耍"};

async function petInteract(action) {
  const buttons = [elements.petFeed, elements.petPet, elements.petPlay];
  buttons.forEach((button) => { button.disabled = true; });
  setMessage(elements.petMessage, `正在${PET_ACTION_LABELS[action]}…`);
  try {
    const response = await fetch("/api/pet/interact", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({action}),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(operatorErrorMessage(body.detail, `HTTP ${response.status}`));
    }
    showPet(body.state);
    await loadPageStatus({quiet: true});
    await requestPetPreview({silent: true});
    setMessage(
      elements.petMessage,
      `${PET_ACTION_LABELS[action]}完成，等待设备下一次轮询（≤60 s）。`,
      "ok",
    );
  } catch (error) {
    setMessage(elements.petMessage, `${PET_ACTION_LABELS[action]}失败：${error.message}`, "error");
  } finally {
    buttons.forEach((button) => { button.disabled = false; });
  }
}

async function requestCalendarPreview(options = {}) {  elements.calendarPreview.disabled = true;
  if (!options.silent) {
    setMessage(elements.calendarMessage, "正在生成预览…");
  }
  try {
    const response = await fetch("/api/pages/calendar/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: "{}",
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(operatorErrorMessage(detail.detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const version = response.headers.get("x-frame-version") || "";
    if (calendarPreviewUrl) {
      URL.revokeObjectURL(calendarPreviewUrl);
    }
    calendarPreviewUrl = URL.createObjectURL(blob);
    elements.calendarPreviewImage.src = calendarPreviewUrl;
    elements.calendarPreviewImage.hidden = false;
    elements.calendarPreviewVersion.textContent = `帧版本 ${formatVersion(version)}`;
    elements.calendarPreviewMatch.textContent = calendarPreviewMatch(pageStatus, version)
      ? "与 Host 当前提供给设备的帧一致。"
      : "预览使用 Host 当天日期；设备在零点后取到新月份。";
    if (!options.silent) {
      setMessage(elements.calendarMessage, "预览已生成。", "ok");
    }
  } catch (error) {
    setMessage(elements.calendarMessage, `预览失败：${error.message}`, "error");
  } finally {
    elements.calendarPreview.disabled = false;
  }
}

function showCodex(documentBody) {
  const summary = codexSummary(documentBody);
  elements.codexSummary.textContent = summary.label;
  elements.codexSummary.dataset.tone =
    summary.state === "ready" ? "ok" : summary.state === "stale" ? "warn" : "idle";
}

async function loadCodex() {
  try {
    const response = await fetch("/api/pages/codex", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showCodex(await response.json());
    await requestCodexPreview({silent: true});
  } catch {
    setMessage(elements.codexMessage, "Codex 用量读取失败。", "error");
  }
}

async function requestCodexPreview(options = {}) {
  elements.codexPreview.disabled = true;
  if (!options.silent) {
    setMessage(elements.codexMessage, "正在生成预览…");
  }
  try {
    const response = await fetch("/api/pages/codex/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: "{}",
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(operatorErrorMessage(detail.detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const version = response.headers.get("x-frame-version") || "";
    if (codexPreviewUrl) {
      URL.revokeObjectURL(codexPreviewUrl);
    }
    codexPreviewUrl = URL.createObjectURL(blob);
    elements.codexPreviewImage.src = codexPreviewUrl;
    elements.codexPreviewImage.hidden = false;
    elements.codexPreviewVersion.textContent = `帧版本 ${formatVersion(version)}`;
    elements.codexPreviewMatch.textContent = codexPreviewMatch(pageStatus, version)
      ? "与 Host 当前提供给设备的帧一致。"
      : "预览使用 Host 缓存的用量文档。";
    if (!options.silent) {
      setMessage(elements.codexMessage, "预览已生成。", "ok");
    }
  } catch (error) {
    setMessage(elements.codexMessage, `预览失败：${error.message}`, "error");
  } finally {
    elements.codexPreview.disabled = false;
  }
}

const TAKEOUT_NEXT = {
  waiting: [["waiting", "待取"], ["delivering", "配送中"], ["arrived", "已到"]],
  delivering: [["delivering", "配送中"], ["arrived", "已到"]],
  arrived: [["arrived", "已到"]],
};

function makeTakeoutRow(order, index) {
  const row = document.createElement("div");
  row.className = "takeout-row";

  const name = document.createElement("input");
  name.type = "text";
  name.maxLength = 20;
  name.placeholder = "店名 / 餐品";
  name.value = order.name;
  name.setAttribute("aria-label", "外卖名称");

  const status = document.createElement("select");
  status.setAttribute("aria-label", "外卖状态");
  for (const [value, label] of TAKEOUT_NEXT[order.status] || TAKEOUT_NEXT.waiting) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    status.append(option);
  }
  status.value = order.status;

  const expected = document.createElement("input");
  expected.type = "time";
  expected.value = order.expected_at || "";
  expected.setAttribute("aria-label", "预计送达时间");

  const note = document.createElement("input");
  note.type = "text";
  note.maxLength = 8;
  note.placeholder = "备注（8 字内）";
  note.value = order.note || "";
  note.setAttribute("aria-label", "备注");

  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "删除";
  remove.addEventListener("click", () => {
    takeoutRows.splice(index, 1);
    renderTakeoutRows();
    invalidateTakeoutPreview();
  });

  name.addEventListener("input", () => {
    takeoutRows[index].name = name.value;
    invalidateTakeoutPreview();
  });
  status.addEventListener("change", () => {
    takeoutRows[index].status = status.value;
    renderTakeoutRows();
    invalidateTakeoutPreview();
  });
  expected.addEventListener("input", () => {
    takeoutRows[index].expected_at = expected.value;
    invalidateTakeoutPreview();
  });
  note.addEventListener("input", () => {
    takeoutRows[index].note = note.value;
    invalidateTakeoutPreview();
  });

  row.append(name, status, expected, note, remove);
  return row;
}

function renderTakeoutRows() {
  elements.takeoutRows.replaceChildren();
  takeoutRows.forEach((order, index) => {
    elements.takeoutRows.append(makeTakeoutRow(order, index));
  });
}

function showTakeout(documentBody) {
  takeoutDocument = documentBody;
  takeoutRows = (documentBody?.data?.orders || []).map((order) => ({
    id: order.id,
    name: order.name,
    status: order.status,
    expected_at: order.expected_at || "",
    note: order.note || "",
  }));
  renderTakeoutRows();
}

async function loadTakeout() {
  if (takeoutLoading) return;
  takeoutLoading = true;
  try {
    const response = await fetch("/api/pages/takeout", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showTakeout(await response.json());
  } catch {
    setMessage(elements.takeoutMessage, "外卖页读取失败；保存功能暂不可用。", "error");
  } finally {
    takeoutLoading = false;
  }
}

function takeoutDraft() {
  return buildTakeoutDraft(takeoutRows);
}

function invalidateTakeoutPreview() {
  if (takeoutPreviewUrl) {
    URL.revokeObjectURL(takeoutPreviewUrl);
    takeoutPreviewUrl = null;
  }
  elements.takeoutPreviewImage.hidden = true;
  elements.takeoutPreviewImage.removeAttribute("src");
  elements.takeoutPreviewVersion.textContent = "尚未预览";
  elements.takeoutPreviewMatch.textContent = "保存后 Host 会用同一数据生成设备帧。";
}

async function requestTakeoutPreview(options = {}) {
  let data = options.data;
  if (!data) {
    try {
      data = takeoutDraft();
    } catch (error) {
      setMessage(elements.takeoutMessage, error.message, "error");
      return;
    }
  }
  elements.takeoutPreview.disabled = true;
  if (!options.silent) {
    setMessage(elements.takeoutMessage, "正在生成预览…");
  }
  try {
    const body = {
      ...data,
      revision: options.revision ?? takeoutDocument?.revision,
      updated_at: options.updated_at ?? takeoutDocument?.updated_at,
    };
    const response = await fetch("/api/pages/takeout/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(operatorErrorMessage(detail.detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const version = response.headers.get("x-frame-version") || "";
    if (takeoutPreviewUrl) {
      URL.revokeObjectURL(takeoutPreviewUrl);
    }
    takeoutPreviewUrl = URL.createObjectURL(blob);
    elements.takeoutPreviewImage.src = takeoutPreviewUrl;
    elements.takeoutPreviewImage.hidden = false;
    elements.takeoutPreviewVersion.textContent = `帧版本 ${formatVersion(version)}`;
    elements.takeoutPreviewMatch.textContent =
      pageStatus?.page === "takeout" && pageStatus.frame_version === version
        ? "与 Host 当前提供给设备的帧一致。"
        : "保存后 Host 将用同一数据生成设备帧。";
    if (!options.silent) {
      setMessage(elements.takeoutMessage, "预览已生成。", "ok");
    }
  } catch (error) {
    setMessage(elements.takeoutMessage, `预览失败：${error.message}`, "error");
  } finally {
    elements.takeoutPreview.disabled = false;
  }
}

async function saveTakeout(event) {
  event.preventDefault();
  let draft;
  try {
    draft = takeoutDraft();
  } catch (error) {
    setMessage(elements.takeoutMessage, error.message, "error");
    return;
  }
  if (!takeoutDocument) {
    setMessage(elements.takeoutMessage, "尚未载入外卖页，请稍后重试。", "error");
    return;
  }
  elements.takeoutSave.disabled = true;
  setMessage(elements.takeoutMessage, "正在保存…");
  try {
    const response = await fetch("/api/pages/takeout", {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({revision: takeoutDocument.revision, data: draft}),
    });
    const body = await response.json().catch(() => ({}));
    if (response.status === 409) {
      showTakeout(body);
      invalidateTakeoutPreview();
      setMessage(elements.takeoutMessage, "保存冲突：已载入最新版本，请重新编辑。", "warn");
      return;
    }
    if (!response.ok) {
      throw new Error(operatorErrorMessage(body.detail, `HTTP ${response.status}`));
    }
    showTakeout(body);
    invalidateTakeoutPreview();
    const refreshed = await loadPageStatus({quiet: true});
    const report = refreshed
      ? takeoutSaveReport(body, pageStatus)
      : {label: "已保存；页面状态读取失败。", tone: "warn"};
    setMessage(elements.takeoutMessage, report.label, report.tone);
    await requestTakeoutPreview({
      data: body.data,
      revision: body.revision,
      updated_at: body.updated_at,
      silent: true,
    });
  } catch (error) {
    setMessage(elements.takeoutMessage, `保存失败：${error.message}`, "error");
  } finally {
    elements.takeoutSave.disabled = false;
  }
}

export function initPageEditor() {
  if (!elements.switcher) return;
  elements.add.addEventListener("click", () => {
    if (memoRows.length >= 8) {
      setMessage(elements.message, "最多 8 项。", "error");
      return;
    }
    memoRows.push({id: allocateId(), text: "", due: "", face: "todo"});
    renderRows();
  });
  elements.rows.addEventListener("input", () => {
    invalidatePreview();
  });
  elements.rows.addEventListener("change", () => {
    invalidatePreview();
  });
  document.querySelector("#memo-form").addEventListener("submit", saveMemo);
  elements.preview.addEventListener("click", () => requestMemoPreview());

  elements.courseAdd.addEventListener("click", () => {
    if (courseRows.length >= 12) {
      setMessage(elements.courseMessage, "最多 12 门课程。", "error");
      return;
    }
    courseRows.push({
      id: `c-${allocateId().slice(2)}`,
      name: "",
      weekday: 1,
      weeks: "1",
      period: 1,
      room: "",
    });
    renderCourseRows();
  });
  elements.overrideAdd.addEventListener("click", () => {
    if (overrideRows.length >= 16) {
      setMessage(elements.courseMessage, "最多 16 条调课。", "error");
      return;
    }
    overrideRows.push({
      date: "",
      course_id: "",
      action: "cancel",
      room: "",
      period: 1,
      name: "",
    });
    renderOverrideRows();
  });
  document.querySelector("#course-form").addEventListener("submit", saveCourse);
  elements.coursePreview.addEventListener("click", () => requestCoursePreview());
  elements.weatherRefresh.addEventListener("click", refreshWeather);
  elements.weatherPreview.addEventListener("click", () => requestWeatherPreview());
  elements.petFeed.addEventListener("click", () => petInteract("feed"));
  elements.petPet.addEventListener("click", () => petInteract("pet"));
  elements.petPlay.addEventListener("click", () => petInteract("play"));
  elements.petPreview.addEventListener("click", () => requestPetPreview());
  elements.calendarPreview.addEventListener("click", () => requestCalendarPreview());
  elements.codexPreview.addEventListener("click", () => requestCodexPreview());
  elements.takeoutAdd.addEventListener("click", () => {
    if (takeoutRows.length >= 6) {
      setMessage(elements.takeoutMessage, "最多 6 单。", "error");
      return;
    }
    takeoutRows.push({
      id: allocateId(),
      name: "",
      status: "waiting",
      expected_at: "",
      note: "",
    });
    renderTakeoutRows();
    invalidateTakeoutPreview();
  });
  document.querySelector("#takeout-form").addEventListener("submit", saveTakeout);
  elements.takeoutPreview.addEventListener("click", () => requestTakeoutPreview());
  for (const element of [
    elements.courseRows,
    elements.overrideRows,
    elements.semesterStart,
    elements.totalWeeks,
  ]) {
    element.addEventListener("input", invalidateCoursePreview);
    element.addEventListener("change", invalidateCoursePreview);
  }

  loadPageStatus();
  pollTimer = window.setInterval(loadPageStatus, 10000);
  window.addEventListener("beforeunload", () => {
    if (pollTimer) window.clearInterval(pollTimer);
  });
}
