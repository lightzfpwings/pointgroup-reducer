/* 数学语义与节点结构回归检查；不声称验证了浏览器视觉渲染。 */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const R=require('../reduction-engine.js');
function formatter(){
  class Node{constructor(tag){this.tag=tag;this.children=[];this.attributes={};this.text='';}append(...nodes){this.children.push(...nodes);}set textContent(value){this.text=String(value);this.children=[];}get textContent(){return this.text+this.children.map(n=>n.textContent).join('');}setAttribute(key,value){this.attributes[key]=value;}}
  const context={document:{createElementNS:(_,tag)=>new Node(tag)}};vm.createContext(context);vm.runInContext(fs.readFileSync(require.resolve('../math-format.js'),'utf8'),context);return context.MathFormat;
}
const walk=n=>[n,...n.children.flatMap(walk)];
function arithmetic(n){
  if(n.tag==='mfrac')return '(('+arithmetic(n.children[0])+')/('+arithmetic(n.children[1])+'))';
  if(n.tag==='msqrt')return 'sqrt('+arithmetic(n.children[0])+')';
  if(n.tag==='msup')return '(('+arithmetic(n.children[0])+')^('+arithmetic(n.children[1])+'))';
  if(n.tag==='mi')return {π:'pi',φ:'phi'}[n.text]||n.text;
  if(n.tag==='mo')return {'−':'-','×':'*','\u2062':'*','\u2061':''}[n.text]??n.text;
  if(n.tag==='mn'||n.tag==='mtext')return n.text;
  return n.children.map(arithmetic).join('');
}
test('fraction/root/sign formatting preserves character-table values across group families',()=>{
  const M=formatter();for(const name of ['C3','C7','C12','C13','C60','S24','D6h','D5d','T','Th','Oh','Ih']){
    const table=R.table(name);table.expressions.forEach((row,i)=>row.forEach((s,j)=>{
      const tree=M.expression(s);assert(!walk(tree).some(n=>n.tag==='mtext'),s);const value=R.number(arithmetic(tree));assert(R.abs(R.add(value,R.mul(-1,table.X[i][j])))<1e-7,name+' '+s);
    }));
  }
});
test('negative powers, implicit products and subtraction retain their mathematical meaning',()=>{
  const M=formatter();for(const text of ['(-2)^2','-2^2','2^-2','2i','2(pi/3)','sqrt(3)/2','(-1/2)+(-sqrt(3)/2)*i','1-(2-3)','-(-1/2)']){
    const tree=M.expression(text);assert(!walk(tree).some(n=>n.tag==='mtext'),text);assert(R.abs(R.add(R.number(arithmetic(tree)),R.mul(-1,R.number(text))))<1e-9,text);
  }
  assert(!walk(M.expression('(-1/2)+(-sqrt(3)/2)*i')).some(n=>n.tag==='mo'&&n.text==='('));
});
test('scientific notation and small nonzero numbers use proper powers without becoming zero',()=>{
  const M=formatter();for(const value of [1e-12,-2.5e-9,3e21]){const tree=M.number(value);assert(walk(tree).some(n=>n.tag==='msup'));assert(walk(tree).some(n=>n.tag==='mo'&&n.text==='×'));assert(Math.abs(R.number(arithmetic(tree))/value-1)<1e-9);}
  assert.equal(M.numberText(1.00000001),'1.00000001');
  const power=walk(M.expression('1e-7^2')).find(n=>n.tag==='msup');assert.equal(power.children[0].children[0].textContent,'(');
  assert(M.latexExpression('1e-7^2').includes('\\left(1\\times 10^{-7}\\right)'));
});
test('group symbols, class handedness, primes and simultaneous scripts are distinct',()=>{
  const M=formatter();assert.equal(walk(M.label('Ci')).find(n=>n.tag==='msub').children[1].textContent,'i');
  assert.equal(walk(M.label('Cs')).find(n=>n.tag==='msub').children[1].textContent,'s');
  assert(walk(M.label('C4^3')).some(n=>n.tag==='msubsup'));
  assert.equal(walk(M.label('C3(-)')).find(n=>n.tag==='msubsup').children[2].textContent,'−');
  assert.equal(walk(M.label('E1+g')).find(n=>n.tag==='msubsup').children[1].textContent,'1g');
  assert.equal(walk(M.label("C2''(phi=5*pi/12)")).find(n=>n.tag==='msubsup').children[2].textContent,'′′');
  assert(walk(M.label('sigma_d(phi=pi/6)')).some(n=>n.tag==='mfrac'));
});
test('orbital components are subscripted, with squares nested inside the d subscript',()=>{
  const M=formatter();for(const axis of ['px','py','pz','dxy','dxz','dyz','dx2-y2','dz2'])assert(walk(M.orbital(axis)).some(n=>n.tag==='msub'));
  const d=walk(M.orbital('dx2-y2')).find(n=>n.tag==='msub');assert.equal(walk(d.children[1]).filter(n=>n.tag==='msup').length,2);
  assert.equal(walk(M.component('u','z')).find(n=>n.tag==='msub').children[1].textContent,'z');
});
test('matrix reduction uses bold a/X/W/c and elementwise conjugation without a transpose',()=>{
  const nodes=walk(formatter().formula());assert.deepEqual(nodes.filter(n=>n.tag==='mi'&&n.attributes.mathvariant==='bold').map(n=>n.text),['a','X','W','c']);
  assert.equal(nodes.find(n=>n.tag==='msup').children[1].textContent,'∗');assert(!nodes.some(n=>n.text==='†'||n.text==='T'));
});
test('LaTeX has matching group and irrep scripts, scientific notation and imaginary unit',()=>{
  const M=formatter();assert.equal(M.latexLabel('Oh'),'O_{\\mathrm{h}}');assert.equal(M.latexLabel('Ci'),'C_{\\mathrm{i}}');assert.equal(M.latexLabel('E1+g'),'E_{1\\mathrm{g}}^{+}');assert.equal(M.latexLabel("A''"),"A''");
  assert.equal(M.latexExpression('1e-7'),'1\\times 10^{-7}');assert.equal(M.latexExpression('2i'),'2 \\mathrm{i}');assert.equal(M.latexExpression('sqrt(3)/2'),'\\frac{\\sqrt{3}}{2}');
});
test('unsupported punctuation is retained as text instead of silently changing an expression',()=>{
  const M=formatter();for(const value of ['2<+3','1%2','x&y']){const tree=M.expression(value);assert.equal(tree.textContent,value);assert(walk(tree).some(n=>n.tag==='mtext'));}
});
