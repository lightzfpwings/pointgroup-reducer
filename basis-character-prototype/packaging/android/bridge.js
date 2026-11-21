// The native side transfers this port only to the bundled top-level HTTPS origin.
(function () {
  if (window !== window.top || location.href !== 'https://appassets.androidplatform.net/index.html') return;
  function connect(event) {
    if (event.data !== 'basis-port' || event.ports.length !== 1) return;
    window.removeEventListener('message', connect);
    const port = event.ports[0], handlers = {};
    for (const type of ['openJSON', 'saveJSON', 'copyText','update']) {
      handlers[type] = {postMessage: payload => port.postMessage(JSON.stringify({type, payload}))};
    }
    let pendingXYZ, receiveXYZ;
    window.BasisAndroid = {readXYZ() {
      if (!pendingXYZ) {
        pendingXYZ = new Promise((resolve, reject) => {
          receiveXYZ = document => {
            if (document.error) reject(new Error(document.error === 'size' ? '输入文件不能超过 2 MiB。' : '无法读取所选文件。'));
            else resolve(document.text ?? null);
          };
        });
        port.postMessage(JSON.stringify({type: 'openXYZ'}));
      }
      return pendingXYZ;
    }};
    port.onmessage = message => {
      const document = JSON.parse(message.data);
      if (document.type === 'project') window.BasisDesktop.importJSON(document.text);
      if (document.type !== 'xyz' || !pendingXYZ) return;
      receiveXYZ(document);
      pendingXYZ = null;
      receiveXYZ = null;
    };
    window.BasisUpdatePlatform = "android";
    window.webkit = {messageHandlers: handlers};
    port.postMessage(JSON.stringify({type: 'ready'}));
  }
  window.addEventListener('message', connect);
})();
