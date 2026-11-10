const EVENT_PREFIX = "web-";

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

function defaultId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function buildDraft(values, source, options = {}) {
  const now = options.now ?? (() => new Date());
  const id = options.id ?? defaultId;
  const data = {};

  const title = text(values.title);
  if (title) {
    data.title = title;
  }

  const progressText =
    values.progress === undefined || values.progress === null
      ? ""
      : String(values.progress).trim();
  if (progressText !== "") {
    const progress = Number(progressText);
    if (Number.isFinite(progress)) {
      data.progress = Math.max(0, Math.min(100, Math.trunc(progress)));
    }
  }

  const currentStep = text(values.currentStep);
  if (currentStep) {
    data.current_step = currentStep;
  }

  const status = text(values.status);
  if (status) {
    data.status = status;
  }

  const description = text(values.description);
  if (description) {
    data.description = description;
  }

  const tags = text(values.tags)
    .split(/[,，]/)
    .map((tag) => tag.trim())
    .filter(Boolean);
  if (tags.length > 0) {
    data.tags = tags;
  }

  const contentSource = text(values.contentSource);
  if (contentSource) {
    data.source = contentSource;
  }

  return {
    event_id: `${EVENT_PREFIX}${id()}`,
    type: "panel.update",
    source,
    panel: "progress",
    occurred_at: now().toISOString(),
    data,
  };
}

export function statusReport(status, draft, options = {}) {
  if (options.pollFailed) {
    return {
      label: options.lastSuccessText
        ? `状态未知（读取失败；最近成功 ${options.lastSuccessText}）`
        : "状态未知（读取失败）",
      tone: "error",
    };
  }
  if (!status?.source) {
    return {label: "Host 未配置发布源", tone: "error"};
  }
  if (!draft) {
    return {label: "等待发布", tone: "idle"};
  }

  const device = status.device ?? {};
  if (status.publish_id !== draft.event.event_id) {
    return {label: "等待 Host 接受本次发布", tone: "warn"};
  }
  if (status.frame_version && status.frame_version !== draft.frameVersion) {
    return {label: "预览与发布帧不一致", tone: "error"};
  }
  if (
    device.refresh_stage === "DEVICE_REFRESH_FLOW_COMPLETE" &&
    device.accepted_frame_version === draft.frameVersion
  ) {
    return {label: "刷新流程完成（软件报告）", tone: "ok"};
  }
  if (device.accepted_frame_version === draft.frameVersion) {
    return {label: "设备已接受", tone: "ok"};
  }
  if (status.host_stage === "FRAME_READY") {
    return {label: "帧已就绪，等待设备取帧", tone: "ok"};
  }
  if (device.last_seen) {
    return {label: "设备已通信，等待本次帧接受", tone: "warn"};
  }
  if (status.host_stage === "HOST_ACCEPTED") {
    return {label: "Host 已接收，等待设备取帧", tone: "ok"};
  }
  return {label: "等待设备报告", tone: "warn"};
}

export function previewMatches(status, draft) {
  return Boolean(
    draft?.event?.event_id &&
      status?.publish_id === draft.event.event_id &&
      status?.frame_version &&
      status.frame_version === draft.frameVersion,
  );
}

export function previewOutcome(status, preview) {
  if (!preview) {
    return {label: "预览与发布使用同一份草稿；修改后需重新预览。", tone: "idle"};
  }
  if (!status?.publish_id || status.publish_id !== preview.event.event_id) {
    return {label: "预览已生成；发布后将与 Host 帧版本比对。", tone: "idle"};
  }
  if (!status.frame_version) {
    return {label: "Host 已接收本次发布，帧尚未就绪。", tone: "warn"};
  }
  return previewMatches(status, preview)
    ? {label: "预览与发布帧一致（同一 SHA-256）", tone: "ok"}
    : {label: "预览与发布帧不一致", tone: "error"};
}

export function formSignature(values) {
  // Same normalization as buildDraft; excludes the generated id and time.
  const probe = buildDraft(values, "signature", {
    now: () => new Date(0),
    id: () => "probe",
  });
  return JSON.stringify(probe.data);
}

export function canPublish(draft, dirty, source) {
  return Boolean(
    !dirty && !draft?.published && source && draft?.event?.event_id && draft?.frameVersion,
  );
}

const OPERATOR_MESSAGES = [
  [/^Layout: tags exceed column/i, "标签过长：最多显示两个标签，且总宽度需放得下。"],
  [/^Layout:/i, "内容超出安全排版区域：请缩短标题、当前步骤或描述。"],
  [/^Font\/layout:/i, "内容包含不支持的字符或控制符。"],
  [/^Font:/i, "内容包含字体无法显示的字符。"],
  [/Text has no visible contrast/i, "文字与背景对比不足，最终帧会不可见：请缩短或调整内容。"],
  [/Business frame unavailable/i, "当前内容无法生成业务帧（状态不得为 WAITING DATA / UPDATE FAILED）。"],
  [/Panel data is incomplete or invalid/i, "内容不完整或格式不正确，无法生成 Progress 帧。"],
  [/Progress event required/i, "仅支持 Progress 面板。"],
  [/Complete immutable T frame required/i, "生成帧不完整，已阻止发布。"],
];

export function operatorErrorMessage(detail, fallback = "请求失败，请稍后再试。") {
  if (Array.isArray(detail)) {
    return "请求格式不正确：请检查表单内容。";
  }
  if (typeof detail === "string") {
    const value = detail.trim();
    for (const [pattern, message] of OPERATOR_MESSAGES) {
      if (pattern.test(value)) {
        return message;
      }
    }
  }
  return fallback;
}

export function identityFields(pagesStatus, options = {}) {
  if (options.failed === true) {
    return {source: "UNKNOWN", frameFormat: "UNKNOWN", firmware: "UNKNOWN", lastSeen: "UNKNOWN"};
  }
  const device = pagesStatus?.device ?? null;
  return {
    source: pagesStatus?.source || "未配置",
    frameFormat: pagesStatus?.frame_format || "--",
    firmware: device?.firmware_version || "--",
    lastSeen: device?.last_seen || "未通信",
  };
}

export function formatVersion(value) {
  const normalized = typeof value === "string" ? value.replace(/^"|"$/g, "") : "";
  if (!normalized) {
    return "—";
  }
  return normalized.length > 12 ? `${normalized.slice(0, 12)}…` : normalized;
}
