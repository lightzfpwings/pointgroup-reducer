'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createHash,webcrypto} = require('node:crypto');
const fs = require('node:fs'), vm = require('node:vm');
const U = require('../updates.js');
const repo = 'https://github.com/lightzfpwings/pointgroup-reducer/releases/download/';
function release(version, extra={}) {
  const tag = 'basis-v'+version, name = 'BasisCharacterPrototype-'+version+'-en.html', bytes = Buffer.from('verified replacement');
  return {tag_name:tag,draft:false,prerelease:false,assets:[{id:19,name,state:'uploaded',size:bytes.length,
    digest:'sha256:'+createHash('sha256').update(bytes).digest('hex'),browser_download_url:repo+tag+'/'+name}],...extra};
}
test('stable integrated releases are compared numerically across pages, independent of the Python release line',async()=>{
  const other = release('9.9.9',{tag_name:'v9.9.9'});
  const chosen=await U.newest(async p=>p===1 ? [other,release('0.9.0'),release('9.9.9',{draft:true}),release('0.9.1',{prerelease:true}),
    release('1.0.0-rc1'),...Array(5).fill(other)] : [release('0.12.1'),release('0.10.0')]);
  assert.equal(chosen.tag_name,'basis-v0.12.1');
  assert.equal(await U.newest(async()=>[other]),null);
  assert(U.compare('0.10.0','0.9.9')>0); assert.equal(U.compare('1.1.0','1.1.0'),0);
  for (const v of ['0.7','01.7.0','0.7.0-rc1','v0.7.1']) assert.throws(()=>U.compare(v,'0.7.0'));
});
test('an update requires the exact platform and tag, published asset, digest and official URL',()=>{
  for(const [p,suffix] of Object.entries({android:'Android.apk',windows:'Windows-x64.zip',macos:'macOS-arm64.dmg',linux:'Linux-all.deb'})){
    const r=release('0.8.0'),a=r.assets[0];a.name='BasisCharacter-0.8.0-'+suffix;a.browser_download_url=repo+r.tag_name+'/'+a.name;
    assert.equal(U.descriptor(r,p,'en').name,a.name);
    for(const patch of [{state:'starter'},{digest:null},{id:0},{size:0},{browser_download_url:'https://example.org/pkg'}])
      assert.throws(()=>U.descriptor({...r,assets:[{...a,...patch}]},p,'en'));
  }
  assert.throws(()=>U.descriptor(release('0.8.0'),'html','zh-Hans'));
});
function ui(framework={}) {
  const nodes={}, page=(id)=>nodes[id]??=( {textContent:'',click(){return this.onclick?.();}} );
  const ctx={crypto:webcrypto, setTimeout,clearTimeout, AbortController, Blob, location:{href:'file:///tmp/app.html'}, ...framework};
  vm.runInNewContext(fs.readFileSync(require.resolve('../updates.js'),'utf8'),ctx);
  ctx.BasisUpdates.bind({getElementById:page,createElement:()=>({click(){}})}, {translate:s=>s,language:()=>'en',onChange(){}}, '0.7.0');
  return {ctx,page};
}
test('the browser contacts GitHub only on click, rejects corrupt bytes, then replaces the chosen older HTML',async()=>{
  const files=[];let reads=0, saved='';
  const {page}=ui({fetch:async()=>{reads++;return {ok:true,status:200,json:async()=>[release('0.8.0')]};},
    showOpenFilePicker:async()=>[files.shift()]});
  assert.equal(reads,0); await page('check-update').click(); assert.equal(reads,1);
  assert.match(page('update-status').textContent,/0\.8\.0/);
  const source=s=>({getFile:async()=>new Blob([s])});
  files.push(source('bad')); await page('install-update').click(); assert.match(page('update-status').textContent,/校验失败/);
  files.push(source('verified replacement')); await page('install-update').click();
  assert.match(page('install-update').textContent,/原文件/);
  files.push(source('<!doctype html><title>unrelated</title>')); await page('install-update').click(); assert.equal(saved,'');
  files.push({...source('<meta name="basis-app-version" content="0.7.0">'),createWritable:async()=>({write:async b=>{saved=Buffer.from(b).toString()},close:async()=>{}})});
  await page('install-update').click(); assert.equal(saved,'verified replacement'); assert.match(page('update-status').textContent,/已替换/);
});
test('offline and GitHub rate limits clear stale install actions and can be retried',async()=>{
  let mode='offline';const {page}=ui({fetch:async()=>{
    if(mode==='offline')throw Error('offline');
    if(mode==='limited')return {ok:false,status:403};
    return {ok:true,status:200,json:async()=>[release('0.6.0')]};
  }});
  await page('check-update').click(); assert.match(page('update-status').textContent,/网络/);
  mode='limited';await page('check-update').click();assert.match(page('update-status').textContent,/次数/);
  mode='ok';await page('check-update').click();assert.match(page('update-status').textContent,/最新版本/);
  assert.equal(page('install-update').hidden,true);
});
