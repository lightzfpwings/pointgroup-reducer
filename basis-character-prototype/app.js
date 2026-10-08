(function () {
  'use strict';
  const E = window.BasisEngine, R = window.ReductionEngine, I = window.I18n, M = window.MathFormat, t = I.translate, $ = id => document.getElementById(id);
  let spec = { schemaVersion: 1, group: 'D6h', tolerance: 1e-6, sites: [], functions: [], note: '' }, result = null, selection = new Set(), history = [], serial = 0;
  let mode = 'basis', manual = {group:'D6h',text:'',tolerance:1e-7}, reduction = null, revision = 0, lastMessage = '', lastKind = '', lastDetail = null;
  const clone = x => JSON.parse(JSON.stringify(x));
  const fmt = x => Math.abs(x) < 1e-10 ? '0' : Math.abs(x - Math.round(x)) < 1e-10 ? String(Math.round(x)) : Number(x.toPrecision(7)).toString();
  // 表头与正文共用内容插入：MathML/HTML 节点直接插入，文本才设置 textContent。
  function el(tag, text, className) { const node = document.createElement(tag); if (text instanceof Node) node.append(text); else if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; }
  function option(select, value, label) { const o = el('option', label); o.value = value; select.append(o); }
  function status(message, kind = '', detail = null) {
    lastMessage=I.canonical(message);lastKind=kind;lastDetail=detail;$('status').textContent = t(lastMessage); $('status').className = 'notice status ' + kind;
    if(detail&&Object.keys(detail).length){const details=el('details');details.append(el('summary',t('查看失败操作与对象')),el('pre',JSON.stringify(detail,null,2),'vector'));$('status').append(details);}
  }
  function numberInput(id, label) { const v = $(id).value.trim(), n = Number(v); if (!v || !Number.isFinite(n)) throw new Error(label + t('需要填写有限数值。')); return n; }
  function checkpoint() { history.push({ spec: clone(spec), selection: [...selection], mode, manual:clone(manual) }); if (history.length > 30) history.shift(); $('undo').disabled = false; }
  function invalidate(message) {
    revision++; result = null; reduction = null; $('export-result').disabled = true; $('export-aligned').disabled = true; $('inspector-card').classList.add('hidden'); $('alignment-card').classList.add('hidden'); $('copy-card').classList.add('hidden'); $('copy-content').value='';
    $('result-body').className = 'empty'; $('result-body').textContent = t('输入已更新，请重新计算。');
    if (message) status(message); else status('');
  }
  function protect(action) { return () => { try { action(); } catch (error) { status(I.error(error), 'error', error.detail); } }; }
  function makeTable(container, headers, rows) {
    container.replaceChildren(); const table = el('table'), thead = el('thead'), tr = el('tr'); headers.forEach(h => tr.append(el('th', h))); thead.append(tr); table.append(thead); const tbody = el('tbody');
    rows.forEach(cells => { const row = el('tr'); cells.forEach(c => row.append(el('td', c))); tbody.append(row); }); table.append(tbody); container.append(table); return table;
  }
  function removeButton(action) { const b = el('button', t('移除'), 'small remove'); b.onclick = protect(action); return b; }
  function renderSites() {
    $('site-count').textContent = spec.sites.length + t(' 个中心');
    if (!spec.sites.length) { $('sites-table').replaceChildren(el('div', t('输入一个代表位置，或载入上方示例。'), 'empty')); updateSelection(); return; }
    const rows = spec.sites.map(site => {
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.checked = selection.has(site.id); checkbox.setAttribute('aria-label', t('选择中心 ') + site.id); checkbox.onchange = () => { checkbox.checked ? selection.add(site.id) : selection.delete(site.id); updateSelection(); };
      const kind = document.createElement('input'); kind.type = 'text'; kind.className = 'kind'; kind.value = site.kind; kind.setAttribute('aria-label', site.id + t(' 类型')); kind.onchange = protect(() => { if (!kind.value.trim()) { kind.value = site.kind; throw new Error(t('中心类型不能为空。')); } checkpoint(); site.kind = kind.value.trim(); invalidate(); render(); });
      const coords = site.position.map((value, axis) => {
        const input = document.createElement('input'); input.type = 'number'; input.step = 'any'; input.value = String(value); input.setAttribute('aria-label', site.id + ' ' + ['x', 'y', 'z'][axis]);
        input.onchange = protect(() => { if (!input.value.trim() || !Number.isFinite(Number(input.value))) { input.value = String(site.position[axis]); throw new Error(t('坐标需要有限数值。')); } checkpoint(); site.position[axis] = Number(input.value); invalidate(); }); return input;
      });
      return [checkbox, site.id, kind, ...coords, removeButton(() => { checkpoint(); spec.sites = spec.sites.filter(s => s.id !== site.id); spec.functions = spec.functions.filter(f => f.site !== site.id); selection.delete(site.id); invalidate(t('已移除中心及引用它的函数，可撤销。')); render(); })];
    });
    makeTable($('sites-table'), [t('选择'), t('中心'), t('类型'), 'x', 'y', 'z', ''], rows); updateSelection();
  }
  function renderFunctions() {
    $('function-count').textContent = spec.functions.length + t(' 个函数'); const batchCounts = new Map(); spec.functions.forEach(f => batchCounts.set(f.batch, (batchCounts.get(f.batch) || 0) + 1));
    $('batch-summary').replaceChildren(); for (const [name, count] of batchCounts) {const item=el('span',undefined,'tag');item.append(M.basisLabel(name),' × '+count);$('batch-summary').append(item);}
    if (!spec.functions.length) { $('functions-table').replaceChildren(el('div', t('勾选中心，然后添加 s、p 或 d 函数。'), 'empty')); return; }
    const angularDescription = f => {
      if(f.family==='s')return t('球对称');if(f.family==='p')return '('+f.direction.map(fmt).join(', ')+')';
      const item=el('span');item.append(M.orbital(f.component),t('；局部轴列矩阵 ')+JSON.stringify(f.frame || [[1,0,0],[0,1,0],[0,0,1]]));return item;
    };
    makeTable($('functions-table'), [t('函数'), t('中心'), t('径向类型'), t('方向 / 局部坐标'), ''], spec.functions.map(f => [M.basisLabel(f.label), f.site, f.radial, angularDescription(f), removeButton(() => { checkpoint(); spec.functions = spec.functions.filter(x => x.id !== f.id); invalidate(); renderFunctions(); })]));
  }
  function render() {
    $('group').value = spec.group; $('tolerance').value = String(spec.tolerance); $('workflow').value=mode;$('manual-group').value=manual.group;$('manual-characters').value=manual.text;$('reduction-tolerance').value=String(manual.tolerance);
    for(const id of ['positions-section','basis-section','group'])$(id).classList[mode==='basis'?'remove':'add']('hidden');
    for(const id of ['manual-section','manual-group'])$(id).classList[mode==='manual'?'remove':'add']('hidden');
    $('group-note').textContent = mode==='basis'?t(E.group(spec.group).note):t('手动约化支持 423 个点群；输入向量须符合当前表的列顺序。');
    $('project-note').textContent = t(spec.note || ''); renderSites(); renderFunctions(); renderCharacterTable();
    $('calculate').textContent=t(mode==='basis'?t('计算并分解'):t('分解特征标'));
  }
  function renderCharacterTable(){
    const table=R.table(mode==='basis'?spec.group:manual.group);
    makeTable($('character-table'),['',...table.classes.map(c=>M.label(c))],table.irreps.map((label,i)=>[M.label(label),...table.expressions[i].map(x=>M.expression(x))]));
    $('table-note').textContent=t('完整复不可约特征标表；复共轭表示分别保留。')+' h = '+table.h;
    $('manual-columns').textContent=t('需要 ')+table.classes.length+t(' 个特征标。');
  }
  function updateSelection() { $('selection-count').textContent = t('已选择 ') + selection.size + t(' 个中心。'); }
  function allocateSiteId(prefix, used) { let k = 0; while (used.has(prefix + k)) k++; const id = prefix + k; used.add(id); return id; }
  function addPositions(positions, kind, prefix) {
    if (!kind || !prefix) throw new Error(t('请填写类型和编号前缀。'));
    const used = new Set(spec.sites.map(s => s.id)), added = [], selected = [], tol = spec.tolerance;
    positions.forEach(position => {
      const matches = [...spec.sites, ...added].filter(s => E.distance(s.position, position) <= tol);
      if (matches.length > 1) throw new Error(t('位置对应多个中心，请调整容差。'));
      if (matches.length) { if (matches[0].kind !== kind) throw new Error(t('该位置已存在不同类型中心 ') + matches[0].id + t('。')); selected.push(matches[0].id); }
      else { const site = { id: allocateSiteId(prefix, used), kind, position }; added.push(site); selected.push(site.id); }
    });
    if (spec.sites.length + added.length > 120) throw new Error(t('初版最多支持 120 个中心。'));
    checkpoint(); spec.sites.push(...added); selection = new Set(selected); invalidate(t('新增 ') + added.length + t(' 个中心；已选择该位置集合。')); render(); return added.length;
  }
  function direction() { const u = ['direction-x', 'direction-y', 'direction-z'].map(id => numberInput(id, t('p 方向'))); const length = Math.hypot(...u); if (length < 1e-10) throw new Error(t('p 方向不能为零。')); return u.map(v => v / length); }
  function localDFrame() {
    const axes = ['x', 'z'].map(axis => {
      const u = ['x','y','z'].map(c => numberInput('d-' + axis + '-' + c, t('局部 ') + axis + t(' 轴')));
      const length = Math.hypot(...u); if (length < 1e-10) throw new Error(t('d 的局部轴不能为零。'));
      return u.map(v => v / length);
    });
    const [x,z] = axes;
    if (Math.abs(x.reduce((sum,v,i) => sum + v*z[i],0)) > 1e-8) throw new Error(t('d 的局部 x′、z′ 轴必须互相垂直。'));
    const y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]];
    return E.frame(E.transpose([x,y,z]));
  }
  function addFunctions() {
    const sites = spec.sites.filter(s => selection.has(s.id)); if (!sites.length) throw new Error(t('请先勾选至少一个中心。'));
    const prefix = $('radial-prefix').value.trim(); if (!prefix) throw new Error(t('请填写径向编号 / 副本标识。'));
    const kinds = ['s', 'px', 'py', 'pz', ...E.dComponents].filter(k => $('orbital-' + k).checked); if ($('orbital-custom').checked) kinds.push('p(u)');
    if (!kinds.length) throw new Error(t('请至少选择一种函数。'));
    const custom = kinds.includes('p(u)') ? direction() : null, dFrame = kinds.some(k => E.dComponents.includes(k)) ? localDFrame() : null, added = [];
    sites.forEach(site => kinds.forEach(axis => {
      const family = axis === 's' ? 's' : E.dComponents.includes(axis) ? 'd' : 'p', radial = prefix + family, u = family === 'p' ? axis === 'p(u)' ? custom : { px: [1, 0, 0], py: [0, 1, 0], pz: [0, 0, 1] }[axis] : null;
      const tensor = family === 'd' ? E.dTensor(axis,dFrame).flat() : null;
      if ([...spec.functions, ...added].some(f => f.site === site.id && f.radial === radial && f.family === family && (family === 's' || family === 'p' && Math.min(E.distance(f.direction, u), E.distance(f.direction, u.map(v => -v))) < 1e-8 || family === 'd' && Math.min(E.distance(E.dTensor(f.component,f.frame).flat(),tensor), E.distance(E.dTensor(f.component,f.frame).flat(),tensor.map(v=>-v))) < 1e-8))) throw new Error(site.id + t(' 已有相同径向类型和方向的函数。'));
      const batch = site.kind + ' ' + prefix + axis + (axis === 'p(u)' ? '[' + u.map(fmt).join(',') + ']' : family === 'd' && E.distance(dFrame.flat(),[1,0,0,0,1,0,0,0,1]) > 1e-8 ? '[frame ' + dFrame.flat().map(fmt).join(',') + ']' : '');
      let id; do { id = 'f-' + (++serial) + '-' + site.id; } while ([...spec.functions, ...added].some(f => f.id === id));
      added.push({ id, site: site.id, radial, family, direction: u, ...(family === 'd' ? {component:axis, frame:dFrame} : {}), batch, label: site.id + ' ' + prefix + axis });
    }));
    if (spec.functions.length + added.length > 180) throw new Error(t('初版最多支持 180 个函数。'));
    checkpoint(); spec.functions.push(...added); invalidate(t('已添加 ') + added.length + t(' 个独立函数；尚未预设它们的计算分组。')); renderFunctions();
  }
  function download(name, data) {
    const nativeSave = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.saveJSON;
    if (nativeSave && typeof nativeSave.postMessage === 'function') {
      nativeSave.postMessage({ name, text: JSON.stringify(data, null, 2) }); return;
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }), url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = name; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function renderResult() {
    const body = $('result-body'); body.replaceChildren(); body.className = '';
    const summary=el('div',undefined,'decomposition');summary.append(M.decomposition(reduction.total));body.append(summary);
    const formula=el('div',undefined,'formula');formula.append(M.formula());body.append(formula);
    body.append(el('div',t('X 的行对应不可约表示、列对应共轭类；星号表示逐项复共轭，不含转置。'),'sub'));
    const aligned = window.ReducerAdapter.align(result);
    const chars = el('div', undefined, 'scroll');
    makeTable(chars, [t('基函数组'), t('维数'), ...aligned.classes.map(c => M.label(c))], [...aligned.blocks.map(b => [M.basisLabel(b.label), b.dimension, ...b.c.map(v=>M.number(v))]), [t('全体'), result.dimension, ...aligned.c.map(v=>M.number(v))]]); body.append(chars);
    const irreducible=el('div',undefined,'scroll');makeTable(irreducible,[t('基函数组'),t('维数'),t('不可约组成')],reduction.blocks.map(b=>[M.basisLabel(b.label),b.dimension,M.decomposition(b)]));body.append(irreducible);
    const details = el('details'); details.append(el('summary', t('分组与检查详情')));
    details.append(el('div', t('已通过位置映射、线性独立性、封闭性、群关系及同类 trace 检查。'), 'notice'));
    const batchScroll = el('div', undefined, 'scroll short');
    makeTable(batchScroll, [t('输入批次'), t('函数数'), t('计算关系')], result.batches.map(b => [b.name, b.dimension, b.closed ? t('可独立计算') : t('需与 ') + b.linkedBatches.join(t('、')) + t(' 联合')])); details.append(batchScroll);
    const vector = el('div', t('全体向量：[') + result.totalCharacters.map(fmt).join(', ') + ']', 'notice vector'); details.append(vector);
    if (result.equivalentBlocks.length) details.append(el('div', t('独立但对称等价：') + result.equivalentBlocks.map(pair => pair.join(' ↔ ')).join(t('；')) + t('。各副本均保留。'), 'equivalence'));
    details.append(el('div', t('已核对各块重数之和等于全体重数；封闭计算块不等同于不可约表示。'), 'sub')); body.append(details);
    $('export-result').disabled = false; $('inspector-card').classList.remove('hidden');
    $('inspect-class').replaceChildren(); aligned.mapping.forEach((map,j)=>option($('inspect-class'),map.source_index,(aligned.class_sizes[j]>1?aligned.class_sizes[j]+' ':'')+M.plainLabel(map.target_class)));
    $('inspect-block').replaceChildren(); option($('inspect-block'), 'all', t('全体基函数')); result.blocks.forEach(b => option($('inspect-block'), b.id, b.id + ' · ' + b.batches.join(' + ')));
    populateOperations();
    $('alignment-vector').replaceChildren(); option($('alignment-vector'), 'all', t('全体基函数')); result.blocks.forEach(b => option($('alignment-vector'), b.id, b.batches.join(' + ')));
    renderAlignment(); $('alignment-card').classList.remove('hidden'); $('export-aligned').disabled = false;
    renderCopy();
  }
  function renderManualResult(){
    const body=$('result-body');body.replaceChildren();body.className='';const r=reduction.total;
    if(!r.valid){body.append(el('div',t('输入不是容差内的合法表示特征标；重数须为非负整数且能重建输入。'),'notice error'));}
    else{const summary=el('div',undefined,'decomposition');summary.append(M.decomposition(r));body.append(summary);}
    const formula=el('div',undefined,'formula');formula.append(M.formula());body.append(formula);
    body.append(el('div',t('X 的行对应不可约表示、列对应共轭类；星号表示逐项复共轭，不含转置。'),'sub'));
    const table=R.table(manual.group),chars=el('div',undefined,'scroll');makeTable(chars,['c',...table.classes.map(c=>M.label(c))],[['',...r.c.map(v=>M.number(v))]]);body.append(chars);
    const weights=el('div',undefined,'scroll');makeTable(weights,[t('不可约表示'),t('重数')],table.irreps.map((name,i)=>[M.label(name),M.number(r.valid?r.integer_a[i]:r.a[i])]));body.append(weights);
    body.append(el('div',t('维数')+' = '+String(R.z(r.dimension).re),'notice'));
    $('export-result').disabled=false;renderCopy();
  }
  function plainDecomposition(r){return 'Γ = '+(r.valid?(r.terms.map(term=>(term.multiplicity===1?'':term.multiplicity)+term.irrep).join(' + ')||'0'):t('无合法不可约组成'));}
  function resultText(latex=false){
    if(!reduction)return '';
    const table=R.table(reduction.point_group),rows=[{label:t('全体'),...reduction.total},...reduction.blocks];
    const plainNumber=v=>{const a=R.z(v);return Math.abs(a.im)<1e-12?String(a.re):a.re+(a.im<0?' - ':' + ')+Math.abs(a.im)+'i';};
    if(latex){
      const escape=s=>String(s).replace(/[\\{}%&#_$^~]/g,c=>({'\\':'\\textbackslash{}','^':'\\textasciicircum{}','~':'\\textasciitilde{}'}[c]||'\\'+c));
      const latexNumber=v=>M.latexExpression(plainNumber(v));
      const lines=['\\mathbf a &= \\frac{1}{h}\\mathbf X^{*}\\mathbf W\\mathbf c'];
      rows.forEach(r=>{lines.push('\\text{'+escape(r.label)+'} &\\quad '+M.latexLabel(table.name),'\\mathbf c &= \\left('+r.c.map(latexNumber).join(', ')+'\\right)','\\mathbf a &= \\left('+(r.valid?r.integer_a:r.a).map(latexNumber).join(', ')+'\\right)',r.valid?'\\Gamma &= '+(r.terms.map(term=>(term.multiplicity===1?'':term.multiplicity)+M.latexLabel(term.irrep)).join(' + ')||'0'):'\\text{'+t('无合法不可约组成')+'}','\\dim\\Gamma &= '+latexNumber(r.dimension));});
      return '\\begin{aligned}\n'+lines.join(' \\\\\n')+'\n\\end{aligned}';
    }
    return table.name+'    h = '+table.h+'\n'+table.classes.join(', ')+'\n'+rows.map(r=>r.label+'\n'+plainDecomposition(r)+'\nc = ['+r.c.map(plainNumber).join(', ')+']\na = ['+(r.valid?r.integer_a:r.a).map(plainNumber).join(', ')+']\n'+t('维数')+' = '+plainNumber(r.dimension)).join('\n\n');
  }
  function renderCopy(){ $('copy-card').classList.remove('hidden');$('copy-content').value=resultText(); }
  function copyResult(latex){
    const text=resultText(latex);$('copy-content').value=text;
    const bridge=window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.copyText;
    if(bridge){bridge.postMessage({text});status(t('已复制结果。'));return;}
    if(navigator.clipboard&&typeof navigator.clipboard.writeText==='function')navigator.clipboard.writeText(text).then(()=>status(t('已复制结果。'))).catch(()=>{ $('copy-content').focus();$('copy-content').select();status(t('内容已选中，请复制。'));});
    else{$('copy-content').focus();$('copy-content').select();status(t('内容已选中，请复制。'));}
  }
  function renderAlignment() {
    if (!result) return;
    const aligned = window.ReducerAdapter.align(result), row = aligned.blocks.find(b => b.id === $('alignment-vector').value) || {c:aligned.c,dimension:aligned.dimension,label:t('全体')};
    makeTable($('alignment-table'), [t('向量'), ...aligned.classes.map(c=>M.label(c))], [[M.basisLabel(row.label), ...row.c.map(v=>M.number(v))]]);
    // 粘贴到原程序时保留双精度，避免展示用七位有效数字造成约化失败。
    $('alignment-text').value = row.c.map(String).join(', ');
  }
  function populateOperations() {
    if (!result) return; const c = result.classes[Number($('inspect-class').value)]; $('inspect-operation').replaceChildren(); c.operationIndexes.forEach(i => option($('inspect-operation'), i, result.operations[i].id + (i === c.representative ? t(' · 代表操作') : ''))); renderInspector();
  }
  function renderInspector() {
    if (!result) return; const gi = Number($('inspect-operation').value), op = result.operations[gi], d = result.representationMatrices[gi], block = result.blocks.find(b => b.id === $('inspect-block').value), ids = block ? block.indices : result.functions.map((_, i) => i);
    $('operation-matrix').textContent = op.matrix.map(row => '[ ' + row.map(v => fmt(v).padStart(10)).join(' ') + ' ]').join('\n');
    const fixed = result.sites.filter((_, i) => op.sitePermutation[i] === i).map(s => s.id), trace = ids.reduce((s, i) => s + d[i][i], 0);
    $('fixed-sites').textContent = t('保持原位的中心：') + (fixed.length ? fixed.join(t('、')) : t('无')) + t('。所选空间 trace = ') + fmt(trace) + t('。');
    const rows = ids.map(j => {
      const terms = result.functions.flatMap((f, i) => Math.abs(d[i][j]) > 1e-9 ? [{ value: d[i][j], label: f.label }] : []);
      const output = el('span', undefined, 'transform');
      terms.forEach((term,k)=>{output.append(k?(term.value<0?' − ':' + '):term.value<0?'−':'');if(Math.abs(Math.abs(term.value)-1)>1e-9)output.append(M.number(Math.abs(term.value)),' ');output.append(M.basisLabel(term.label));});
      return [M.basisLabel(result.functions[j].label), output, M.number(d[j][j])];
    }); makeTable($('transform-table'), [t('原函数'), t('操作后的完整展开'), t('对角贡献')], rows);
    makeTable($('mapping-table'), [t('原中心'), t('目标中心'), t('变换后坐标')], result.sites.map((s, i) => [s.id, result.sites[op.sitePermutation[i]].id, '(' + E.apply(op.matrix, s.position).map(fmt).join(', ') + ')']));
  }
  function loadTemplate(name) {
    checkpoint(); mode='basis';spec = E.template(name);manual.group=spec.group; selection = new Set(spec.sites.filter(s => name === 'benzene' ? s.kind === 'C' : true).map(s => s.id)); invalidate(t('已载入示例。坐标与轨道均可编辑。')); render();
  }
  E.groupNames.forEach(name => option($('group'), name, M.plainLabel(name)));
  R.groupNames.forEach(name=>option($('manual-group'),name,M.plainLabel(name)));
  document.querySelectorAll('[data-template]').forEach(b => b.onclick = protect(() => loadTemplate(b.dataset.template)));
  $('group').onchange = protect(() => { checkpoint(); spec.group = $('group').value; invalidate(t('点群已改变；已有位置和函数已保留，需要重新验证。')); render(); });
  $('workflow').onchange=protect(()=>{checkpoint();mode=$('workflow').value==='manual'?'manual':'basis';if(mode==='manual')manual.group=spec.group;invalidate();render();});
  $('manual-group').onchange=protect(()=>{R.table($('manual-group').value);checkpoint();manual.group=$('manual-group').value;invalidate();render();});
  $('manual-characters').oninput=()=>{manual.text=$('manual-characters').value;invalidate();};
  $('reduction-tolerance').onchange=protect(()=>{const n=numberInput('reduction-tolerance',t('约化容差'));if(n<=0||n>=.01){$('reduction-tolerance').value=String(manual.tolerance);throw new R.ReductionError('invalid_reduction_tolerance');}checkpoint();manual.tolerance=n;invalidate();});
  for(const [id,l] of [['manual-s',0],['manual-p',1],['manual-d',2]])$(id).onclick=protect(()=>{checkpoint();const table=R.table(manual.group),meta=window.ReductionCatalog.groups[manual.group];manual.text=meta.orbital[l].map(String).join(', ');invalidate();render();});
  $('tolerance').onchange = protect(() => { let value; try { value = numberInput('tolerance', t('容差')); if (value < 1e-10 || value > 0.01) throw new Error(t('容差需在 1e−10 至 0.01 之间。')); } catch (error) { $('tolerance').value = String(spec.tolerance); throw error; } checkpoint(); spec.tolerance = value; invalidate(); });
  $('expand-seed').onclick = protect(() => {
    const seed = ['seed-x', 'seed-y', 'seed-z'].map(id => numberInput(id, t('代表坐标'))), orbit = E.orbit(spec.group, seed, spec.tolerance), count = $('seed-count').value.trim();
    if (count && (!Number.isInteger(Number(count)) || Number(count) !== orbit.count)) throw new Error(t('实际生成 ') + orbit.count + t(' 个位置，与预期 ') + count + t(' 不同；未添加任何位置。'));
    addPositions(orbit.positions, $('seed-kind').value.trim(), $('seed-prefix').value.trim()); $('orbit-note').textContent = t('生成 ') + orbit.count + t(' 个唯一位置；稳定子含 ') + orbit.stabilizerSize + t(' 个操作。');
  });
  $('add-site').onclick = protect(() => addPositions([['seed-x', 'seed-y', 'seed-z'].map(id => numberInput(id, t('坐标')))], $('seed-kind').value.trim(), $('seed-prefix').value.trim()));
  $('apply-sites').onclick = protect(() => {
    const text = $('paste-sites').value.trim(); if (!text) throw new Error(t('请粘贴坐标。')); const rows = text.split(/\n/).filter(s => s.trim()).map(line => { const p = line.trim().split(/[\s,]+/); if (p.length !== 5 || p.slice(2).some(x => !Number.isFinite(Number(x)))) throw new Error(t('每行需要：编号 类型 x y z。')); return { id: p[0], kind: p[1], position: p.slice(2).map(Number) }; });
    if (rows.length + spec.sites.length > 120) throw new Error(t('初版最多支持 120 个中心。'));
    const all = [...spec.sites, ...rows]; if (new Set(all.map(s => s.id)).size !== all.length) throw new Error(t('存在重复中心编号。'));
    for (let i = 0; i < all.length; i++) for (let j = 0; j < i; j++) if (E.distance(all[i].position, all[j].position) <= spec.tolerance) throw new Error(t('存在重合中心，请复用已有中心。'));
    checkpoint(); spec.sites.push(...rows); selection = new Set(rows.map(s => s.id)); invalidate(t('已添加 ') + rows.length + t(' 个中心。')); render();
  });
  $('select-all-sites').onclick = () => { selection = new Set(spec.sites.map(s => s.id)); renderSites(); };
  $('select-no-sites').onclick = () => { selection.clear(); renderSites(); };
  const selectOrbitals = chosen => ['s', 'px', 'py', 'pz', 'custom', ...E.dComponents].forEach(k => { $('orbital-' + k).checked = chosen.includes(k); });
  $('select-p').onclick = () => selectOrbitals(['px','py','pz']);
  $('select-d').onclick = () => selectOrbitals(E.dComponents);
  $('select-s').onclick = () => selectOrbitals(['s']);
  $('add-functions').onclick = protect(addFunctions);
  $('clear-functions').onclick = protect(() => { checkpoint(); spec.functions = []; invalidate(t('已清空函数；中心坐标保留，可撤销。')); renderFunctions(); });
  $('calculate').onclick = () => {
    invalidate(); $('calculate').disabled = true; status(t('正在逐函数检查变换、分组和群关系…'));
    const current=revision,input=clone(spec),manualInput=clone(manual),method=mode;
    setTimeout(() => { try { if(current!==revision)return;
      if(method==='basis'){const basis=E.calculate(input),integrated=R.integrate(basis,window.ReducerAdapter);result=basis;result.conventions.reductionIntegrated=true;result.reduction=integrated;reduction=integrated;renderResult();status(t('已生成 ') + result.blocks.length + t(' 个封闭空间的特征标，共 ') + result.dimension + t(' 个基函数。'), 'success');}
      else{const total=R.reduce(manualInput.group,R.parseVector(manualInput.text),manualInput.tolerance);reduction={schemaVersion:1,reductionIntegrated:true,point_group:manualInput.group,total,blocks:[]};renderManualResult();status(total.valid?t('不可约分解已完成。'):t('特征标未通过合法表示检查。'),total.valid?'success':'error');}
    }
      catch (error) { protect(() => { throw error; })(); $('result-body').textContent = t('输入未通过验证，尚未生成可约表示特征标。'); }
      finally { $('calculate').disabled = false; }
    }, 20);
  };
  $('inspect-class').onchange = populateOperations; $('inspect-operation').onchange = renderInspector; $('inspect-block').onchange = renderInspector;
  $('alignment-vector').onchange = protect(renderAlignment);
  $('export-aligned').onclick = protect(() => { if (!result) throw new Error(t('请先生成结果。')); download('reducer-input-' + spec.group + '.json', {...window.ReducerAdapter.align(result),reductionIntegrated:true,reduction}); });
  $('save-project').onclick = protect(() => download('symmetry-input-' + (mode==='basis'?spec.group:manual.group) + '.json', { schemaVersion: 1, application: 'symmetry-integrated', version: E.VERSION, language:I.language(), input: mode==='basis'?spec:{mode:'manual',...manual} }));
  $('export-result').onclick = protect(() => { if (!reduction) throw new Error(t('请先生成结果。')); const exportReduction={...reduction,table:R.payload(reduction.point_group)};download('symmetry-result-' + reduction.point_group + '.json', mode==='basis'?{ ...result,reduction:exportReduction, input: spec,language:I.language() }:{schemaVersion:1,engineVersion:E.VERSION,status:reduction.total.valid?'valid':'invalid',reductionIntegrated:true,reduction:exportReduction,language:I.language(),input:{mode:'manual',...manual}}); });
  $('copy-text').onclick=protect(()=>copyResult(false));$('copy-latex').onclick=protect(()=>copyResult(true));
  $('load-project').onclick = protect(() => {
    const nativeOpen = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.openJSON;
    if (nativeOpen && typeof nativeOpen.postMessage === 'function') nativeOpen.postMessage({});
    else $('project-file').click();
  });
  function importProjectText(text) {
      const data = JSON.parse(text); if (data.schemaVersion !== 1) throw new Error(t('不支持的输入版本。'));
      const input = data.input || data;
      if(input&&input.mode==='manual'){
        R.table(input.group);if(typeof input.text!=='string'||input.text.length>32768||typeof input.tolerance!=='number'||!Number.isFinite(input.tolerance)||input.tolerance<=0||input.tolerance>=.01)throw new Error(t('手动特征标输入格式有误。'));
        checkpoint();mode='manual';manual={group:input.group,text:input.text,tolerance:input.tolerance};invalidate(t('已载入输入。请重新计算，不沿用文件中的旧结果。'));render();return;
      }
      if (!input || !Array.isArray(input.sites) || !Array.isArray(input.functions) || input.sites.length > 120 || input.functions.length > 180) throw new Error(t('输入结构或数量有误。'));
      E.group(input.group);
      if (typeof input.tolerance !== 'number' || !Number.isFinite(input.tolerance) || input.tolerance < 1e-10 || input.tolerance > 0.01) throw new Error(t('输入容差无效。'));
      if (input.sites.some(s => typeof s.id !== 'string' || typeof s.kind !== 'string' || !Array.isArray(s.position) || s.position.length !== 3 || s.position.some(x => typeof x !== 'number' || !Number.isFinite(x)))) throw new Error(t('中心数据格式有误。'));
      if (new Set(input.sites.map(s => s.id)).size !== input.sites.length || input.functions.some(f => typeof f.id !== 'string' || typeof f.site !== 'string' || typeof f.radial !== 'string' || !['s', 'p', 'd'].includes(f.family) || (f.family === 'p' && (!Array.isArray(f.direction) || f.direction.length !== 3 || f.direction.some(x => typeof x !== 'number' || !Number.isFinite(x)))))) throw new Error(t('基函数数据格式有误。'));
      input.functions.filter(f => f.family === 'd').forEach(f => E.dTensor(f.component, f.frame));
      const ids = new Set(input.sites.map(s => s.id)); if (new Set(input.functions.map(f => f.id)).size !== input.functions.length || input.functions.some(f => !ids.has(f.site))) throw new Error(t('函数编号重复或引用了不存在的中心。'));
      checkpoint(); mode='basis';spec = { schemaVersion: 1, group: input.group, tolerance: input.tolerance, sites: input.sites.map(s => ({ id: s.id, kind: s.kind, position: s.position.slice() })), functions: input.functions.map(f => ({ ...f, label: String(f.label || f.id), batch: String(f.batch || f.family) })), note: String(input.note || '') }; selection = new Set(spec.sites.map(s => s.id)); invalidate(t('已载入输入。请重新计算，不沿用文件中的旧结果。')); render();
  }
  window.BasisDesktop = { importJSON: text => protect(() => importProjectText(text))(),setLanguage:language=>I.setLanguage(language) };
  $('project-file').onchange = async () => {
    try {
      const file = $('project-file').files[0]; if (!file) return; if (file.size > 2 * 1024 * 1024) throw new Error(t('输入文件不能超过 2 MiB。'));
      importProjectText(await file.text());
    } catch (error) { status(I.error(error), 'error'); } finally { $('project-file').value = ''; }
  };
  $('undo').onclick = () => { if (!history.length) return; const old = history.pop(); spec = old.spec; mode=old.mode;manual=old.manual;selection = new Set(old.selection); invalidate(t('已撤销最近一次输入修改。')); $('undo').disabled = !history.length; render(); };
  $('new-project').onclick = () => { checkpoint();if(mode==='manual')manual.text='';else{spec = { schemaVersion: 1, group: spec.group, tolerance: spec.tolerance, sites: [], functions: [], note: '' }; selection.clear();} invalidate(t('已新建空项目，可撤销。')); render(); };
  $('language').onchange=()=>I.setLanguage($('language').value);
  I.onChange(()=>{
    const view=['inspect-class','inspect-operation','inspect-block','alignment-vector'].map(id=>[id,$(id).value]);
    I.apply(document);$('language').value=I.language();render();
    if(reduction){if(mode==='basis'){renderResult();view.forEach(([id,value])=>$(id).value=value);populateOperations();$('inspect-operation').value=view[1][1];renderInspector();renderAlignment();}else renderManualResult();}
    status(lastMessage,lastKind,lastDetail);
  });
  loadTemplate('benzene'); history = []; $('undo').disabled = true;
  for(const axis of ['s','px','py','pz',...E.dComponents])$('symbol-'+axis).replaceChildren(M.orbital(axis));
  for(const axis of ['x','y','z'])$('symbol-direction-'+axis).replaceChildren(M.component('u',axis));
  I.apply(document);$('language').value=I.language();
})();
