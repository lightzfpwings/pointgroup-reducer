/* 原 Table.reduce 的独立数值实现；完整复不可约表，不合并复共轭行。 */
(function(root) {
  'use strict';
  const catalog=typeof module!=='undefined'&&module.exports?require('./reduction-catalog.js'):root.ReductionCatalog;
  class ReductionError extends Error { constructor(code,detail={}){super(code);this.name='ReductionError';this.code=code;this.detail=detail;} }
  const fail=(code,detail)=>{throw new ReductionError(code,detail);};
  const z=a=>typeof a==='number'?{re:a,im:0}:a;
  const pack=a=>a.im===0?a.re:a;
  const add=(a,b)=>{a=z(a);b=z(b);return pack({re:a.re+b.re,im:a.im+b.im});};
  const mul=(a,b)=>{a=z(a);b=z(b);return pack({re:a.re*b.re-a.im*b.im,im:a.re*b.im+a.im*b.re});};
  const conj=a=>{a=z(a);return pack({re:a.re,im:-a.im});};
  const abs=a=>{a=z(a);return Math.hypot(a.re,a.im);};
  function div(a,b){
    a=z(a);b=z(b);
    if(!finite(a)||!finite(b))fail('invalid_expression');
    if(b.im===0){
      if(b.re===0)fail('invalid_expression');
      return pack({re:a.re/b.re,im:a.im/b.re});
    }
    // Power-of-two scaling keeps both squared magnitudes and intermediate sums
    // representable, including when both complex operands are subnormal.
    const exponent=v=>Math.min(1023,Math.floor(Math.log2(Math.max(Math.abs(v.re),Math.abs(v.im)))));
    if(a.re===0&&a.im===0)return 0;
    const ae=exponent(a),be=exponent(b),as=2**ae,bs=2**be;
    const ar=a.re/as,ai=a.im/as,br=b.re/bs,bi=b.im/bs,d=br*br+bi*bi;
    const shift=ae-be,first=Math.max(-1022,Math.min(1023,shift));
    const scale=x=>x===0?0:(x*2**first)*2**(shift-first);
    return pack({re:scale((ar*br+ai*bi)/d),im:scale((ai*br-ar*bi)/d)});
  }
  const exp=a=>{a=z(a);return pack({re:Math.exp(a.re)*Math.cos(a.im),im:Math.exp(a.re)*Math.sin(a.im)});};
  const log=a=>{a=z(a);if(!abs(a))fail('invalid_expression');return {re:Math.log(abs(a)),im:Math.atan2(a.im,a.re)};};
  function power(a,b){
    a=z(a);b=z(b);
    if(!finite(a)||!finite(b))fail('invalid_expression');
    if(abs(b)>100)fail('expression_limit');
    if(a.re===0&&a.im===0){
      if(b.im||b.re<0)fail('invalid_expression');
      return b.re===0?1:0;
    }
    if(b.im===0){
      if(a.im===0&&(a.re>=0||Number.isInteger(b.re)))return a.re**b.re;
      if(a.im===0&&b.re===0.5)return {re:0,im:Math.sqrt(-a.re)};
      if(Number.isInteger(b.re)){
        let base=b.re<0?div(1,a):a, result=1;
        for(let n=Math.abs(b.re);n>0;n=Math.floor(n/2)){
          if(n%2)result=mul(result,base);
          if(n>1)base=mul(base,base);
        }
        return result;
      }
    }
    return exp(mul(b,log(a)));
  }
  const gcd=(a,b)=>b?gcd(b,a%b):a;
  function cosine(p,q){p=((p%(2*q))+2*q)%(2*q);const d=gcd(p,q);p/=d;q/=d;return catalog.cosines[p+'/'+q]||'cos('+ (p===1?'':p+'*')+'π/'+q+')';}
  const negExpr=s=>s==='0'?'0':'-('+s+')';
  function unitExpression(p,n){
    const a=cosine(2*p,n),b=cosine(n-4*p,2*n);
    if(b==='0')return a;if(a==='0')return b==='1'?'i':b==='-1'?'-i':'('+b+')*i';
    return '('+a+')+('+b+')*i';
  }
  function cyclic(n){
    const order=[0,...(n%2===0?[n/2]:[])];for(let k=1;k<Math.floor((n+1)/2);k++)order.push(k,n-k);
    return {X:order.map(k=>Array.from({length:n},(_,p)=>{
      const phase=(k*p)%n;
      if(phase===0)return 1;
      if(2*phase===n)return -1;
      return {re:(4*phase)%n===0?0:Math.cos(2*Math.PI*phase/n),im:Math.sin(2*Math.PI*phase/n)};
    })),
      expressions:order.map(k=>Array.from({length:n},(_,p)=>unitExpression(k*p,n)))};
  }
  function dihedral(n,vertical){
    const powers=Array.from({length:Math.floor(n/2)+1},(_,i)=>i),js=n%2===0?[0,1]:[0];
    let X=[];
    for(const [a,b] of [[1,1],[1,-1],...(n%2===0?[[-1,1],[-1,-1]]:[])])X.push([...powers.map(p=>a**p),...js.map(j=>a**j*b)]);
    let expressions=X.map(row=>row.map(String));
    for(let k=1;k<Math.floor((n+1)/2);k++){
      X.push([...powers.map(p=>2*Math.cos(2*Math.PI*k*p/n)),...js.map(()=>0)]);
      expressions.push([...powers.map(p=>{const c=cosine(2*k*p,n);return ['0','1','-1'].includes(c)?String(2*Number(c)):'2*('+c+')';}),...js.map(()=>'0')]);
    }
    if(n===2&&!vertical){const order=[0,1,3,2];X=order.map(i=>X[i]);expressions=order.map(i=>expressions[i]);}
    return {X,expressions};
  }
  function product(base){return {X:[...base.X.map(row=>[...row,...row]),...base.X.map(row=>[...row,...row.map(v=>mul(-1,v))])],
    expressions:[...base.expressions.map(row=>[...row,...row]),...base.expressions.map(row=>[...row,...row.map(negExpr)])]};}
  function recipe(name){
    if(catalog.explicit[name])return catalog.explicit[name];
    const [,family,nText,suffix]=name.match(/^([CDS])(\d+)([vhd]?)$/)||[];const n=Number(nText);
    if(family==='S')return cyclic(n);
    if(family==='C')return suffix==='h'?product(cyclic(n)):suffix==='v'?dihedral(n,true):cyclic(n);
    if(family==='D')return suffix==='h'||suffix==='d'&&n%2?product(dihedral(n,false)):dihedral(suffix==='d'?2*n:n,false);
    fail('unsupported_reducer_group');
  }
  const cache=new Map();
  function table(name){
    if(cache.has(name))return cache.get(name);
    if(typeof name!=='string'||!Object.prototype.hasOwnProperty.call(catalog.groups,name))fail('unsupported_reducer_group');
    const meta=catalog.groups[name];
    const r={...meta,...recipe(name)};const n=r.classes.length;
    if(r.X.length!==n||r.X.some(row=>row.length!==n))fail('table_shape');
    let error=0;
    for(let i=0;i<n;i++)for(let k=0;k<=i;k++){
      let value=0;for(let j=0;j<n;j++)value=add(value,mul(r.sizes[j]/r.h,mul(conj(r.X[i][j]),r.X[k][j])));
      error=Math.max(error,abs(add(value,i===k?-1:0)));
    }
    if(error>1e-8)fail('table_orthogonality',{error});
    r.orthogonalityError=error;cache.set(name,r);return r;
  }
  function finite(a){const v=z(a);return typeof v.re==='number'&&typeof v.im==='number'&&Number.isFinite(v.re)&&Number.isFinite(v.im);}
  function reduce(name,c,tol=1e-7){
    const t=table(name);if(!Number.isFinite(tol)||tol<=0||tol>=.01)fail('invalid_reduction_tolerance');
    if(!Array.isArray(c)||c.length!==t.classes.length)fail('character_count',{expected:t.classes.length});
    if(!Array.from(c).every(v=>(typeof v==='number'||v&&typeof v==='object')&&finite(v)))fail('nonfinite_characters');
    const a=t.X.map(row=>row.reduce((sum,v,j)=>add(sum,mul(t.sizes[j]/t.h,mul(conj(v),c[j]))),0));
    const nearest=a.map(v=>Math.round(z(v).re)||0);
    const integral=a.every((v,i)=>Number.isSafeInteger(nearest[i])&&nearest[i]>=0&&abs(add(v,-nearest[i]))<=tol);
    const recovered=t.classes.map((_,j)=>t.X.reduce((sum,row,i)=>add(sum,mul(row[j],a[i])),0));
    const rounded=t.classes.map((_,j)=>t.X.reduce((sum,row,i)=>add(sum,mul(row[j],nearest[i])),0));
    const residual=Math.max(...c.map((v,j)=>abs(add(recovered[j],mul(-1,v))))),integerResidual=Math.max(...c.map((v,j)=>abs(add(rounded[j],mul(-1,v)))));
    const valid=integral&&integerResidual<=tol;
    return {point_group:name,c:c.map(v=>pack(z(v))),a,integer_a:valid?nearest:null,valid,reconstructed_c:recovered,residual,integer_residual:integerResidual,dimension:c[0],tolerance:tol,
      terms:valid?t.irreps.flatMap((irrep,i)=>nearest[i]?[{irrep,multiplicity:nearest[i],dimension:z(t.X[i][0]).re}]:[]):[]};
  }
  function integrate(basisResult,adapter){
    const aligned=adapter.align(basisResult),total=reduce(aligned.point_group,aligned.c);
    const blocks=aligned.blocks.map(b=>({...b,...reduce(aligned.point_group,b.c)}));
    if(!total.valid||blocks.some(b=>!b.valid))fail('integration_invalid');
    const t=table(aligned.point_group),sum=total.integer_a.map((_,i)=>blocks.reduce((n,b)=>n+b.integer_a[i],0));
    if(sum.some((v,i)=>v!==total.integer_a[i]))fail('integration_sum');
    return {schemaVersion:1,reductionIntegrated:true,point_group:aligned.point_group,classes:t.classes,class_sizes:t.sizes,irreps:t.irreps,total,blocks,mapping:aligned.mapping,provenance:catalog.provenance};
  }
  function payload(name){const t=table(name);return {schema_version:1,point_group:name,h:t.h,classes:t.classes,class_sizes:t.sizes,W:t.sizes.map((v,i)=>t.sizes.map((_,j)=>i===j?v:0)),irreps:t.irreps,X:t.X,X_symbolic:t.expressions,formula:'a = X.conj() @ W @ c / h',orthogonality_error:t.orthogonalityError};}
  // 有界递归下降解析器，不调用 eval、Function 或外部符号求值。
  function number(text){
    if(typeof text!=='string'||text.length>256)fail('expression_limit');
    text=text.replace(/−/g,'-').replace(/π/g,'pi').replace(/√/g,'sqrt').replace(/\*\*/g,'^');
    const tokens=[];let offset=0;
    while(offset<text.length){const match=/^\s*(?:(\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|([A-Za-z]+)|([()+\-*/^]))/.exec(text.slice(offset));if(!match){if(!text.slice(offset).trim())break;fail('invalid_expression');}tokens.push(match[1]||match[2]||match[3]);offset+=match[0].length;}
    if(!tokens.length||tokens.length>80)fail('expression_limit');let i=0,depth=0;
    const primary=()=>{if(++depth>40)fail('expression_limit');const token=tokens[i++];let value;
      if(token==='('){value=sum();if(tokens[i++]!==')')fail('invalid_expression');}
      else if(/^(\d|\.)/.test(token||''))value=Number(token);
      else if(['i','j','pi','e'].includes(token))value=token==='i'||token==='j'?{re:0,im:1}:token==='pi'?Math.PI:Math.E;
      else if(['sqrt','exp','cos','sin'].includes(token)){
        let arg;if(tokens[i]==='('){i++;arg=sum();if(tokens[i++]!==')')fail('invalid_expression');}else if(token==='sqrt')arg=primary();else fail('invalid_expression');
        const v=z(arg);
        value=token==='sqrt'?power(arg,.5):token==='exp'?exp(arg):token==='cos'?pack({re:Math.cos(v.re)*Math.cosh(v.im),im:-Math.sin(v.re)*Math.sinh(v.im)}):pack({re:Math.sin(v.re)*Math.cosh(v.im),im:Math.cos(v.re)*Math.sinh(v.im)});
      }else fail('invalid_expression');if(!finite(value))fail('invalid_expression');depth--;return value;};
    const pow=()=>{let a=primary();if(tokens[i]==='^'){i++;a=power(a,unary());}return a;};
    const unary=()=>{if(tokens[i]==='+'||tokens[i]==='-'){const sign=tokens[i++];return mul(sign==='-'?-1:1,unary());}return pow();};
    const term=()=>{let a=unary();while(i<tokens.length){if(tokens[i]==='*'||tokens[i]==='/'){const op=tokens[i++];a=op==='*'?mul(a,unary()):div(a,unary());}else if(tokens[i]==='('||/^[A-Za-z]/.test(tokens[i]))a=mul(a,unary());else break;}return a;};
    const sum=()=>{let a=term();while(tokens[i]==='+'||tokens[i]==='-'){const op=tokens[i++];a=add(a,mul(op==='-'?-1:1,term()));}return a;};
    const result=sum();if(i!==tokens.length||!finite(result))fail('invalid_expression');return pack(z(result));
  }
  function parseVector(text){const parts=/[,;，；]/.test(text)?text.split(/[,;，；]/):text.trim().split(/\s+/);if(parts.some(p=>!p.trim()))fail('invalid_expression');return parts.map(number);}
  const api={VERSION:'0.7.0',ReductionError,groupNames:catalog.names,table,reduce,integrate,payload,number,parseVector,z,add,mul,conj,abs};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;root.ReductionEngine=api;
})(typeof globalThis!=='undefined'?globalThis:this);
