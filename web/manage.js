import {
  buildDraft,
  canPublish,
  formSignature,
  formatVersion,
  operatorErrorMessage,
  previewOutcome,
  statusReport,
} from "./manage_logic.mjs";
import {
  canRegisterServiceWorker,
  installationHint,
  shouldOfferInstall,
} from "./pwa_logic.mjs";

const elements = {
  form: document.querySelector("#progress-form"),
  title: document.querySelector("#title"),
  progress: document.querySelector("#progress-input"),
  currentStep: document.querySelector("#current-step"),
  status: document.querySelector("#status"),
  description: document.querySelector("#description"),
  tags: document.querySelector("#tags"),
  contentSource: document.querySelector("#content-source"),
  previewButton: document.querySelector("#preview"),
  publishButton: document.querySelector("#publish"),
  formMessage: document.querySelector("#form-message"),
  previewImage: document.querySelector("#preview-image"),
  previewVersion: document.querySelector("#preview-version"),
  previewMatch: document.querySelector("#preview-match"),
  report: document.querySelector("#status-report"),
  publishId: document.querySelector("#status-publish-id"),
  hostStage: document.querySelector("#status-host-stage"),
  frameVersion: document.querySelector("#status-frame-version"),
  accepted: document.querySelector("#status-accepted"),
  refresh: document.querySelector("#status-refresh"),
  hostOrigin: document.querySelector("#host-origin"),
  hostSource: document.querySelector("#host-source"),
  frameFormat: document.querySelector("#frame-format"),
  deviceFirmware: document.querySelector("#device-firmware"),
  deviceLastSeen: document.querySelector("#device-last-seen"),
  installHint: document.querySelector("#install-hint"),
  installHintText: document.querySelector("#install-hint-text"),
  installButton: document.querySelector("#install-app"),
};

let status = null;
let preview = null;
let dirty = true;
let previewing = false;
let pollTimer = null;
let previewUrl = null;
let statusFailed = false;
let lastStatusAt = null;
let installPrompt = null;
let installFailure = "";

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  renderInstallHint();
});
window.addEventListener("appinstalled", () => {
  installPrompt = null;
  installFailure = "";
  renderInstallHint();
});

function setMessage(value, tone = "") {
  elements.formMessage.textContent = value;
  elements.formMessage.dataset.tone = tone;
}

function readForm() {
  return {
    title: elements.title.value,
    progress: elements.progress.value,
    currentStep: elements.currentStep.value,
    status: elements.status.value,
    description: elements.description.value,
    tags: elements.tags.value,
    contentSource: elements.contentSource.value,
  };
}

function updatePublishButton() {
  elements.publishButton.disabled =
    statusFailed || !canPublish(preview, dirty, status?.source);
}

function renderIdentity() {
  elements.hostOrigin.textContent = window.location.origin;
  elements.hostSource.textContent = statusFailed ? "UNKNOWN" : status?.source || "未配置";
  elements.frameFormat.textContent = statusFailed ? "UNKNOWN" : status?.frame_format || "--";
  elements.deviceFirmware.textContent = statusFailed
    ? "UNKNOWN"
    : status?.device?.firmware_version || "--";
  elements.deviceLastSeen.textContent = statusFailed
    ? "UNKNOWN"
    : status?.device?.last_seen || "未通信";
}

function renderReport() {
  const report = statusReport(status, preview, {
    pollFailed: statusFailed,
    lastSuccessText: lastStatusAt ? lastStatusAt.toLocaleTimeString() : "",
  });
  elements.report.textContent = report.label;
  elements.report.dataset.tone = report.tone;

  if (statusFailed) {
    for (const element of [
      elements.publishId,
      elements.hostStage,
      elements.frameVersion,
      elements.accepted,
      elements.refresh,
    ]) {
      element.textContent = "UNKNOWN";
    }
    elements.previewMatch.textContent = preview
      ? "状态未知：无法比对预览与发布帧。"
      : "状态未知。";
    elements.previewMatch.dataset.tone = "error";
    return;
  }

  elements.publishId.textContent = status?.publish_id || "--";
  elements.hostStage.textContent = status?.host_stage || "--";
  elements.frameVersion.textContent = status?.frame_version
    ? formatVersion(status.frame_version)
    : "--";
  elements.accepted.textContent = status?.device?.accepted_frame_version
    ? formatVersion(status.device.accepted_frame_version)
    : "--";
  elements.refresh.textContent = status?.device?.refresh_stage || "--";
  const outcome = previewOutcome(status, preview);
  elements.previewMatch.textContent = outcome.label;
  elements.previewMatch.dataset.tone = outcome.tone;
}

function invalidatePreview(message = "") {
  const hadPreview = Boolean(preview);
  preview = null;
  dirty = true;
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }
  elements.previewImage.hidden = true;
  elements.previewImage.removeAttribute("src");
  elements.previewVersion.textContent = "尚未预览";
  elements.previewMatch.textContent = "预览与发布使用同一份草稿；修改后需重新预览。";
  updatePublishButton();
  renderReport();
  if (hadPreview && message) {
    setMessage(message, "warn");
  }
}

