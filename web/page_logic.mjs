const ID_PATTERN = /^[A-Za-z0-9_-]{1,32}$/;
const FACES = new Set(["todo", "doing", "done", "note"]);

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

export function normalizeDue(value) {
  const candidate = text(value);
  if (!candidate) {
    return null;
  }
  const match = /^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})/.exec(candidate);
  return match ? `${match[1]} ${match[2]}` : null;
}

function defaultId(index) {
  return `memo-${Date.now().toString(36)}-${index}`;
}

export function buildMemoDraft(rows, options = {}) {
  const newId = options.newId || defaultId;
  const items = [];
  for (const [index, row] of (rows || []).entries()) {
    const itemText = text(row?.text);
    if (!itemText) {
      continue;
    }
    let id = text(row?.id);
    if (!id) {
      id = newId(index);
    }
    if (!ID_PATTERN.test(id)) {
      throw new Error("事项标识无效");
    }
    items.push({
      id,
      text: itemText,
      due: normalizeDue(row?.due),
      face: FACES.has(row?.face) ? row.face : "todo",
    });
  }
  if (items.length > 8) {
    throw new Error("最多 8 项");
  }
  if (new Set(items.map((item) => item.id)).size !== items.length) {
    throw new Error("事项标识重复");
  }
  return {items};
}

const TAKEOUT_STATUSES = new Set(["waiting", "delivering", "arrived"]);
const TAKEOUT_MINUTE = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

function defaultTakeoutId(index) {
  return `takeout-${Date.now().toString(36)}-${index}`;
}

export function buildTakeoutDraft(rows, options = {}) {
  const newId = options.newId || defaultTakeoutId;
  const orders = [];
  for (const [index, row] of (rows || []).entries()) {
    const name = text(row?.name);
    if (!name) {
      continue;
    }
    let id = text(row?.id);
    if (!id) {
      id = newId(index);
    }
    if (!ID_PATTERN.test(id)) {
      throw new Error("外卖单标识无效");
    }
    if (!TAKEOUT_STATUSES.has(row?.status)) {
      throw new Error("外卖状态无效");
    }
    const expected = text(row?.expected_at);
    if (expected && !TAKEOUT_MINUTE.test(expected)) {
      throw new Error("预计时间要写成 HH:MM");
    }
    const note = text(row?.note);
    if (name.length > 20) {
      throw new Error("名称最多 20 个字");
    }
    if (note.length > 8) {
      throw new Error("备注最多 8 个字");
    }
    const order = {id, name, status: row.status, expected_at: expected || null};
    if (note) {
      order.note = note;
    }
    orders.push(order);
  }
  if (orders.length > 6) {
    throw new Error("最多 6 单");
  }
  if (new Set(orders.map((order) => order.id)).size !== orders.length) {
    throw new Error("外卖单标识重复");
  }
  return {orders};
}

export function weatherSummary(documentBody) {  const data = documentBody?.data || {};
  const updated = typeof data.updated_at === "string"
    ? data.updated_at
    : typeof documentBody?.updated_at === "string"
      ? documentBody.updated_at
      : "";
  const hasData = Array.isArray(data.hourly) && data.hourly.length > 0
    && data.current_temp !== null && data.current_temp !== undefined;
  if (!hasData) {
    return {state: "waiting", label: "尚未获取天气数据", canRefresh: true};
  }
  if (data.stale === true) {
    return {state: "stale", label: `缓存数据 · 更新 ${updated || "--"}`, canRefresh: true};
  }
  return {state: "ready", label: `已更新 ${updated || "--"}`, canRefresh: true};
}

export function calendarPreviewMatch(status, version) {
  return Boolean(version && status?.page === "calendar" && status.frame_version === version);
}

export function petSummary(stateBody) {
  const state = stateBody || {};
  const name = typeof state.name === "string" && state.name ? state.name : "大肥鱼";
  const level = Number.isInteger(state.level) ? state.level : 1;
  const satiety = Number.isInteger(state.satiety) ? state.satiety : 0;
  const mood = Number.isInteger(state.mood) ? state.mood : 0;
  const affinity = Number.isInteger(state.affinity) ? state.affinity : 0;
  const fedToday = state.fed_today === true;
  return {
    name,
    levelLabel: `Lv.${level}`,
    satietyLabel: `${state.satiety_label || "未知"} · ${satiety}`,
    moodLabel: `${state.mood_label || "未知"} · ${mood}`,
    affinityLabel: `亲密 ${affinity}`,
    fedLabel: fedToday ? "今天已喂" : "今天还没喂",
    tone: fedToday ? "ok" : "idle",
    canInteract: state.page === "pet",
  };
}

