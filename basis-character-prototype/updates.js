// The bundled UI requests release metadata only after a click. Native installers
// independently resolve the selected tag and verify the package before replacing it.
(function (root) {
  'use strict';
  const repo = 'lightzfpwings/pointgroup-reducer';
  const api = 'https://api.github.com/repos/' + repo + '/releases';
  const web = 'https://github.com/' + repo + '/releases/download/';
  const pageSize = 10;
  const versionPattern = /^(0|[1-9]\d{0,5})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})$/;
  const suffixes = {android:'Android.apk', windows:'Windows-x64.zip', macos:'macOS-arm64.dmg', linux:'Linux-all.deb'};
  function compare(a,b) {
    if (!versionPattern.test(a) || !versionPattern.test(b)) throw new Error('metadata');
    const right = b.split('.').map(Number);
    for (const [i,value] of a.split('.').entries()) if (+value !== right[i]) return +value - right[i];
    return 0;
  }
  function releaseVersion(r) {
    if (!r || r.draft !== false || r.prerelease !== false || !r.tag_name?.startsWith('basis-v')) return null;
    const version = r.tag_name.slice(7);
    return versionPattern.test(version) ? version : null;
  }
  async function newest(read) {
    let best = null;
    for (let page = 1; ; page++) {
      const rows = await read(page);
      if (!Array.isArray(rows) || rows.length > pageSize) throw new Error('metadata');
      for (const r of rows) if (releaseVersion(r) && (!best || compare(releaseVersion(r),releaseVersion(best)) > 0)) best = r;
      if (rows.length < pageSize) return best;
    }
  }
  function descriptor(release, platform, language) {
    const version = releaseVersion(release);
    if (!version) throw new Error('metadata');
    const name = platform === 'html' ? 'BasisCharacterPrototype-' + version + '-' + language + '.html'
      : 'BasisCharacter-' + version + '-' + suffixes[platform];
    const url = web + release.tag_name + '/' + name;
    const asset = release.assets?.find(a => a.name === name && a.state === 'uploaded');
    if (!asset || asset.browser_download_url !== url || !Number.isSafeInteger(asset.id) || asset.id <= 0 ||
        !Number.isSafeInteger(asset.size) || asset.size <= 0 || !/^sha256:[a-f0-9]{64}$/.test(asset.digest)) throw new Error('asset');
    return {version,name,url,id:asset.id,bytes:asset.size,sha256:asset.digest.slice(7)};
  }
  const pending = new Map();
  let sequence = 0;
  function receive(id, status, data) {
    const call = pending.get(id);
    if (!call) return;
    pending.delete(id);
    root.clearTimeout(call.timer);
    if (status === 'ok') call.resolve(data);
    else call.reject(new Error(status));
  }
  function native(action, fields) {
    return new Promise((resolve,reject) => {
      const id = ++sequence;
      const timer = root.setTimeout(() => receive(id,'timeout'), action === 'page' ? 35000 : 30*60*1000);
      pending.set(id,{resolve,reject,timer});
      try { root.webkit.messageHandlers.update.postMessage({id,action,...fields}); }
      catch (_) { receive(id,'network'); }
    });
  }
  async function browserFetch(url, accept, timeout, consume) {
    const controller = new AbortController(), timer = root.setTimeout(() => controller.abort(), timeout);
    try {
      const res = await root.fetch(url,{headers:{Accept:accept},credentials:'omit',cache:'no-store',signal:controller.signal});
      if (res.status === 403 || res.status === 429) throw new Error('rate');
      if (res.status === 404) throw new Error('missing');
      if (!res.ok) throw new Error('network');
      return await consume(res);
    } finally { root.clearTimeout(timer); }
  }
  async function readPage(page, packaged) {
    if (packaged) {
      const result = await native('page',{page});
      return JSON.parse(result);
    }
    return browserFetch(api + '?per_page=' + pageSize + '&page=' + page,
      'application/vnd.github+json', 25000, res => res.json());
  }
  function pickHTML() {
    return root.showOpenFilePicker({multiple:false,types:[{description:'HTML',accept:{'text/html':['.html','.htm']}}]});
  }
  async function verifiedHTML(asset) {
    const [handle] = await pickHTML(), file = await handle.getFile();
    if (file.size !== asset.bytes || file.size > 20*1024*1024) throw new Error('integrity');
    const bytes = await file.arrayBuffer();
    const hash = await root.crypto.subtle.digest('SHA-256',bytes);
    const digest = Array.from(new Uint8Array(hash),v=>v.toString(16).padStart(2,'0')).join('');
    if (digest !== asset.sha256) throw new Error('integrity');
    return bytes;
  }
  async function replaceHTML(asset, bytes) {
    const [handle] = await pickHTML(), original = await handle.getFile();
    if (original.size > 20*1024*1024) throw new Error('file');
    const marker = (await original.slice(0,4096).text()).match(/<meta name="basis-app-version" content="([0-9.]+)">/);
    if (!marker || compare(asset.version,marker[1]) <= 0) throw new Error('file');
    const file = await handle.createWritable();
    try { await file.write(bytes); await file.close(); }
    catch (e) { try { await file.abort(); } catch (_) {} throw e; }
  }
  const errors = {
    rate:'GitHub 暂时限制了查询次数，请稍后重试。', asset:'该正式版缺少可验证的本平台安装包。',
    integrity:'安装包校验失败，请重新检查更新。', file:'请选择本软件较旧的离线 HTML 文件。',
    permission:'需要系统允许安装更新，请授权后重试。', cancelled:'已取消更新。',
    location:'请将应用放在可写的应用目录，再检查更新。', busy:'已有更新正在进行。',
    install:'系统未能安装更新，请重试。', timeout:'请求超时，请重试。'
  };
  function bind(doc, I, current) {
    const get = id => doc.getElementById(id), check = get('check-update'), install = get('install-update');
    const link = get('download-update'), status = get('update-status');
    let asset, platform, verifiedFile, phase = '', message = '', busy = false;
    function render() {
      check.disabled = busy;
      install.hidden = !asset || phase === 'done' || (platform === 'html' && !root.showOpenFilePicker);
      install.disabled = busy;
      install.textContent = I.translate(platform === 'html' ? (verifiedFile ? '选择原文件并替换' : '校验下载的 HTML') : '安装更新');
      link.hidden = !asset || platform !== 'html' || phase === 'done' || !!verifiedFile;
      if (!link.hidden) link.href = asset.url;
      status.textContent = I.translate(message).replace('{version}',asset?.version || current);
    }
    function state(text, step, working) { message=text; phase=step; busy=working; render(); }
    check.onclick = async () => {
      if (busy) return;
      asset = null; verifiedFile = null;
      const location = root.location?.href?.split(/[?#]/)[0];
      platform = root.BasisUpdatePlatform || (location === 'https://appassets.androidplatform.net/index.html' ? 'android'
        : location === 'https://basischaracter.local/index.html' ? 'windows'
        : location === 'file:///usr/share/basis-character/index.html' ? 'linux' : 'html');
      state('正在检查 GitHub 正式版…','checking',true);
      try {
        const release = await newest(page=>readPage(page, platform !== 'html' && platform !== 'linux'));
        if (!release) { state('GitHub 暂无本软件的正式版。','current',false); return; }
        if (compare(releaseVersion(release),current) <= 0) { state('已是最新版本（{version}）。','current',false); return; }
        asset = descriptor(release,platform,root.BasisDefaultLanguage || I.language());
        state(platform === 'html' ? '发现 {version}。请先下载新版 HTML，再替换原文件。' : '发现 {version}。安装前请保存当前项目。','available',false);
      } catch (e) { state(errors[e.message] || '无法连接 GitHub，请检查网络后重试。','error',false); }
    };
    install.onclick = async () => {
      if (busy || !asset || phase === 'done') return;
      state(platform==='linux' ? '正在准备更新…' : '正在下载并校验安装包…','installing',true);
      try {
        if (platform === 'linux') {
          const a = doc.createElement('a'); a.href = 'basis-character-update://install/'+asset.version+'?lang='+I.language(); a.click();
          state('请在系统窗口完成更新。安装后重新打开应用。','system',false);
        } else if (platform === 'html') {
          if (verifiedFile) {
            await replaceHTML(asset,verifiedFile); verifiedFile=null;
            state('已替换 HTML 文件。请重新打开该文件。','done',false);
          } else {
            verifiedFile = await verifiedHTML(asset);
            state('新版文件已校验。请选择要覆盖的原 HTML 文件。','available',false);
          }
        } else {
          await native('install',{version:asset.version});
          state('请在系统窗口完成更新。安装后重新打开应用。','system',false);
        }
      } catch (e) { state(e.name==='AbortError' ? errors.cancelled : errors[e.message] || '更新失败，请重试或从 GitHub 下载。','error',false); }
    };
    I.onChange(render); render();
  }
  const exports = {bind,receive,compare,newest,descriptor};
  if (typeof module !== 'undefined' && module.exports) module.exports = exports;
  root.BasisUpdates = exports;
})(typeof globalThis !== 'undefined' ? globalThis : this);