async function loadStatus() {
  try {
    const response = await fetch("/api/panels/progress/status", {cache: "no-store"});
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    status = await response.json();
    statusFailed = false;
    lastStatusAt = new Date();
  } catch (error) {
    statusFailed = true;
    setMessage("状态读取失败，请确认 Host 仍在运行。", "error");
  }
  renderIdentity();
  renderReport();
  updatePublishButton();
}

async function requestPreview() {
  if (previewing) {
    return;
  }
  if (statusFailed) {
    setMessage("状态未知，请先恢复 Host 连接再预览。", "error");
    return;
  }
  if (!status?.source) {
    setMessage("Host 未配置 EINK_PROGRESS_SOURCE，无法预览或发布。", "error");
    return;
  }

  previewing = true;
  elements.previewButton.disabled = true;
  setMessage("正在生成最终帧预览…");
  const signature = formSignature(readForm());
  try {
    const event = buildDraft(readForm(), status.source);
    const response = await fetch("/api/panels/progress/preview", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(event),
    });
    if (!response.ok) {
      let detail;
      try {
        const body = await response.json();
        detail = body.detail;
      } catch {
        // Keep the status code when the error body is not JSON.
      }
      throw new Error(operatorErrorMessage(detail, `HTTP ${response.status}`));
    }
    const blob = await response.blob();
    const frameVersion = response.headers.get("x-frame-version") || "";
    if (!/^[0-9a-f]{64}$/.test(frameVersion)) {
      throw new Error("Host 未返回帧版本，预览不可用。");
    }
    if (formSignature(readForm()) !== signature) {
      setMessage("内容在预览生成期间已修改，请重新预览。", "warn");
      return;
    }
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    previewUrl = URL.createObjectURL(blob);
    preview = {event, frameVersion};
    dirty = false;
    elements.previewImage.src = previewUrl;
    elements.previewImage.hidden = false;
    elements.previewVersion.textContent = `帧版本 ${formatVersion(frameVersion)}`;
    setMessage("预览已生成。发布使用同一份草稿。", "ok");
    renderReport();
    updatePublishButton();
    startPolling(2000, true);
  } catch (error) {
    setMessage(`预览失败：${error.message}`, "error");
    invalidatePreview("");
  } finally {
    previewing = false;
    elements.previewButton.disabled = false;
  }
}

async function publishDraft() {
  if (statusFailed || !canPublish(preview, dirty, status?.source)) {
    return;
  }
  elements.publishButton.disabled = true;
  setMessage("正在发布…");
  try {
    const response = await fetch("/api/events", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(preview.event),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      if (response.status === 409) {
        setMessage("发布被拒绝：事件时间早于当前快照。请重新预览生成新草稿。", "error");
        invalidatePreview("");
      } else {
        setMessage(
          `发布失败：${operatorErrorMessage(body.detail, `HTTP ${response.status}`)}`,
          "error",
        );
      }
      return;
    }
    if (!body.accepted) {
      setMessage(
        body.reason === "duplicate" ? "该草稿已发布（重复事件）。" : "发布未被接受。",
        "warn",
      );
      preview.published = true;
    } else {
      setMessage("Host 已接收。等待设备取帧与软件报告。", "ok");
      preview.published = true;
    }
    startPolling(2000, true);
  } catch (error) {
    setMessage(`发布失败：${error.message}`, "error");
  } finally {
    updatePublishButton();
  }
}

function startPolling(interval = 10000, immediate = false) {
  if (pollTimer) {
    window.clearInterval(pollTimer);
  }
  pollTimer = window.setInterval(loadStatus, interval);
  if (immediate) {
    loadStatus();
  }
}

function pwaContext() {
  return {
    standalone: window.matchMedia?.("(display-mode: standalone)")?.matches ?? false,
    hasServiceWorker: "serviceWorker" in navigator,
    secureContext: Boolean(window.isSecureContext),
  };
}

function renderInstallHint() {
  const context = pwaContext();
  if (installFailure) {
    elements.installHint.hidden = false;
    elements.installHintText.textContent = installFailure;
    elements.installButton.hidden = true;
    return;
  }
  const hint = installationHint(context);
  if (!hint) {
    elements.installHint.hidden = true;
    return;
  }
  elements.installHint.hidden = false;
  elements.installHintText.textContent = hint;
  elements.installButton.hidden = !(shouldOfferInstall(context) && installPrompt);
}

function registerPwa() {
  renderInstallHint();
  window.matchMedia?.("(display-mode: standalone)")?.addEventListener?.(
    "change",
    renderInstallHint,
  );
  elements.installButton.addEventListener("click", async () => {
    if (!installPrompt) {
      return;
    }
    try {
      installPrompt.prompt();
      await installPrompt.userChoice;
    } catch {
      // An expired prompt cannot be reused; the browser may offer it again.
    }
    installPrompt = null;
    renderInstallHint();
  });
  if (canRegisterServiceWorker(pwaContext())) {
    navigator.serviceWorker
      .register("/sw.js", {scope: "/", updateViaCache: "none"})
      .catch(() => {
        installFailure = "离线外壳注册失败；在线管理不受影响。";
        renderInstallHint();
      });
  }
}

elements.form.addEventListener("input", () => {
  if (preview) {
    invalidatePreview("内容已修改，请重新预览。");
  }
});
elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  requestPreview();
});
elements.publishButton.addEventListener("click", publishDraft);

loadStatus();
startPolling(10000);
registerPwa();