export function formatTokens(value) {
  const total = Number(value) || 0;
  if (total < 1000) return String(total);
  if (total < 1_000_000) return `${(total / 1000).toFixed(1)}k`;
  if (total < 1_000_000_000) return `${(total / 1_000_000).toFixed(1)}M`;
  return `${(total / 1_000_000_000).toFixed(2)}B`;
}

export function codexSummary(documentBody) {
  const data = documentBody?.data || {};
  if (data.today_tokens === null || data.today_tokens === undefined) {
    return {state: "waiting", label: "尚未同步 Codex 用量"};
  }
  const numbers = `今日 ${formatTokens(data.today_tokens)} · 近 7 天 `
    + `${formatTokens(data.week_tokens)} · 累计 ${formatTokens(data.total_tokens)}`;
  if (data.stale === true) {
    return {state: "stale", label: `STALE · ${numbers}`};
  }
  const updated = typeof documentBody?.updated_at === "string" ? documentBody.updated_at : "";
  return {state: "ready", label: `已同步 ${updated || "--"} · ${numbers}`};
}

export function codexPreviewMatch(status, version) {
  return Boolean(version && status?.page === "codex" && status.frame_version === version);
}

export function pageSwitchState(status, desired) {
  if (!status || !status.page || !desired || status.page !== desired) {
    return status && desired ? "pending" : "expired";
  }
  return status.frame_version ? "active" : "expired";
}

export function takeoutSaveReport(saved, status) {
  if (!saved || !status) {
    return {label: "状态未知", tone: "idle"};
  }
  if (status.page !== "takeout") {
    return {label: "外卖页已保存；设备当前显示其他页面。", tone: "warn"};
  }
  if (!status.frame_version) {
    return {label: "已保存，等待设备下一次轮询（≤60 s）。", tone: "warn"};
  }
  if (status.device?.accepted_frame_version === status.frame_version) {
    return {label: "设备已接受当前帧。", tone: "ok"};
  }
  return {label: "设备已取帧，等待软件报告。", tone: "warn"};
}

export function memoSaveReport(saved, status) {  if (!saved || !status) {
    return {label: "状态未知", tone: "idle"};
  }
  if (status.page !== "memo") {
    return {label: "备忘录已保存；设备当前显示其他页面。", tone: "warn"};
  }
  if (!status.frame_version) {
    return {label: "已保存，等待设备下一次轮询（≤60 s）。", tone: "warn"};
  }
  if (status.device?.accepted_frame_version === status.frame_version) {
    return {label: "设备已接受当前帧。", tone: "ok"};
  }
  return {label: "设备已取帧，等待软件报告。", tone: "warn"};
}

export function pageSwitchLabel(state) {
  if (state === "active") return "Host 已提供当前帧";
  if (state === "pending") return "等待切换";
  return "等待设备取帧";
}

function periodOf(value, message) {
  const candidate = Number(value);
  if (!Number.isInteger(candidate) || candidate < 1 || candidate > 5) {
    throw new Error(message);
  }
  return candidate;
}

function validDate(value, message) {
  const candidate = text(value);
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(candidate);
  if (!match) {
    throw new Error(message);
  }
  const [year, month, day] = match.slice(1).map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (
    parsed.getUTCFullYear() !== year
    || parsed.getUTCMonth() !== month - 1
    || parsed.getUTCDate() !== day
  ) {
    throw new Error(message);
  }
  return candidate;
}

export function parseWeeks(value, totalWeeks) {
  const total = Number(totalWeeks);
  if (!Number.isInteger(total) || total < 1 || total > 30) {
    throw new Error("总周数必须为 1-30 周");
  }
  const candidate = text(value);
  if (!candidate) {
    throw new Error("周次不能为空");
  }
  const weeks = [];
  for (const part of candidate.split(",")) {
    const segment = part.trim();
    if (!segment) {
      throw new Error("周次格式无效");
    }
    if (segment.includes("-")) {
      if (segment.split("-").length !== 2) {
        throw new Error("周次格式无效");
      }
      const [first, last] = segment.split("-").map(Number);
      if (!Number.isInteger(first) || !Number.isInteger(last) || first > last) {
        throw new Error("周次格式无效");
      }
      for (let week = first; week <= last; week += 1) {
        weeks.push(week);
      }
    } else {
      const week = Number(segment);
      if (!Number.isInteger(week)) {
        throw new Error("周次格式无效");
      }
      weeks.push(week);
    }
  }
  if (weeks.some((week) => week < 1 || week > total)) {
    throw new Error("周次超出学期范围");
  }
  if (new Set(weeks).size !== weeks.length) {
    throw new Error("周次重复");
  }
  return weeks.sort((left, right) => left - right);
}

