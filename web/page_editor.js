import {
  buildCourseDraft,
  buildMemoDraft,
  courseSaveReport,
  memoSaveReport,
  pageSwitchLabel,
  pageSwitchState,
  resolveOverrideCourse,
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

  const start = courseField("input", "time", course.start, "上课时间");
  start.addEventListener("change", () => {
    courseRows[index].start = start.value;
  });
  const end = courseField("input", "time", course.end, "下课时间");
  end.addEventListener("change", () => {
    courseRows[index].end = end.value;
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

  row.append(name, weekday, weeks, start, end, room, remove);
  return row;
}

function refreshOverrideOptions() {
  for (const select of elements.overrideRows.querySelectorAll(".override-course")) {
    const index = Number(select.dataset.index);
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
    ["cancel", "取消"], ["move_room", "换教室"], ["move_time", "调时间"],
  ]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    option.selected = override.action === value;
    action.append(option);
  }

  const room = courseField("input", "text", override.room, "调课教室", 16);
  room.addEventListener("input", () => {
    overrideRows[index].room = room.value;
  });

  const start = courseField("input", "time", override.start, "调课开始时间");
  start.addEventListener("change", () => {
    overrideRows[index].start = start.value;
  });
  const end = courseField("input", "time", override.end, "调课结束时间");
  end.addEventListener("change", () => {
    overrideRows[index].end = end.value;
  });

  const updateVisibility = () => {
    room.hidden = action.value !== "move_room";
    start.hidden = action.value !== "move_time";
    end.hidden = action.value !== "move_time";
  };
  action.addEventListener("change", () => {
    overrideRows[index].action = action.value;
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

  row.append(date, course, action, room, start, end, remove);
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
  }));
  overrideRows = (data.overrides || []).map((override) => ({
    ...override,
    room: override.room || "",
    start: override.start || "",
    end: override.end || "",
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
      start: "08:00",
      end: "09:00",
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
      start: "",
      end: "",
    });
    renderOverrideRows();
  });
  document.querySelector("#course-form").addEventListener("submit", saveCourse);
  elements.coursePreview.addEventListener("click", () => requestCoursePreview());
  elements.weatherRefresh.addEventListener("click", refreshWeather);
  elements.weatherPreview.addEventListener("click", () => requestWeatherPreview());
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
