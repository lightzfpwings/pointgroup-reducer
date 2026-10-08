'use strict';
const {test}=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const script=fs.readFileSync(require('node:path').join(__dirname,'../packaging/windows/bridge.js'),'utf8');
function harness(url='https://basischaracter.local/index.html',top=true){
  const messages=[],window={location:{href:url},chrome:{webview:{postMessage:m=>messages.push(m)}}};
  window.top=top?window:{}; vm.runInNewContext(script,{window}); return {window,messages};
}
test('Windows forwards existing JSON, clipboard and language contracts without string coercion',()=>{
  const h=harness(),payloads={saveJSON:{name:'basis.json',text:'{"orbital":"dxy"}'},openJSON:{},copyText:{text:'χ(E) = 5'},languageChanged:{language:'zh-Hant'}};
  for(const [type,payload] of Object.entries(payloads))h.window.webkit.messageHandlers[type].postMessage(payload);
  assert.deepEqual(h.messages.map(m=>JSON.parse(JSON.stringify(m))),Object.entries(payloads).map(([type,payload])=>({type,payload})));
  assert.ok(Object.isFrozen(h.window.webkit.messageHandlers));
});
test('Windows native capabilities are absent in frames and all non-app documents',()=>{
  for(const url of ['https://example.org/','https://basischaracter.local/other.html','file:///index.html','https://basischaracter.local/index.html#frame'])assert.equal(harness(url).window.webkit,undefined);
  assert.equal(harness(undefined,false).window.webkit,undefined);
});