export function buildCourseDraft(values, options = {}) {
  const newId = options.newId || ((index) => `course-${Date.now().toString(36)}-${index}`);
  const total = Number(values?.total_weeks);
  if (!Number.isInteger(total) || total < 1 || total > 30) {
    throw new Error("总周数必须为 1-30 周");
  }
  const semester = validDate(values?.semester_start, "学期起始日期无效");
  const courses = [];
  for (const [index, row] of (values?.courses || []).entries()) {
    const name = text(row?.name);
    const hasContent = name || text(row?.weeks) || text(row?.room) || text(row?.period);
    if (!hasContent) {
      continue;
    }
    let id = text(row?.id);
    if (!id) {
      id = newId(index);
    }
    if (!ID_PATTERN.test(id)) {
      throw new Error("课程标识无效");
    }
    if (!name || name.length > 24) {
      throw new Error("课程名必须为 1-24 字");
    }
    const weekday = Number(row?.weekday);
    if (!Number.isInteger(weekday) || weekday < 1 || weekday > 7) {
      throw new Error("星期必须为 1-7");
    }
    const weeks = parseWeeks(row?.weeks, total);
    const period = periodOf(row?.period, "节次必须为 1-5");
    const room = text(row?.room);
    if (!room || room.length > 16) {
      throw new Error("教室必须为 1-16 字");
    }
    courses.push({id, name, weekday, weeks, period, room});
  }
  if (courses.length > 12) {
    throw new Error("最多 12 门课程");
  }
  if (new Set(courses.map((course) => course.id)).size !== courses.length) {
    throw new Error("课程标识重复");
  }
  const slots = courses.flatMap((course) =>
    course.weeks.map((week) => `${course.weekday}/${week}/${course.period}`));
  if (new Set(slots).size !== slots.length) {
    throw new Error("同一时段有多门课程");
  }

  const overrides = [];
  const known = new Set(courses.map((course) => course.id));
  const addDates = new Set();
  for (const row of values?.overrides || []) {
    const date = text(row?.date);
    const courseId = text(row?.course_id);
    const action = text(row?.action);
    if (!date && !courseId && !action) {
      continue;
    }
    validDate(date, "调课日期无效");
    if (!["cancel", "move_room", "move_period", "add"].includes(action)) {
      throw new Error("调课动作无效");
    }
    if (action === "add") {
      if (!ID_PATTERN.test(courseId)) {
        throw new Error("临时课程标识无效");
      }
      if (known.has(courseId)) {
        throw new Error("临时课程标识与已有课程重复");
      }
      if (addDates.has(date)) {
        throw new Error("同一天只能临时加一节课");
      }
      addDates.add(date);
      const name = text(row?.name);
      if (!name || name.length > 24) {
        throw new Error("课程名必须为 1-24 字");
      }
      const period = periodOf(row?.period, "节次必须为 1-5");
      const room = text(row?.room);
      if (!room || room.length > 16) {
        throw new Error("教室必须为 1-16 字");
      }
      overrides.push({date, course_id: courseId, action: "add", name, period, room});
      continue;
    }
    if (!known.has(courseId)) {
      throw new Error("调课引用的课程不存在");
    }
    const override = {date, course_id: courseId, action};
    if (action === "move_room") {
      const room = text(row?.room);
      if (!room || room.length > 16) {
        throw new Error("教室必须为 1-16 字");
      }
      override.room = room;
    } else if (action === "move_period") {
      override.period = periodOf(row?.period, "节次必须为 1-5");
    }
    overrides.push(override);
  }
  if (overrides.length > 16) {
    throw new Error("最多 16 条调课");
  }
  const keys = overrides.map((override) => `${override.date}/${override.course_id}`);
  if (new Set(keys).size !== keys.length) {
    throw new Error("同一天的调课重复");
  }
  return {semester_start: semester, total_weeks: total, courses, overrides};
}

export function resolveOverrideCourse(override, courses) {
  if (text(override?.action) === "add") return "";
  const id = text(override?.course_id);
  return (courses || []).some((course) => course.id === id) ? id : "";
}

export function courseSaveReport(saved, status) {
  if (!saved || !status) {
    return {label: "状态未知", tone: "idle"};
  }
  if (status.page !== "course") {
    return {label: "课表已保存；设备当前显示其他页面。", tone: "warn"};
  }
  if (!status.frame_version) {
    return {label: "已保存，等待设备下一次轮询（≤60 s）。", tone: "warn"};
  }
  if (status.device?.accepted_frame_version === status.frame_version) {
    return {label: "设备已接受当前帧。", tone: "ok"};
  }
  return {label: "设备已取帧，等待软件报告。", tone: "warn"};
}
