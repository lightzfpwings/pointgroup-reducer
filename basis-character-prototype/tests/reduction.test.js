'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const R=require('../reduction-engine.js'),E=require('../engine.js'),A=require('../reducer-adapter.js');
const ref=require('./fixtures/integrated-reducer-reference.json').groups;
const near=(a,b)=>assert(R.abs(R.add(a,R.mul(-1,b)))<1e-7);
test('423 complete complex tables match original numeric entries, classes and irrep order',()=>{
  assert.equal(R.groupNames.length,423);
  for(const name of R.groupNames){const t=R.table(name),expected=ref[name];assert.deepEqual(t.classes,expected.classes);assert.deepEqual(t.sizes,expected.sizes);assert.deepEqual(t.irreps,expected.irreps);t.X.forEach((row,i)=>row.forEach((v,j)=>near(v,expected.X[i][j])));assert(t.orthogonalityError<1e-8);}
});
test('each original irreducible row reduces to exactly its own unit multiplicity vector',()=>{
  for(const name of R.groupNames){const expected=ref[name];expected.X.forEach((row,i)=>{const r=R.reduce(name,row);assert(r.valid,name);assert.deepEqual(r.integer_a,expected.irreps.map((_,j)=>i===j?1:0));assert(r.integer_residual<1e-7);});}
});
test('exact table display expressions evaluate to the same complex table numbers',()=>{
  for(const name of ['C3','C7','C12','C13','C60','S24','D6h','D5d','T','Th','Oh','Ih']){const t=R.table(name);t.expressions.forEach((row,i)=>row.forEach((s,j)=>near(R.number(s),t.X[i][j])));}
});
test('complex expression parser preserves precedence, conjugate signs and safe limits',()=>{
  near(R.number('-2^2'),-4);near(R.number('2^-2'),.25);near(R.number('2i'),{re:0,im:2});near(R.number('√3/2'),Math.sqrt(3)/2);near(R.number('-1/2+i*sqrt(3)/2'),{re:-.5,im:Math.sqrt(3)/2});
  near(R.number('sin(pi/2)'),1);near(R.number('cos(pi)'),-1);near(R.number('sqrt(-1)'),{re:0,im:1});
  for(const s of ['process.exit()','(()=>1)()','globalThis','1/0','NaN','Infinity','exp(1000)','2^101','('.repeat(100)+'1'+')'.repeat(100)])assert.throws(()=>R.number(s),R.ReductionError);
  assert.throws(()=>R.reduce('C1',[null]),R.ReductionError);assert.throws(()=>R.reduce('C1',[Infinity]),R.ReductionError);
});
test('manual complex C3 irrep is not merged into a real two-dimensional E row',()=>{
  const r=R.reduce('C3',R.parseVector('1, exp(2*pi*i/3), exp(4*pi*i/3)'));assert(r.valid);assert.equal(r.dimension,1);assert.deepEqual(r.terms,[{irrep:'E1+',multiplicity:1,dimension:1}]);
});
test('invalid and negative multiplicities remain invalid with no decomposition',()=>{
  for(const c of [[1,0,0,0],[-1,-1,-1,-1]]){const r=R.reduce('C2v',c);assert.equal(r.valid,false);assert.equal(r.integer_a,null);assert.deepEqual(r.terms,[]);}
  assert.throws(()=>R.reduce('C2v',[1,2]),R.ReductionError);assert.throws(()=>R.reduce('C1',[1],.01),R.ReductionError);
  assert.deepEqual(R.reduce('C1',[0]).terms,[]);
});
test('integrated molecular and d examples have expected decompositions and block sums',()=>{
  const oh=R.integrate(E.calculate(E.template('central-d-oh')),A);assert.deepEqual(oh.total.terms.map(t=>t.irrep),['Eg','T2g']);assert.deepEqual(oh.blocks.map(b=>b.dimension),[3,2]);
  const water=R.integrate(E.calculate(E.template('water')),A);assert.deepEqual(water.total.terms.map(t=>t.irrep),['A1','B1']);
  for(const name of ['benzene','water','central-c2v','central-oh','central-d-c2v','central-d-oh','icosahedron']){const r=R.integrate(E.calculate(E.template(name)),A);assert.equal(r.reductionIntegrated,true);r.total.integer_a.forEach((v,i)=>assert.equal(v,r.blocks.reduce((s,b)=>s+b.integer_a[i],0)));}
});
test('every supported geometric p/d shell passes integrated reduction',()=>{
  for(const group of E.groupNames)for(const name of ['central-c2v','central-d-oh']){const input=E.template(name);input.group=group;const r=R.integrate(E.calculate(input),A);assert(r.total.valid);}
});
