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

export function pageSwitchState(status, desired) {
  if (!status || !status.page || !desired || status.page !== desired) {
    return status && desired ? "pending" : "expired";
  }
  return status.frame_version ? "active" : "expired";
}

export function memoSaveReport(saved, status) {
  if (!saved || !status) {
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
  if (state === "active") return "设备已显示";
  if (state === "pending") return "等待切换";
  return "等待取帧";
}
