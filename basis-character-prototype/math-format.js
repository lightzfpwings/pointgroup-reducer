/* MathML 与 LaTeX 共用表达式树，保留数值含义，不通过字符串猜测根式。 */
(function(root){
  'use strict';
  const ns='http://www.w3.org/1998/Math/MathML';
  function node(tag,...children){const n=document.createElementNS(ns,tag);children.forEach(c=>{if(typeof c==='string')n.textContent=c;else n.append(c);});return n;}
  const row=(...items)=>node('mrow',...items);
  function mi(text,variant){const n=node('mi',text);if(variant)n.setAttribute('mathvariant',variant);return n;}
  const wrap=content=>{const n=node('math',content);n.setAttribute('display','inline');return n;};
  const fence=content=>row(node('mo','('),content,node('mo',')'));
  const scripts=(base,sub,sup)=>sub&&sup?node('msubsup',base,sub,sup):sub?node('msub',base,sub):sup?node('msup',base,sup):base;
  function parse(value){
    const text=String(value).replace(/−/g,'-').replace(/√/g,'sqrt').replace(/π/g,'pi').replace(/φ/g,'phi').replace(/\*\*/g,'^');
    if(text.length>2048)return null;
    const tokens=[];let offset=0,index=0,depth=0;
    while(offset<text.length){const m=/^\s*(?:(\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|([A-Za-z]+)|([()+\-*/^]))/.exec(text.slice(offset));if(!m){if(!text.slice(offset).trim())break;return null;}tokens.push(m[1]||m[2]||m[3]);offset+=m[0].length;if(tokens.length>256)return null;}
    const primary=()=>{if(++depth>40)throw Error('math');const t=tokens[index++];let a;
      if(t==='('){a=sum();if(tokens[index++]!==')')throw Error('math');}
      else if(/^(\d|\.)/.test(t||''))a={kind:'number',text:t};
      else if(['sqrt','cos','sin','exp'].includes(t)){
        let arg;if(tokens[index]==='('){index++;arg=sum();if(tokens[index++]!==')')throw Error('math');}else if(t==='sqrt')arg=primary();else throw Error('math');a={kind:'call',name:t,arg};
      }else if(t&&/^[A-Za-z]+$/.test(t))a={kind:'symbol',text:t};else throw Error('math');depth--;return a;};
    const power=()=>{let a=primary();if(tokens[index]==='^'){index++;a={kind:'binary',op:'^',left:a,right:unary()};}return a;};
    const unary=()=>tokens[index]==='+'||tokens[index]==='-'?{kind:'unary',op:tokens[index++],arg:unary()}:power();
    const term=()=>{let a=unary();while(index<tokens.length){if(tokens[index]==='*'||tokens[index]==='/'){const op=tokens[index++];a={kind:'binary',op,left:a,right:unary()};}else if(tokens[index]==='('||/^[A-Za-z]/.test(tokens[index]))a={kind:'binary',op:'*',left:a,right:unary()};else break;}return a;};
    const sum=()=>{let a=term();while(tokens[index]==='+'||tokens[index]==='-')a={kind:'binary',op:tokens[index++],left:a,right:term()};return a;};
    try{const a=sum();return index===tokens.length?normalize(a):null;}catch(_){return null;}
  }
  function sign(a){return a.kind==='unary'?{negative:a.op==='-',positive:a.arg}:{negative:false,positive:a};}
  function normalize(a){
    if(a.kind==='unary'){const arg=normalize(a.arg);if(a.op==='+')return arg;if(arg.kind==='unary')return arg.arg;return {...a,arg};}
    if(a.kind==='call')return {...a,arg:normalize(a.arg)};
    if(a.kind!=='binary')return a;
    let left=normalize(a.left),right=normalize(a.right);
    if(a.op==='*'||a.op==='/'){const l=sign(left),r=sign(right),b={...a,left:l.positive,right:r.positive};return l.negative!==r.negative?{kind:'unary',op:'-',arg:b}:b;}
    if((a.op==='+'||a.op==='-')&&right.kind==='unary')return {...a,op:a.op==='+'?'-':'+',left,right:right.arg};
    return {...a,left,right};
  }
  const precedence=a=>a.kind==='binary'?a.op==='+'||a.op==='-'?1:a.op==='*'?2:4:a.kind==='unary'?3:5;
  function numberNode(text){
    const m=/^(.+)[eE]([+-]?\d+)$/.exec(text);
    if(!m)return node('mn',text);
    const exponent=String(Number(m[2]));return row(node('mn',m[1]),node('mo','×'),node('msup',node('mn','10'),exponent.startsWith('-')?row(node('mo','−'),node('mn',exponent.slice(1))):node('mn',exponent)));
  }
  function render(a,parent=0){
    let out;
    if(a.kind==='number')out=numberNode(a.text);
    else if(a.kind==='symbol')out=mi(a.text==='pi'?'π':a.text==='phi'?'φ':a.text==='I'?'i':a.text,['pi','i','I','e'].includes(a.text)?'normal':undefined);
    else if(a.kind==='call')out=a.name==='sqrt'?node('msqrt',render(a.arg)):row(mi(a.name,'normal'),node('mo','\u2061'),fence(render(a.arg)));
    else if(a.kind==='unary')out=row(node('mo','−'),render(a.arg,3));
    else if(a.op==='/')out=node('mfrac',render(a.left),render(a.right));
    else if(a.op==='^')out=node('msup',render(a.left,4),render(a.right));
    else if(a.op==='*')out=row(render(a.left,2),node('mo','\u2062'),render(a.right,2));
    else out=row(render(a.left,1),node('mo',a.op==='-'?'−':'+'),render(a.right,a.op==='-'?2:1));
    return precedence(a)<parent||a.kind==='number'&&/[eE]/.test(a.text)&&parent>=4?fence(out):out;
  }
  function expression(value){const a=parse(value);return wrap(a?render(a):node('mtext',String(value)));}
  function numberText(value){
    const v=typeof value==='number'?{re:value,im:0}:value;
    const fmt=x=>Object.is(x,-0)?'0':Number(x.toPrecision(10)).toString();
    if(v.im===0||v.im===undefined)return fmt(v.re);
    return (v.re!==0?fmt(v.re)+(v.im<0?'-':'+'):'')+(v.im<0&&v.re===0?'-':'')+(Math.abs(v.im)===1?'':fmt(Math.abs(v.im))+'*')+'i';
  }
  const number=value=>expression(numberText(value));
  function orientation(rest){
    const match=/^\(phi=(.+)\)$/.exec(rest);
    return match?fence(row(mi('φ'),node('mo','='),parse(match[1])?render(parse(match[1])):node('mtext',match[1]))):node('mtext',rest.replace(/pi/g,'π').replace(/phi/g,'φ'));
  }
  function labelContent(value){
    const s=String(value);
    if(s.includes('·'))return row(...s.split('·').flatMap((part,i)=>i?[node('mo','·'),labelContent(part)]:[labelContent(part)]));
    const sigma=/^sigma(?:_([a-z]+))?(.*)$/.exec(s);
    if(sigma)return row(scripts(mi('σ'),sigma[1]?node('mtext',sigma[1]):null,null),orientation(sigma[2]));
    if(['Cs','Ci','Th','Td','Oh','Ih'].includes(s))return scripts(mi(s[0]),node('mtext',s.slice(1)),null);
    const op=/^([CDS])(\d+)([vhd]?)([′″']*)(?:\^(\d+))?(.*)$/.exec(s);
    if(op){const [,base,n,suffix,prime,power,rawRest]=op;const handed=/^\(([+-])\)$/.exec(rawRest),rest=handed?'':rawRest;
      const sup=(power||'')+prime.replace(/'/g,'′')+(handed?handed[1].replace('-','−'):'');
      return row(scripts(mi(base),node('mtext',n+suffix),sup?node('mtext',sup):null),orientation(rest));
    }
    const irrep=/^([ABETGHR])(\d*)([+-]?)(g|u|'+)?$/.exec(s);
    if(irrep){const [,base,n,sign,suffix]=irrep,sub=n+(suffix&&!suffix.startsWith("'")?suffix:''),sup=sign.replace('-','−')+(suffix?.startsWith("'")?suffix.replace(/'/g,'′'):'');return scripts(mi(base),sub?node('mtext',sub):null,sup?node('mtext',sup):null);}
    if(['E','i','T','O','I'].includes(s))return mi(s,s==='i'?'normal':undefined);
    return node('mtext',s);
  }
  const label=value=>wrap(labelContent(value));
  function orbitalContent(axis,prefix=''){
    let f;if(axis==='s')f=mi('s');else if(/^p[xyz]$/.test(axis))f=scripts(mi('p'),mi(axis.slice(1)),null);
    else if(['dxy','dxz','dyz'].includes(axis))f=scripts(mi('d'),row(...[...axis.slice(1)].map(c=>mi(c))),null);
    else if(axis==='dx2-y2')f=scripts(mi('d'),row(node('msup',mi('x'),node('mn','2')),node('mo','−'),node('msup',mi('y'),node('mn','2'))),null);
    else if(axis==='dz2')f=scripts(mi('d'),node('msup',mi('z'),node('mn','2')),null);
    else f=node('mtext',axis);
    return prefix?row(node('mtext',String(prefix)),f):f;
  }
  function basisContent(text){
    const matches=String(text).split(' + ');if(matches.length>1)return row(...matches.flatMap((v,i)=>i?[node('mo','+'),basisContent(v)]:[basisContent(v)]));
    const match=/^(.*\s)(.*?)(dx2-y2|dxy|dxz|dyz|dz2|px|py|pz|s)(\s*\[.*\])?$/.exec(String(text));
    return match?row(node('mtext',match[1]),orbitalContent(match[3],match[2]),node('mtext',match[4]||'')):node('mtext',String(text));
  }
  const basisLabel=text=>wrap(basisContent(text));
  function decomposition(result){const content=[mi('Γ'),node('mo','=')];result.terms.forEach((term,i)=>{if(i)content.push(node('mo','+'));if(term.multiplicity!==1)content.push(node('mn',String(term.multiplicity)));content.push(labelContent(term.irrep));});if(!result.terms.length)content.push(node('mn','0'));return wrap(row(...content));}
  // 星号是逐项复共轭，不是伴随转置；X 的行是不可约表示、列是共轭类。
  function formula(){return wrap(row(mi('a','bold'),node('mo','='),node('mfrac',node('mn','1'),mi('h')),node('msup',mi('X','bold'),node('mo','∗')),mi('W','bold'),mi('c','bold')));}
  function plainLabel(value){const sub='₀₁₂₃₄₅₆₇₈₉',sup='⁰¹²³⁴⁵⁶⁷⁸⁹';return String(value).replace(/^(C)([si])$/,(_,a,s)=>a+(s==='s'?'ₛ':'ᵢ')).replace(/^([CDS])(\d+)([vhd]?)/,(_,a,n,suffix)=>a+[...n].map(c=>sub[Number(c)]).join('')+suffix.replace(/v/g,'ᵥ').replace(/h/g,'ₕ').replace(/d/g,'ᵈ')).replace(/^(T|O|I)([hd])$/,(_,a,s)=>a+(s==='h'?'ₕ':'ᵈ')).replace(/\^(\d+)/g,(_,n)=>[...n].map(c=>sup[Number(c)]).join('')).replace(/sigma_h/g,'σₕ').replace(/sigma_v/g,'σᵥ').replace(/sigma_d/g,'σᵈ').replace(/sigma/g,'σ').replace(/phi/g,'φ').replace(/pi/g,'π').replace(/'/g,'′');}
  function latexLabel(value){
    const s=String(value);if(['Cs','Ci','Th','Td','Oh','Ih'].includes(s))return s[0]+'_{\\mathrm{'+s.slice(1)+'}}';
    const group=/^([CDS])(\d+)([vhd]?)$/.exec(s);if(group)return group[1]+'_{'+group[2]+(group[3]?'\\mathrm{'+group[3]+'}':'')+'}';
    const irrep=/^([ABETGHR])(\d*)([+-]?)(g|u|'+)?$/.exec(s);if(irrep){const [,base,n,sign,suffix]=irrep;return base+(n||suffix&&!suffix.startsWith("'")?'_{'+n+(suffix&&!suffix.startsWith("'")?'\\mathrm{'+suffix+'}':'')+'}':'')+(sign?'^{'+sign+'}':'')+(suffix?.startsWith("'")?suffix:'');}return s;
  }
  function latexExpression(value){const a=parse(value);if(!a)return String(value);function out(n,parent=0){let s;
    if(n.kind==='number'){const m=/^(.+)[eE]([+-]?\d+)$/.exec(n.text);s=m?m[1]+'\\times 10^{'+Number(m[2])+'}':n.text;}
    else if(n.kind==='symbol')s=['pi','phi'].includes(n.text)?'\\'+n.text:n.text==='i'||n.text==='I'?'\\mathrm{i}':n.text==='e'?'\\mathrm{e}':n.text;
    else if(n.kind==='call')s=n.name==='sqrt'?'\\sqrt{'+out(n.arg)+'}':'\\'+n.name+'\\left('+out(n.arg)+'\\right)';
    else if(n.kind==='unary')s='-'+out(n.arg,3);
    else if(n.op==='/')s='\\frac{'+out(n.left)+'}{'+out(n.right)+'}';
    else if(n.op==='^')s='{'+out(n.left,4)+'}^{'+out(n.right)+'}';
    else if(n.op==='*')s=out(n.left,2)+' '+out(n.right,2);
    else s=out(n.left,1)+(n.op==='-'?'-':'+')+out(n.right,n.op==='-'?2:1);
    return precedence(n)<parent||n.kind==='number'&&/[eE]/.test(n.text)&&parent>=4?'\\left('+s+'\\right)':s;
  }return out(a);}
  const api={label,expression,number,numberText,decomposition,formula,plainLabel,orbital:(axis,prefix)=>wrap(orbitalContent(axis,prefix)),basisLabel,component:(symbol,index)=>wrap(scripts(mi(symbol),mi(index),null)),latexLabel,latexExpression};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;root.MathFormat=api;
})(typeof globalThis!=='undefined'?globalThis:this);
