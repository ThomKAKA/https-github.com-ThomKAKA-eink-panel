import {
  buildMemoDraft,
  memoSaveReport,
  pageSwitchLabel,
  pageSwitchState,
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
  pageLastSeen: document.querySelector("#page-last-seen"),
  rows: document.querySelector("#memo-rows"),
  add: document.querySelector("#memo-add"),
  save: document.querySelector("#memo-save"),
  preview: document.querySelector("#memo-preview"),
  message: document.querySelector("#memo-message"),
  previewImage: document.querySelector("#memo-preview-image"),
  previewVersion: document.querySelector("#memo-preview-version"),
  previewMatch: document.querySelector("#memo-preview-match"),
};

let pageStatus = null;
let memoDocument = null;
let memoRows = [];
let memoLoading = false;
let memoPreviewUrl = null;
let switching = false;
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
  elements.pageLastSeen.textContent = pageStatus.device?.last_seen || "未通信";
  if (pageStatus.page === "memo" && memoDocument === null && !memoLoading) {
    loadMemo();
  }
}

async function loadPageStatus(options = {}) {
  try {
    const response = await fetch("/api/pages/status", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    pageStatus = await response.json();
    renderPageStatus();
  } catch {
    if (!options.quiet && elements.pageLabel) {
      elements.pageLabel.textContent = "页面状态读取失败";
      elements.pageLabel.dataset.tone = "error";
    }
  }
}

async function selectPage(pageId) {
  if (switching || !pageStatus || pageId === pageStatus.page) return;
  switching = true;
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
    const report = memoSaveReport(body, pageStatus);
    setMessage(elements.message, report.label, report.tone);
    await loadPageStatus({quiet: true});
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
  loadPageStatus();
  pollTimer = window.setInterval(loadPageStatus, 10000);
  window.addEventListener("beforeunload", () => {
    if (pollTimer) window.clearInterval(pollTimer);
  });
}
