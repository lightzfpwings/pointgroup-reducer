// 复用已有桌面协议；仅在应用主页的顶层文档中提供四个有限操作。
(function () {
  'use strict';
  if (window.top !== window || window.location.href !== 'https://basischaracter.local/index.html' || !window.chrome?.webview) return;
  const handlers = {};
  for (const type of ['saveJSON', 'openJSON', 'copyText', 'languageChanged','update']) {
    handlers[type] = Object.freeze({ postMessage(payload) { window.chrome.webview.postMessage({ type, payload }); } });
  }
  window.BasisUpdatePlatform = "windows";
  window.webkit = Object.freeze({ messageHandlers: Object.freeze(handlers) });
})();
