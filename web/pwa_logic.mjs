export function canRegisterServiceWorker({hasServiceWorker, secureContext}) {
  return Boolean(hasServiceWorker && secureContext);
}

export function shouldOfferInstall({standalone, hasServiceWorker, secureContext}) {
  return Boolean(!standalone && hasServiceWorker && secureContext);
}

export function installationHint({standalone, hasServiceWorker, secureContext}) {
  if (standalone) {
    return null;
  }
  if (!secureContext) {
    return "当前 HTTP 连接不支持安装或离线；可先收藏本页。";
  }
  if (!hasServiceWorker) {
    return "当前浏览器不支持安装；可先收藏本页。";
  }
  return "浏览器菜单 → 安装应用 / 添加到主屏幕。";
}
