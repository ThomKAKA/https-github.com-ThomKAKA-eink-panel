export function formatBytes(size) {
  if (!Number.isFinite(size) || size <= 0) {
    return "--";
  }
  return `${Math.ceil(size / 1024)} KiB`;
}

export function shortSha(value) {
  if (typeof value !== "string" || value.length === 0) {
    return "—";
  }
  return `${value.slice(0, 12)}…`;
}

// The arm is one-shot and expires; the state label must say until when so an
// operator never assumes a stale offer is still actionable.
function armedUntil(expiresAt) {
  if (typeof expiresAt !== "string" || expiresAt.length === 0) {
    return "";
  }
  const when = new Date(expiresAt);
  if (Number.isNaN(when.getTime())) {
    return "";
  }
  const time = when.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  return `（有效至 ${time}）`;
}

export function firmwareView(status) {
  if (!status) {
    return {state: "unknown", label: "固件状态未知", canArm: false, canDisarm: false};
  }
  if (!status.configured) {
    return {state: "unconfigured", label: "Host 未配置固件", canArm: false, canDisarm: false};
  }
  if (status.armed) {
    return {
      state: "armed",
      label: `已武装 ${status.version}，等待设备取件${armedUntil(status.expires_at)}`,
      canArm: false,
      canDisarm: true,
    };
  }
  // A device that reports the target version is already current, even though
  // served_at stays set from the transfer that delivered it. Checking this
  // first keeps the card from showing "waiting for the version report" forever
  // and from offering the same upgrade again (design 4.5).
  if (status.device_version && status.device_version === status.version) {
    return {state: "current", label: "设备已是目标版本", canArm: false, canDisarm: false};
  }
  if (status.served_at) {
    return {
      state: "served",
      label: "已发送固件，等待设备版本上报",
      canArm: true,
      canDisarm: false,
    };
  }
  return {state: "ready", label: "可以准备升级", canArm: true, canDisarm: false};
}

export function confirmationText(status) {
  return `将允许设备下载并安装 ${status.version}，设备会重启。确认继续？`;
}
