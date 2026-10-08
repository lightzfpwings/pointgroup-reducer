/* Application event tests in a minimal DOM double. No browser or UI automation.
 * These verify state/event wiring and JSON actions, not browser rendering. */
'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const E = require('../engine.js');
const A = require('../reducer-adapter.js');
const R = require('../reduction-engine.js'),catalog=require('../reduction-catalog.js');

function harness(bundled = false,languageVariant = '') {
  const downloads = [], blobs = new Map(), timers = [];
  class Element {
    constructor(tag = 'div') { this.tagName = tag.toUpperCase(); this.children = []; this.attributes = {}; this.dataset = {}; this.value = ''; this.checked = false; this.disabled = false; this.className = ''; this._text = ''; this.files = []; }
    set textContent(value) { this._text = String(value); this.children = []; }
    get textContent() { return this._text + this.children.map(c => c.textContent).join(''); }
    append(...nodes) { nodes.forEach(node => { if (typeof node === 'string') { const t = new Element('text'); t.textContent = node; node = t; } node.parent = this; this.children.push(node); if (this.tagName === 'SELECT' && this.children.length === 1) this.value = node.value; }); }
    replaceChildren(...nodes) { this._text = ''; this.children = []; if (this.tagName === 'SELECT') this.value = ''; this.append(...nodes); }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    getAttribute(name) { return this.attributes[name]??null; }
    get [Symbol.toStringTag]() { return this.namespaceURI==='http://www.w3.org/1998/Math/MathML'?(this.tagName==='MATH'?'MathMLMathElement':'MathMLElement'):'HTMLElement'; }
    focus() { this.focused=true; }
    select() { this.selected=true; }
    remove() { if (this.parent) this.parent.children = this.parent.children.filter(c => c !== this); }
    click() { if (this.tagName === 'A') downloads.push({ name: this.download, blob: blobs.get(this.href) }); else if (!this.disabled && this.onclick) return this.onclick(); }
    get classList() { const self = this; return { add(name) { self.className = [...new Set([...self.className.split(/\s+/).filter(Boolean), name])].join(' '); }, remove(name) { self.className = self.className.split(/\s+/).filter(s => s && s !== name).join(' '); }, contains(name) { return self.className.split(/\s+/).includes(name); } }; }
  }
  const elements = new Map(), templates = [],statics=[];
  const html = fs.readFileSync(path.join(__dirname, bundled ? '../dist/BasisCharacterPrototype-' + E.VERSION +(languageVariant?'-'+languageVariant:'')+ '.html' : '../index.html'), 'utf8');
  const attr = (s, name) => (s.match(new RegExp('(?:^|\\s)' + name + '="([^"]*)"')) || [null, ''])[1];
  for (const match of html.matchAll(/<(\w+)\b([^>]*\bid="[^"]+"[^>]*)>/g)) {
    const node = new Element(match[1]), attrs = match[2], id = attr(attrs, 'id'); node.value = attr(attrs, 'value'); node.className = attr(attrs, 'class'); node.checked = /\bchecked\b/.test(attrs); node.disabled = /\bdisabled\b/.test(attrs); elements.set(id, node);
  }
  for (const match of html.matchAll(/<button\b([^>]*data-template="[^"]+"[^>]*)>/g)) { const node = new Element('button'); node.dataset.template = attr(match[1], 'data-template'); templates.push(node); }
  for(const match of html.matchAll(/<(\w+)\b([^>]*data-i18n[^>]*)>/g)){const node=elements.get(attr(match[2],'id'))||new Element(match[1]);for(const attribute of match[2].matchAll(/([\w-]+)="([^"]*)"/g))node.setAttribute(attribute[1],attribute[2].replace(/&amp;/g,'&').replace(/&quot;/g,'"'));statics.push(node);}
  const document = { body: new Element('body'),documentElement:new Element('html'), getElementById: id => { assert(elements.has(id), 'unknown DOM id ' + id); return elements.get(id); }, createElement: tag => new Element(tag),createElementNS:(namespace,tag)=>{const n=new Element(tag);n.namespaceURI=namespace;return n;}, querySelectorAll: selector => {if(selector==='[data-template]')return templates;const attr=selector.slice(1,-1);return statics.filter(n=>n.getAttribute(attr)!==null);} };
  const preferences=new Map();
  const context = { BasisEngine: E, ReducerAdapter: A, ReductionEngine:R, ReductionCatalog:catalog,navigator:{},localStorage:{getItem:k=>preferences.get(k)||null,setItem:(k,v)=>preferences.set(k,v)}, document, Node: Element, Blob, URL: { createObjectURL(blob) { const id = 'blob:' + blobs.size; blobs.set(id, blob); return id; }, revokeObjectURL() {} }, setTimeout: fn => { timers.push(fn); }, console };
  context.window = context;
  const sandbox = vm.createContext(context);
  if (bundled) {
    assert(!/<script\s+src=/.test(html), 'offline build must not reference external scripts');
    const scripts = [...html.matchAll(/<script>\s*([\s\S]*?)<\/script>/g)]; assert.equal(scripts.length, languageVariant?10:9);
    scripts.forEach((match, i) => vm.runInContext(match[1], sandbox, { filename: 'offline-script-' + i }));
  } else for(const name of ['messages-data.js','i18n.js','math-format.js','app.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../'+name),'utf8'),sandbox,{filename:name});
  const $ = id => document.getElementById(id);
  return { $, downloads, elements, document, context,statics,preferences, template: name => templates.find(t => t.dataset.template === name).click(), click: id => $(id).click(), flush: () => { while (timers.length) timers.shift()(); }, set: (id, value, changed = false) => { $(id).value = String(value); if (changed && $(id).onchange) $(id).onchange(); }, descendants: function walk(node) { return node.children.flatMap(c => [c, ...walk(c)]); } };
}

test('initial UI is separate, with editable benzene input and no stale result', () => {
  const h = harness(); assert.equal(h.$('group').value, 'D6h'); assert.equal(h.$('function-count').textContent, '30 个函数'); assert.equal(h.$('site-count').textContent, '12 个中心'); assert.equal(h.$('export-result').disabled, true); assert(h.$('inspector-card').classList.contains('hidden'));
});
test('all four example buttons compute the expected number of blocks', () => {
  const h = harness();
  for (const [name, count, dimension] of [['benzene', 4, 30], ['water', 1, 2], ['central-c2v', 3, 3], ['central-oh', 1, 3]]) {
    h.template(name); h.click('calculate'); h.flush();
    assert(h.$('status').textContent.includes('已生成 ' + count + ' 个封闭空间'));
    assert(h.$('status').textContent.includes('共 ' + dimension + ' 个基函数'));
    assert.equal(h.$('export-result').disabled, false); assert(!h.$('inspector-card').classList.contains('hidden'));
  }
});
test('one representative C position generates six s instances end to end', () => {
  const h = harness(); h.click('new-project'); h.set('seed-count', 6); h.click('expand-seed'); assert.equal(h.$('site-count').textContent, '6 个中心');
  h.click('add-functions'); assert.equal(h.$('function-count').textContent, '6 个函数'); h.click('calculate'); h.flush();
  assert(h.$('result-body').textContent.includes('[6, 0, 0, 0, 2, 0, 0, 0, 0, 6, 0, 2]'));
});
test('expected count mismatch and duplicate function addition do not mutate inputs', () => {
  const h = harness(); h.click('new-project'); h.set('seed-count', 5); h.click('expand-seed'); assert(h.$('status').textContent.includes('实际生成 6 个位置')); assert.equal(h.$('site-count').textContent, '0 个中心');
  h.set('seed-count', 6); h.click('expand-seed'); h.click('add-functions'); h.click('add-functions'); assert(h.$('status').textContent.includes('已有相同径向类型')); assert.equal(h.$('function-count').textContent, '6 个函数');
});
test('px-only UI rejects closure; adding py then completes the same input', () => {
  const h = harness(); h.click('new-project'); h.click('expand-seed'); h.$('orbital-s').checked = false; h.$('orbital-px').checked = true; h.click('add-functions'); h.click('calculate'); h.flush();
  assert(h.$('status').textContent.includes('所选集合之外')); assert.equal(h.$('export-result').disabled, true);
  h.$('orbital-px').checked = false; h.$('orbital-py').checked = true; h.click('add-functions'); h.click('calculate'); h.flush(); assert(h.$('status').textContent.includes('已生成 1 个封闭空间')); assert.equal(h.$('function-count').textContent, '12 个函数');
});
test('coordinate edits invalidate results, fail symmetry, and can be undone', () => {
  const h = harness(); h.click('calculate'); h.flush();
  const input = h.descendants(h.$('sites-table')).find(n => n.attributes['aria-label'] === 'C0 x'); input.value = '1.2'; input.onchange();
  assert.equal(h.$('export-result').disabled, true); assert(h.$('inspector-card').classList.contains('hidden')); h.click('calculate'); h.flush(); assert(h.$('status').textContent.includes('缺少同类型目标位置'));
  h.click('undo'); h.click('calculate'); h.flush(); assert(h.$('status').textContent.includes('已生成 4 个封闭空间'));
});
test('cleared or invalid numeric fields restore the previous value', () => {
  const h = harness(); const input = h.descendants(h.$('sites-table')).find(n => n.attributes['aria-label'] === 'C0 x'); input.value = ''; input.onchange(); assert.equal(input.value, '1');
  h.set('tolerance', 1, true); assert.equal(h.$('tolerance').value, '0.000001'); h.set('tolerance', '', true); assert.equal(h.$('tolerance').value, '0.000001');
});
test('valid position tolerance edits persist in each language and invalid edits restore that value', async () => {
  for(const language of ['zh-Hans','zh-Hant','en']) {
    const h=harness();h.set('language',language,true);h.set('tolerance',2e-6,true);
    h.click('save-project');const saved=JSON.parse(await h.downloads.at(-1).blob.text());
    assert.equal(saved.input.tolerance,2e-6);h.set('tolerance',1,true);assert.equal(h.$('tolerance').value,'0.000002');
    h.click('calculate');h.flush();assert.equal(h.$('export-result').disabled,false);
  }
});
test('project save/import and result export contain real reconstructible data', async () => {
  const h = harness(); h.click('save-project'); const saved = JSON.parse(await h.downloads.at(-1).blob.text()); assert.equal(saved.input.functions.length, 30);
  h.click('new-project'); h.$('project-file').files = [{ size: 1000, text: async () => JSON.stringify(saved) }]; await h.$('project-file').onchange(); assert.equal(h.$('function-count').textContent, '30 个函数'); assert.equal(h.$('export-result').disabled, true);
  h.click('calculate'); h.flush(); h.click('export-result'); const exported = JSON.parse(await h.downloads.at(-1).blob.text()); assert.equal(exported.dimension, 30); assert.equal(exported.conventions.reductionIntegrated, true); assert.equal(exported.reduction.total.valid,true); assert.deepEqual(E.calculate(exported.input).totalCharacters, exported.totalCharacters);
});
test('every class/member and block can be inspected from actual matrices', () => {
  const h = harness(); h.click('calculate'); h.flush(); const classes = E.group('D6h').classes;
  for (let i = 0; i < classes.length; i++) { h.set('inspect-class', i, true); for (const op of classes[i].members) { h.set('inspect-operation', op, true); assert(h.$('operation-matrix').textContent.includes('[')); assert(h.$('fixed-sites').textContent.includes('trace =')); } }
  h.set('inspect-block', 'block-2', true); assert(h.$('transform-table').textContent.includes('2px')); assert(h.$('transform-table').textContent.includes('2py'));
});
test('imported function IDs cannot collide with subsequently added functions', async () => {
  const h = harness(), input = E.template('central-c2v'); input.functions = [{ ...input.functions[0], id: 'f-1-X0' }];
  h.$('project-file').files = [{ size: 1000, text: async () => JSON.stringify({ schemaVersion: 1, input }) }]; await h.$('project-file').onchange();
  h.$('orbital-s').checked = false; h.$('orbital-py').checked = true; h.set('radial-prefix', ''); h.click('add-functions'); assert(h.$('status').textContent.includes('请填写径向'));
  h.set('radial-prefix', ''); // Imported radial is 'p', so use a distinct valid radial for another copy.
  h.set('radial-prefix', '3'); h.click('add-functions'); h.click('save-project'); const saved = JSON.parse(await h.downloads.at(-1).blob.text()); assert.equal(new Set(saved.input.functions.map(f => f.id)).size, saved.input.functions.length);
});
test('complete p shortcut produces three functions per center, without an extra s', () => {
  const h = harness(); h.click('new-project'); h.click('expand-seed'); h.click('select-p'); h.click('add-functions'); assert.equal(h.$('function-count').textContent, '18 个函数'); h.click('calculate'); h.flush(); assert(h.$('status').textContent.includes('共 18 个基函数'));
});
test('built single offline file executes its embedded engine and application', () => {
  const h = harness(true); h.click('calculate'); h.flush(); assert(h.$('status').textContent.includes('已生成 4 个封闭空间')); assert(h.$('result-body').textContent.includes('[30, 0, 0, 0, 2, 0, 0, 0, 0, 18, 0, 6]'));
});
test('native packaging sends save/export JSON to the desktop bridge', () => {
  const h = harness(), messages = [];
  h.context.webkit = { messageHandlers: { saveJSON: { postMessage: payload => messages.push(payload) } } };
  h.click('save-project'); assert.equal(messages.length, 1); assert.equal(h.downloads.length, 0);
  const input = JSON.parse(messages[0].text); assert.equal(input.input.functions.length, 30); assert(messages[0].name.endsWith('.json'));
  h.click('calculate'); h.flush(); h.click('export-result'); const output = JSON.parse(messages[1].text);
  assert.equal(output.dimension, 30); assert.deepEqual(E.calculate(output.input).totalCharacters, output.totalCharacters); assert.equal(h.downloads.length, 0);
});
test('native open bridge reloads selected JSON through the same input validation', () => {
  const h = harness(), messages = [];
  h.context.webkit = { messageHandlers: { openJSON: { postMessage: payload => messages.push(payload) } } };
  h.click('new-project'); h.click('load-project'); assert.equal(messages.length, 1);
  h.context.BasisDesktop.importJSON(JSON.stringify({ schemaVersion: 1, input: E.template('water') }));
  assert.equal(h.$('function-count').textContent, '2 个函数'); assert.equal(h.$('export-result').disabled, true);
  h.click('calculate'); h.flush(); assert(h.$('result-body').textContent.includes('[2, 0, 2, 0]'));
  h.context.BasisDesktop.importJSON('not JSON'); assert(h.$('status').className.includes('error')); assert.equal(h.$('function-count').textContent, '2 个函数');
});
test('complete d UI, local frame and saved inputs reconstruct actual d representations',async()=>{
  const h=harness();h.template('central-d-oh');h.click('clear-functions');h.click('select-d');h.set('radial-prefix','3');
  h.set('d-x-x',0);h.set('d-x-y',1);h.click('add-functions');assert.equal(h.$('function-count').textContent,'5 个函数');
  h.click('calculate');h.flush();assert(h.$('status').textContent.includes('共 5 个基函数'));
  h.click('save-project');const saved=JSON.parse(await h.downloads.at(-1).blob.text());
  assert(saved.input.functions.every(f=>f.family==='d'&&f.frame));
  h.click('new-project');h.context.BasisDesktop.importJSON(JSON.stringify(saved));h.click('calculate');h.flush();
  assert(h.$('status').textContent.includes('共 5 个基函数'));
});
test('invalid d local axes/imported frames leave the previous inputs intact',()=>{
  const h=harness();h.template('central-d-oh');h.click('clear-functions');h.click('select-d');
  h.set('d-z-x',1);h.click('add-functions');assert(h.$('status').textContent.includes('互相垂直'));assert.equal(h.$('function-count').textContent,'0 个函数');
  h.template('central-d-oh');const input=E.template('central-d-oh');input.functions[0].frame=[[2,0,0],[0,1,0],[0,0,1]];
  h.context.BasisDesktop.importJSON(JSON.stringify({schemaVersion:1,input}));assert(h.$('status').textContent.includes('单位正交'));assert.equal(h.$('function-count').textContent,'5 个函数');
});
test('aligned export and selectable block vector use original class order without rounding',async()=>{
  const h=harness();h.template('central-d-oh');h.set('group','C7',true);h.click('calculate');h.flush();
  const input=E.template('central-d-oh');input.group='C7';const aligned=A.align(E.calculate(input));
  assert.deepEqual(h.$('alignment-text').value.split(', ').map(Number),aligned.c);
  h.click('export-aligned');const saved=JSON.parse(await h.downloads.at(-1).blob.text());assert.deepEqual(saved.c,aligned.c);assert.equal(saved.characters_weighted,false);
  h.set('alignment-vector',aligned.blocks[0].id,true);assert.deepEqual(h.$('alignment-text').value.split(', ').map(Number),aligned.blocks[0].c);
  h.click('clear-functions');assert(h.$('alignment-card').classList.contains('hidden'));assert.equal(h.$('export-aligned').disabled,true);
});
test('three languages preserve geometry, results, inspector selections and saved data',async()=>{
  const h=harness();h.template('central-d-oh');h.click('calculate');h.flush();h.set('inspect-block','block-2',true);h.set('alignment-vector','block-2',true);
  h.click('export-result');const original=JSON.parse(await h.downloads.at(-1).blob.text());
  for(const language of ['en','zh-Hant','zh-Hans']){
    h.set('language',language,true);assert.equal(h.context.I18n.language(),language);assert.equal(h.preferences.get('symmetry-language'),language);assert.equal(h.$('inspect-block').value,'block-2');assert.equal(h.$('alignment-vector').value,'block-2');assert.equal(h.$('function-count').textContent,language==='en'?'5 functions':language==='zh-Hant'?'5 個函數':'5 个函数');
    h.click('export-result');const exported=JSON.parse(await h.downloads.at(-1).blob.text());assert.deepEqual(exported.input,original.input);assert.deepEqual(exported.reduction.total,original.reduction.total);
    if(language==='en'){for(const id of ['group-note','project-note','status','result-body','fixed-sites'])assert(!/[\u4e00-\u9fff]/.test(h.$(id).textContent),id);}
  }
});
test('English and Traditional Chinese errors are localized and still expose the failing operation',()=>{
  const h=harness();h.click('new-project');h.click('expand-seed');h.$('orbital-s').checked=false;h.$('orbital-px').checked=true;h.click('add-functions');
  for(const language of ['en','zh-Hant']){h.set('language',language,true);h.click('calculate');h.flush();assert.equal(h.$('export-result').disabled,true);assert(h.$('status').textContent.includes(language==='en'?'Basis is not closed':'基函數不封閉'));if(language==='en')assert(!/[\u4e00-\u9fff]/.test(h.$('status').textContent));}
  h.set('language','en',true);assert(!/[\u4e00-\u9fff]/.test(h.$('status').textContent));assert(h.$('status').textContent.includes('"operation"'));assert(h.$('status').textContent.includes('Failed operation and object'));
});
test('manual mode keeps all 423 point groups and reduces high-order complex tables',()=>{
  const h=harness();h.set('workflow','manual',true);assert.equal(h.$('manual-group').children.length,423);assert(h.$('positions-section').classList.contains('hidden'));
  h.set('manual-group','C60',true);h.click('manual-d');assert.equal(h.$('manual-characters').value.split(', ').length,60);h.click('calculate');h.flush();assert(h.$('status').textContent.includes('不可约分解已完成'));assert.equal(h.$('export-result').disabled,false);
});
test('manual JSON save/open and language switches preserve the literal input expressions',async()=>{
  const h=harness();h.set('workflow','manual',true);h.set('manual-group','C3',true);h.set('manual-characters','1, exp(2*pi*i/3), exp(4*pi*i/3)');h.$('manual-characters').oninput();
  h.click('save-project');const saved=JSON.parse(await h.downloads.at(-1).blob.text());assert.equal(saved.input.mode,'manual');h.click('new-project');h.context.BasisDesktop.importJSON(JSON.stringify(saved));h.set('language','en',true);assert.equal(h.$('manual-characters').value,saved.input.text);
  h.click('calculate');h.flush();h.click('export-result');const result=JSON.parse(await h.downloads.at(-1).blob.text());assert.equal(result.reduction.total.valid,true);assert.deepEqual(result.reduction.total.terms,[{irrep:'E1+',multiplicity:1,dimension:1}]);assert.equal(result.input.text,saved.input.text);
});
test('manual invalid vector has no successful decomposition and malformed expressions are rejected',async()=>{
  const h=harness();h.set('workflow','manual',true);h.set('manual-group','C2v',true);h.set('manual-characters','1, 0, 0, 0');h.$('manual-characters').oninput();h.click('calculate');h.flush();assert(h.$('status').textContent.includes('未通过合法'));h.click('export-result');const r=JSON.parse(await h.downloads.at(-1).blob.text());assert.equal(r.status,'invalid');assert.equal(r.reduction.total.integer_a,null);assert.deepEqual(r.reduction.total.terms,[]);
  h.set('manual-characters','process.exit()');h.$('manual-characters').oninput();h.click('calculate');h.flush();assert.equal(h.$('export-result').disabled,true);assert(h.$('status').textContent.includes('无效的数值表达式'));
});
test('MathML and clipboard outputs are shared by manual and basis workflows',()=>{
  const h=harness(),copies=[];h.context.webkit={messageHandlers:{copyText:{postMessage:message=>copies.push(message.text)}}};h.template('central-d-oh');h.click('calculate');h.flush();
  const nodes=h.descendants(h.$('result-body'));assert(nodes.some(n=>n.tagName==='MATH'));assert(nodes.some(n=>n.tagName==='MSUB'));assert(nodes.some(n=>n.tagName==='MFRAC'));
  h.click('copy-text');assert(copies.at(-1).includes('Γ = Eg + T2g'));assert(copies.at(-1).includes('a = ['));h.click('copy-latex');assert(copies.at(-1).includes('E_{\\mathrm{g}}'));assert(copies.at(-1).includes('\\dim\\Gamma'));assert(copies.at(-1).includes('\\mathbf X^{*}\\mathbf W'));
  const before=h.$('copy-content').value;h.set('language','en',true);assert(h.$('copy-content').value.includes('Total'));assert(before!==h.$('copy-content').value);
});
test('changing input while a calculation is pending prevents stale results from appearing',()=>{
  const h=harness();h.click('calculate');h.click('clear-functions');h.flush();assert.equal(h.$('export-result').disabled,true);assert(h.$('copy-card').classList.contains('hidden'));assert.equal(h.$('calculate').disabled,false);
});
test('all three standalone language versions execute with their intended initial language',()=>{
  for(const language of ['zh-Hans','zh-Hant','en']){const h=harness(true,language);assert.equal(h.context.I18n.language(),language);h.template('central-d-oh');h.click('calculate');h.flush();assert.equal(h.$('export-result').disabled,false);assert(h.$('copy-content').value.includes('Γ = Eg + T2g'));}
});
test('every static translation key and accessibility label has explicit three-language text',()=>{
  const h=harness();for(const node of h.statics)for(const attribute of ['data-i18n','data-i18n-title','data-i18n-placeholder','data-i18n-aria-label']){const key=node.getAttribute(attribute);if(key)assert(h.context.I18n.messages[key],key);}
  h.set('language','en',true);for(const node of h.statics)if(node.getAttribute('data-i18n'))assert(!/[\u4e00-\u9fff]/.test(node.textContent));assert.equal(h.document.documentElement.lang,'en');
});
test('mathematical table headers remain MathML nodes in basis, manual and vector tables in all languages',()=>{
  const h=harness();
  const check=(container,start,count)=>{
    const heads=h.descendants(container).filter(n=>n.tagName==='TH').slice(start,start+count);
    assert.equal(heads.length,count);
    heads.forEach(th=>{assert.equal(th.children.length,1);assert.equal(th.children[0].tagName,'MATH');assert.equal(th.children[0].namespaceURI,'http://www.w3.org/1998/Math/MathML');assert(!th.textContent.includes('[object'));});
    assert(!container.textContent.includes('[object MathMLMathElement]'));
  };
  for(const language of ['zh-Hans','zh-Hant','en']){
    h.set('language',language,true);h.template('benzene');h.click('calculate');h.flush();
    check(h.$('character-table'),1,12);check(h.$('result-body'),2,12);check(h.$('alignment-table'),1,12);
    if(language==='en'){const heads=h.descendants(h.$('result-body')).filter(n=>n.tagName==='TH');assert.equal(heads[0].textContent,'Basis block');assert.equal(heads[1].textContent,'Dimension');}
    h.set('workflow','manual',true);h.set('manual-group','Oh',true);h.click('manual-d');h.click('calculate');h.flush();
    check(h.$('character-table'),1,10);check(h.$('result-body'),1,10);
  }
});
