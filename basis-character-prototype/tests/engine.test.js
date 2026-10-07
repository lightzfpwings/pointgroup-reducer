'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine.js');
const copy = x => JSON.parse(JSON.stringify(x));
const expectCode = (fn, code) => assert.throws(fn, error => error instanceof E.BasisError && error.code === code);
const chars = (r, names) => r.blocks.find(b => names.every(name => b.batches.includes(name))).characters;
const scalarHex = [6, 0, 0, 0, 2, 0, 0, 0, 0, 6, 0, 2];

test('original nine groups retain their orders and conjugacy class counts', () => {
  const counts = { C1: [1, 1], Cs: [2, 2], Ci: [2, 2], C2v: [4, 4], C3v: [6, 3], C6v: [12, 6], D2h: [8, 8], D6h: [24, 12], Oh: [48, 10] };
  for (const [name, [order, classes]] of Object.entries(counts)) {
    const g = E.group(name); assert.equal(g.size, order); assert.equal(g.classes.length, classes);
    assert.equal(g.classes.reduce((n, c) => n + c.size, 0), order);
    assert.equal(new Set(g.classes.flatMap(c => c.members)).size, order);
    assert.equal(new Set(g.classes.map(c => c.label)).size, classes);
  }
});
test('D6h class order and multiplicities match documented convention', () => {
  const g = E.group('D6h');
  assert.deepEqual(g.classes.map(c => c.size), [1, 2, 2, 1, 3, 3, 1, 2, 2, 1, 3, 3]);
  assert.deepEqual(g.classes.map(c => c.label), ['E', 'C₆', 'C₃', 'C₂(z)', 'C₂′', 'C₂″', 'i', 'S₃', 'S₆', 'σₕ(xy)', 'σᵈ', 'σᵥ']);
});
test('seed orbit distinguishes ring, origin and general positions', () => {
  assert.equal(E.orbit('D6h', [1, 0, 0]).count, 6);
  assert.equal(E.orbit('D6h', [0, 0, 0]).count, 1);
  assert.equal(E.orbit('D6h', [1, 0.123, 0]).count, 12);
  assert.equal(E.orbit('D6h', [1, 0, 0.4]).count, 12);
  assert.equal(E.orbit('D6h', [1, 0.123, 0.4]).count, 24);
});
test('one s seed produces analytic benzene ring positions and trace', () => {
  const o = E.orbit('D6h', [1, 0, 0]);
  const expected = Array.from({ length: 6 }, (_, k) => [Math.cos(k * Math.PI / 3), Math.sin(k * Math.PI / 3), 0]);
  expected.forEach(p => assert(o.positions.some(q => E.distance(p, q) < 1e-9)));
  assert.equal(o.stabilizerSize, 4);
  const sites = o.positions.map((position, i) => ({ id: 'C' + i, kind: 'C', position }));
  const functions = sites.map(s => ({ id: s.id + ':s', site: s.id, family: 's', radial: '2s', batch: 'C 2s' }));
  const r = E.calculate({ group: 'D6h', sites, functions }); assert.deepEqual(r.totalCharacters, scalarHex);
});
test('benzene four invariant spaces are derived from five input batches', () => {
  const r = E.calculate(E.template('benzene'));
  assert.equal(r.dimension, 30); assert.equal(r.batches.length, 5); assert.equal(r.blocks.length, 4);
  assert.deepEqual(chars(r, ['C 2s']), scalarHex); assert.deepEqual(chars(r, ['H 1s']), scalarHex);
  assert.deepEqual(chars(r, ['C 2pz']), [6, 0, 0, 0, -2, 0, 0, 0, 0, -6, 0, 2]);
  assert.deepEqual(chars(r, ['C 2px', 'C 2py']), [12, 0, 0, 0, 0, 0, 0, 0, 0, 12, 0, 0]);
  assert.equal(r.batches.find(b => b.name === 'C 2px').closed, false);
  assert.equal(r.batches.find(b => b.name === 'C 2px').characters, null);
  assert.equal(r.equivalentBlocks.length, 1);
  assert(r.checks.representationError < 1e-12);
});
test('water in xz gives two-H-s characters [2,0,2,0]', () => {
  const r = E.calculate(E.template('water')); assert.deepEqual(r.totalCharacters, [2, 0, 2, 0]); assert.equal(r.dimension, 2);
});
test('central C2v keeps three Cartesian p spaces independent', () => {
  const r = E.calculate(E.template('central-c2v')); assert.equal(r.blocks.length, 3); assert.equal(r.equivalentBlocks.length, 0);
  assert.deepEqual(chars(r, ['X px']), [1, -1, 1, -1]);
  assert.deepEqual(chars(r, ['X py']), [1, -1, -1, 1]);
  assert.deepEqual(chars(r, ['X pz']), [1, 1, 1, 1]);
});
test('central Oh dynamically joins all three p directions', () => {
  const r = E.calculate(E.template('central-oh')); assert.equal(r.blocks.length, 1); assert.equal(r.blocks[0].dimension, 3);
  assert.deepEqual(r.blocks[0].batches.sort(), ['X px', 'X py', 'X pz']);
  const i = r.classes.findIndex(c => c.label === 'i'); assert.equal(r.totalCharacters[i], -3);
  const c4 = r.classes.find(c => c.label === 'C₄');
  const partial = r.batches.find(b => b.name === 'X px').diagonalContributionsByOperation;
  assert(new Set(c4.operationIndexes.map(k => partial[k])).size > 1, 'partial trace is not a class character');
});
test('partial benzene px selection fails rather than projecting out py', () => {
  const s = E.template('benzene'); s.functions = s.functions.filter(f => f.batch === 'C 2px');
  expectCode(() => E.calculate(s), 'basis_not_closed');
});
test('partial central Oh px/py selection also fails closure', () => {
  const s = E.template('central-oh'); s.functions = s.functions.filter(f => f.batch !== 'X pz');
  expectCode(() => E.calculate(s), 'basis_not_closed');
});
test('missing geometric image stops the calculation', () => {
  const s = E.template('benzene'); s.sites[0].position[0] += 0.2;
  expectCode(() => E.calculate(s), 'missing_site');
});
test('site matching preserves element/equivalence kind', () => {
  const s = E.template('benzene'); s.sites[0].kind = 'N'; expectCode(() => E.calculate(s), 'missing_site');
});
test('radial functions cannot be substituted merely by angular shape', () => {
  const s = E.template('benzene'); s.functions.find(f => f.batch === 'C 2s').radial = '3s';
  expectCode(() => E.calculate(s), 'basis_not_closed');
});
test('duplicate s function is rejected', () => {
  const s = E.template('water'); s.functions.push({ ...s.functions[0], id: 'duplicate' });
  expectCode(() => E.calculate(s), 'dependent_basis');
});
test('opposite p directions are linearly dependent, not another orbital', () => {
  const s = E.template('central-c2v'); s.functions.push({ ...s.functions[0], id: 'minus-px', direction: [-1, 0, 0] });
  expectCode(() => E.calculate(s), 'dependent_basis');
});
test('custom nonorthogonal complete p basis preserves full-shell trace', () => {
  const s = E.template('central-c2v'), original = E.calculate(s);
  [[1, 0, 0], [1, 1, 0], [1, 1, 1]].forEach((u, i) => { s.functions[i].direction = u; });
  const r = E.calculate(s); assert.deepEqual(r.totalCharacters, original.totalCharacters); assert(r.checks.representationError < 1e-12);
});
test('p phases and function/site ordering do not change characters', () => {
  const s = E.template('benzene'), original = E.calculate(s);
  s.functions.forEach((f, i) => { if (f.family === 'p' && i % 2) f.direction = f.direction.map(x => -x); });
  s.functions.reverse(); s.sites.reverse(); const r = E.calculate(s);
  assert.deepEqual(r.totalCharacters, original.totalCharacters);
  assert.deepEqual(chars(r, ['C 2px', 'C 2py']), chars(original, ['C 2px', 'C 2py']));
});
test('multiple equivalent radial copies retain all dimensions', () => {
  const s = E.template('water'); s.functions.push(...s.functions.map(f => ({ ...f, id: f.id + '-copy', radial: 'second-s', batch: 'H second s' })));
  const r = E.calculate(s); assert.equal(r.dimension, 4); assert.equal(r.blocks.length, 2); assert.equal(r.equivalentBlocks.length, 1); assert.deepEqual(r.totalCharacters, [4, 0, 4, 0]);
});
test('every benzene representation product obeys the group law', () => {
  const r = E.calculate(E.template('benzene')), g = E.group('D6h'), n = r.dimension;
  for (let a = 0; a < g.size; a++) for (let b = 0; b < g.size; b++) {
    const target = r.representationMatrices[g.multiply[a][b]], first = r.representationMatrices[a], second = r.representationMatrices[b];
    for (let i = 0; i < n; i++) {
      const row = Array(n).fill(0); for (let k = 0; k < n; k++) if (first[i][k]) for (let j = 0; j < n; j++) if (second[k][j]) row[j] += first[i][k] * second[k][j];
      row.forEach((v, j) => assert(Math.abs(v - target[i][j]) < 1e-9));
    }
  }
});
test('project JSON roundtrip reconstructs matrices and classes', () => {
  const s = E.template('benzene'), r = E.calculate(s), restored = E.calculate(copy(s));
  assert.deepEqual(restored.totalCharacters, r.totalCharacters); assert.deepEqual(restored.representationMatrices, r.representationMatrices);
  assert.equal(r.conventions.reductionIntegrated, false);
});
test('unsupported group, zero direction, bad tolerance and duplicate sites fail', () => {
  expectCode(() => E.group('C13'), 'unsupported_group');
  const s = E.template('central-c2v'); s.functions[0].direction = [0, 0, 0]; expectCode(() => E.calculate(s), 'zero_direction');
  const t = E.template('water'); t.tolerance = 1; expectCode(() => E.calculate(t), 'invalid_tolerance');
  const u = E.template('water'); u.sites.push({ ...u.sites[0], id: 'Ocopy' }); expectCode(() => E.calculate(u), 'coincident_sites');
});
test('every supported group yields a valid full central p representation', () => {
  for (const name of E.groupNames) {
    const s = E.template('central-c2v'); s.group = name; const r = E.calculate(s);
    assert.equal(r.dimension, 3); assert(r.checks.representationError < 1e-9);
    r.classes.forEach((c, i) => { const m = r.operations[c.representative].matrix; assert(Math.abs(r.totalCharacters[i] - m[0][0] - m[1][1] - m[2][2]) < 1e-9); });
  }
});
test('87 finite point groups have independent theoretical orders and class counts', () => {
  assert.equal(E.groupNames.length, 87); assert.equal(new Set(E.groupNames).size, 87);
  for (let n = 2; n <= 12; n++) {
    const dihedralClasses = n % 2 === 0 ? n / 2 + 3 : (n + 3) / 2;
    for (const [name, order, classes] of [['C' + n, n, n], ['C' + n + 'v', 2*n, dihedralClasses], ['C' + n + 'h', 2*n, 2*n], ['D' + n, 2*n, dihedralClasses], ['D' + n + 'h', 4*n, 2*dihedralClasses], ['D' + n + 'd', 4*n, n+3], ['S' + 2*n, 2*n, 2*n]]) {
      const g = E.group(name); assert.equal(g.size, order, name); assert.equal(g.classes.length, classes, name);
      assert.equal(new Set(g.classes.map(c => c.label)).size, classes, name);
      assert.equal(new Set(g.classes.flatMap(c => c.members)).size, order, name);
    }
  }
  for (const [name, order, sizes] of [['T',12,[1,3,4,4]],['Th',24,[1,1,3,3,4,4,4,4]],['Td',24,[1,3,6,6,8]],['O',24,[1,3,6,6,8]],['I',60,[1,12,12,15,20]],['Ih',120,[1,1,12,12,12,12,15,15,20,20]]]) {
    const g=E.group(name); assert.equal(g.size,order,name); assert.deepEqual(g.classes.map(c=>c.size).sort((a,b)=>a-b),sizes,name);
  }
});
test('all supported spatial matrices have orthogonality, inverse and group product identities', () => {
  for (const name of E.groupNames) {
    const g=E.group(name);
    g.matrices.forEach((m,i)=>{
      const identity=E.matmul(m,E.transpose(m)); identity.forEach((row,a)=>row.forEach((v,b)=>assert(Math.abs(v-(a===b?1:0))<1e-9,name)));
      assert.equal(g.multiply[i][g.inverse[i]],0,name);
    });
    g.multiply.forEach((row,a)=>row.forEach((index,b)=>{
      const m=E.matmul(g.matrices[a],g.matrices[b]), target=g.matrices[index];
      m.forEach((r,i)=>r.forEach((v,j)=>assert(Math.abs(v-target[i][j])<1e-9,name)));
    }));
  }
});
test('tetrahedral generators realize a regular tetrahedron, not just correct order', () => {
  for (const name of ['T','Td']) {
    const points=E.orbit(name,[0,0,1]).positions; assert.equal(points.length,4);
    for(let i=0;i<4;i++) for(let j=0;j<i;j++) assert(Math.abs(E.distance(points[i],points[j])**2-8/3)<1e-9);
    const sites=points.map((position,i)=>({id:'X'+i,kind:'X',position}));
    const functions=sites.map(s=>({id:s.id+':s',site:s.id,radial:'s',family:'s',batch:'X s'}));
    const r=E.calculate({group:name,sites,functions});
    r.classes.forEach((c,i)=>{ if(c.label.startsWith('C₃')) assert.equal(r.totalCharacters[i],1); if(c.label==='C₂') assert.equal(r.totalCharacters[i],0); });
  }
});
test('icosahedral seed gives twelve regular vertices with C5 aligned to z', () => {
  for(const name of ['I','Ih']) {
    const points=E.orbit(name,[0,0,1]).positions; assert.equal(points.length,12);
    points.forEach(p=>{ assert(Math.abs(Math.hypot(...p)-1)<1e-9); assert([1,-1,1/Math.sqrt(5),-1/Math.sqrt(5)].some(z=>Math.abs(p[2]-z)<1e-9)); });
    const distances=points.slice(1).map(p=>E.distance(points[0],p)).sort((a,b)=>a-b);
    assert.equal(distances.filter(d=>Math.abs(d-distances[0])<1e-9).length,5);
    assert.equal(distances.filter(d=>Math.abs(d-2)<1e-9).length,1);
  }
  const r=E.calculate(E.template('icosahedron')); assert.equal(r.dimension,12); assert.equal(r.blocks.length,1);
  assert.equal(r.totalCharacters[r.classes.findIndex(c=>c.label==='C₅')],2);
  assert.equal(r.totalCharacters[r.classes.findIndex(c=>c.label==='C₅²')],2);
  assert.equal(r.totalCharacters[r.classes.findIndex(c=>c.label==='i·C₂')],4);
});
test('inverse rotations and tetrahedral handed classes are not merged by trace or angle', () => {
  assert.equal(E.group('C7').classes.length,7);
  const t=E.group('T'); assert.equal(t.classes.filter(c=>c.label.startsWith('C₃')).length,2);
  assert.equal(t.classes.find(c=>c.label==='C₃⁺').size,4); assert.equal(t.classes.find(c=>c.label==='C₃⁻').size,4);
});
test('expanded groups preserve scalar orbits and original input-file compatibility', () => {
  for(const name of ['C7v','C12h','D3h','D4d','S24','Th','Ih']) {
    const positions=E.orbit(name,[0.72,0.31,0.27]).positions;
    const sites=positions.map((position,i)=>({id:'X'+i,kind:'X',position}));
    const functions=sites.map(s=>({id:s.id+':s',site:s.id,family:'s',radial:'s',batch:'X s'}));
    const r=E.calculate({group:name,sites,functions}); assert.equal(r.dimension,positions.length);
    r.operations.forEach((op,i)=>{ const fixed=op.sitePermutation.filter((j,k)=>j===k).length; const cls=r.classes.findIndex(c=>c.operationIndexes.includes(i)); assert.equal(r.totalCharacters[cls],fixed); });
  }
  const legacy=require('./fixtures/legacy-benzene-0.1.0.json'); assert.equal(legacy.version,'0.1.0'); assert.equal(E.calculate(legacy.input).dimension,30);
});
