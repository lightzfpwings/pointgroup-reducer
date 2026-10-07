'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine.js'), A = require('../reducer-adapter.js');
const reference = require('./fixtures/reducer-reference.json').groups;
const shell = name => { const input = E.template('central-d-oh'); input.group = name; return input; };
const near = (a,b) => assert(Math.abs(a-b) < 1e-7, `${a} != ${b}`);
const code = (fn,c) => assert.throws(fn,e=>e instanceof E.BasisError && e.code===c);
const angle = .371, rotate = [[Math.cos(angle),0,Math.sin(angle)],[0,1,0],[-Math.sin(angle),0,Math.cos(angle)]];

test('five real d tensors are symmetric, traceless and orthonormal',()=>{
  const qs = E.dComponents.map(c=>E.dTensor(c));
  qs.forEach((q,i)=>{
    near(q[0][0]+q[1][1]+q[2][2],0);
    q.forEach((row,j)=>row.forEach((v,k)=>near(v,q[k][j])));
    qs.forEach((p,j)=>near(q.flat().reduce((s,v,k)=>s+v*p.flat()[k],0),i===j?1:0));
  });
});
test('all 87 d representations match original central l=2 characters after class alignment',()=>{
  for(const name of E.groupNames){
    const r=E.calculate(shell(name)), aligned=A.align(r), expected=reference[name];
    assert.deepEqual(aligned.classes,expected.classes,name); assert.deepEqual(aligned.class_sizes,expected.class_sizes,name);
    aligned.c.forEach((v,j)=>near(v,expected.orbital['2'][j]));
    assert.equal(r.dimension,5); assert(r.checks.representationError<1e-9);
  }
});
test('Oh d blocks have dimensions 3 and 2; C2v has five independent components',()=>{
  assert.deepEqual(E.calculate(shell('Oh')).blocks.map(b=>b.dimension).sort(),[2,3]);
  const r=E.calculate(shell('C2v')); assert.equal(r.blocks.length,5);
  assert.equal(r.equivalentBlocks.length,1); // dz2 和 dx2-y2 两个独立 A1 副本。
  assert.deepEqual(A.align(r).c,[5,1,1,1]);
});
test('dxy/dx2-y2 at C3 mix with the correct normalized sine/cosine coefficients',()=>{
  const input=shell('C3'); input.functions=input.functions.filter(f=>['dxy','dx2-y2'].includes(f.component));
  const r=E.calculate(input), g=E.group('C3'), gi=g.generatorIndexes[0], d=r.representationMatrices[gi];
  assert.equal(r.blocks.length,1); near(d[0][0],-.5); near(d[1][0],Math.sqrt(3)/2); near(d[0][1],-Math.sqrt(3)/2);
  input.functions=input.functions.slice(0,1); code(()=>E.calculate(input),'basis_not_closed');
});
test('inversion preserves d and reflection gives expected component signs',()=>{
  const r=E.calculate(shell('Cs')), op=r.operations.findIndex(o=>o.matrix[2][2]===-1);
  assert.deepEqual(r.representationMatrices[op].map((row,i)=>row[i]),[1,-1,-1,1,1]);
  assert.deepEqual(A.align(E.calculate(shell('Ci'))).c,[5,5]);
});
test('a rotated local d frame preserves characters but changes the matrices',()=>{
  for(const name of ['C2v','D6h','Oh','Ih']){
    const input=shell(name), original=E.calculate(input); input.functions.forEach(f=>f.frame=rotate);
    const rotated=E.calculate(input); rotated.totalCharacters.forEach((v,i)=>near(v,original.totalCharacters[i]));
    assert(rotated.checks.representationError<1e-9);
  }
  const input=shell('C2v');input.functions=input.functions.filter(f=>f.component==='dz2');input.functions[0].frame=rotate;
  code(()=>E.calculate(input),'basis_not_closed');
});
test('d is allowed away from the origin and on multiple symmetry-related centers',()=>{
  const input=shell('C3v');input.sites=E.orbit('C3v',[1,0,0.2]).positions.map((position,i)=>({id:'M'+i,kind:'M',position}));
  const fs=input.functions; input.functions=input.sites.flatMap(s=>fs.map(f=>({...f,id:s.id+f.component,site:s.id})));
  const r=E.calculate(input); assert.equal(r.dimension,15);
  const central=E.calculate(shell('C3v'));
  r.operations.forEach((op,gi)=>{
    const fixed=op.sitePermutation.filter((j,k)=>j===k).length;
    const ci=r.classes.findIndex(c=>c.operationIndexes.includes(gi));
    near(r.totalCharacters[ci],fixed*central.totalCharacters[ci]);
  });
});
test('d validation rejects dependent copies, invalid components and bad local frames',()=>{
  const input=shell('Oh'); input.functions[0].component='dxx';code(()=>E.calculate(input),'invalid_d_component');
  input.functions[0].component='dxy';input.functions[0].frame=[[1,0,0],[0,1,0],[0,0,-1]];code(()=>E.calculate(input),'invalid_frame');
  input.functions[0].frame=[[2,0,0],[0,1,0],[0,0,1]];code(()=>E.calculate(input),'invalid_frame');
  input.functions[0].frame=undefined;input.functions.push({...input.functions[0],id:'duplicate'});code(()=>E.calculate(input),'dependent_basis');
  const two=shell('C1'); two.functions=[two.functions[0],{...two.functions[0],id:'second'}];code(()=>E.calculate(two),'dependent_basis');
});
test('adapter preserves separate cyclic/chiral classes and uses true axial matrices',()=>{
  for(const name of E.groupNames){const map=A.mapping(name);assert.equal(new Set(map.indices).size,reference[name].classes.length,name);}
  assert.equal(A.mapping('C7').indices.length,7);assert.equal(A.mapping('T').indices.length,4);
  const water=A.align(E.calculate(E.template('water')));assert.deepEqual(water.c,[2,0,2,0]);
});
function multiplicities(aligned,ref){
  return ref.X.map(row=>{
    let re=0,im=0;row.forEach((z,j)=>{const weight=ref.class_sizes[j]*aligned.c[j]/ref.h;re+=(typeof z==='number'?z:z.re)*weight;im-=(typeof z==='number'?0:z.im)*weight;});
    near(im,0);near(re,Math.round(re));assert(re> -1e-7);return Math.round(re);
  });
}
test('original complex tables validate all aligned d vectors and Oh Eg + T2g blocks',()=>{
  for(const name of E.groupNames){const aligned=A.align(E.calculate(shell(name)));multiplicities(aligned,reference[name]);}
  const a=A.align(E.calculate(shell('Oh'))), ref=reference.Oh, mult=multiplicities(a,ref);
  assert.deepEqual(ref.irreps.filter((_,i)=>mult[i]),['Eg','T2g']);
  a.blocks.forEach(b=>assert.equal(multiplicities({...a,c:b.c},ref).reduce((s,n)=>s+n,0),1));
  const benz=A.align(E.calculate(E.template('benzene')));multiplicities(benz,reference.D6h);
  benz.blocks.forEach(b=>multiplicities({...benz,c:b.c},reference.D6h));
});
test('alignment fails on altered result class metadata instead of silently reordering',()=>{
  const r=E.calculate(shell('D6h'));[r.classes[1],r.classes[2]]=[r.classes[2],r.classes[1]];
  assert.throws(()=>A.align(r),/类顺序/);
});
