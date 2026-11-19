// The native side transfers this port only to the bundled top-level HTTPS origin.
(function () {
  if (window !== window.top || location.href !== 'https://appassets.androidplatform.net/index.html') return;
  function connect(event) {
    if (event.data !== 'basis-port' || event.ports.length !== 1) return;
    window.removeEventListener('message', connect);
    const port = event.ports[0], handlers = {};
    for (const type of ['openJSON', 'saveJSON', 'copyText']) {
      handlers[type] = {postMessage: payload => port.postMessage(JSON.stringify({type, payload}))};
    }
    port.onmessage = message => window.BasisDesktop.importJSON(message.data);
    window.webkit = {messageHandlers: handlers};
    port.postMessage(JSON.stringify({type: 'ready'}));
  }
  window.addEventListener('message', connect);
})();
