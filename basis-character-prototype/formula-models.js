/* Offline structure candidates indexed by elemental composition and ionic charge. */
(function (root) {
  'use strict';
  const commonJS = typeof module !== 'undefined' && module.exports;
  const E = commonJS ? require('./engine.js') : root.BasisEngine;
  const S = commonJS ? require('./structure.js') : root.MolecularStructure;
  const library = commonJS ? require('./structure-library.js') : root.StructureLibrary;
  const invalid = '请输入化学式，注意元素符号大小写。离子示例 [Fe(CN)6]4-。';
  const subscripts = '₀₁₂₃₄₅₆₇₈₉', superscripts = '⁰¹²³⁴⁵⁶⁷⁸⁹';

  function parseFormula(input) {
    if (typeof input !== 'string' || input.length > 512) throw new Error(invalid);
    let text = input.trim().replace(/[₀-₉]/g, c => subscripts.indexOf(c)).replace(/−/g, '-')
      .replace(/([⁰¹²³⁴⁵⁶⁷⁸⁹]*)([⁺⁻])$/, (_, digits, sign) =>
        '^' + Array.from(digits, c => superscripts.indexOf(c)).join('') + (sign === '⁺' ? '+' : '-'));
    // Digits after ] or ^ denote charge. In NH4+ the 4 remains a subscript.
    const suffix = /(\]|\^)([1-9]\d?)?([+-])$/.exec(text);
    let charge = 0;
    if (suffix) {
      charge = Number(suffix[2] || 1) * (suffix[3] === '+' ? 1 : -1);
      text = text.slice(0, suffix.index + (suffix[1] === ']' ? 1 : 0));
    } else if (/[+-]$/.test(text)) {
      charge = text.endsWith('+') ? 1 : -1;
      text = text.slice(0, -1);
    }
    if (text.startsWith('[') && text.endsWith(']')) text = text.slice(1, -1);
    const groups = [new Map()];
    const token = /\s*([A-Z][a-z]?|\(|\))(\d*)/gy;
    for (let offset = 0; offset < text.length; offset = token.lastIndex) {
      const match = token.exec(text);
      if (!match) throw new Error(invalid);
      const [, symbol, suffix] = match;
      if (suffix.startsWith('0') || (symbol === '(' && suffix)) throw new Error(invalid);
      if (symbol === '(') { groups.push(new Map()); continue; }
      const multiple = suffix ? Number(suffix) : 1;
      let terms;
      if (symbol === ')') {
        if (groups.length === 1) throw new Error(invalid);
        terms = groups.pop();
        if (!terms.size) throw new Error(invalid);
      } else {
        if (!S.isElement(symbol)) throw new E.BasisError('formula_element', '无法识别化学式中的元素。', {symbol});
        terms = [[symbol, 1]];
      }
      const current = groups[groups.length - 1];
      for (const [kind, n] of terms) current.set(kind, (current.get(kind) || 0) + n * multiple);
      if ([...current.values()].reduce((a, b) => a + b, 0) > 120) throw new Error('每个分子最多支持 120 个原子。');
    }
    if (groups.length !== 1 || !groups[0].size) throw new Error(invalid);
    return {counts:groups[0], charge};
  }

  function chargeSuffix(charge, display = false) {
    if (!charge) return '';
    const n = Math.abs(charge), digits = n === 1 ? '' : String(n);
    return display ? Array.from(digits, c => superscripts[c]).join('') + (charge > 0 ? '⁺' : '⁻')
      : digits + (charge > 0 ? '+' : '-');
  }

  function speciesDisplay(formula) {
    const end = /\]([1-9]\d?)?([+-])$/.exec(formula);
    const composition = end ? formula.slice(0, end.index + 1) : formula;
    return composition.replace(/\d/g, digit => subscripts[digit]) +
      (end ? chargeSuffix(Number(end[1] || 1) * (end[2] === '+' ? 1 : -1), true) : '');
  }

  const ethanol = [
    ['C',1.1879,-0.3829,0], ['C',0,0.5526,0], ['O',-1.1867,-0.2472,0],
    ['H',-1.9237,0.3850,0], ['H',2.0985,0.2306,0], ['H',1.1184,-1.0093,0.8869],
    ['H',1.1184,-1.0093,-0.8869], ['H',-0.0227,1.1812,0.8852], ['H',-0.0227,1.1812,-0.8852]
  ];
  const ether = [
    ['O',0,0,0.5952], ['C',0,1.1669,-0.1963], ['C',0,-1.1669,-0.1963],
    ['H',0,2.0489,0.4542], ['H',0,-2.0489,0.4542], ['H',0.8950,1.1787,-0.8287],
    ['H',-0.8950,1.1787,-0.8287], ['H',-0.8950,-1.1787,-0.8287], ['H',0.8950,-1.1787,-0.8287]
  ];

  function model(id, name, group, atoms, cas) {
    const sites = atoms.map(([kind, x, y, z], i) => ({id:kind + (i + 1), kind, position:[x,y,z]}));
    const data = {id, name, group, geometry:cas ? 'NIST 参考几何' : '理想化几何', sites};
    if (cas) data.sourceURL = 'https://cccbdb.nist.gov/exp2x.asp?casno=' + cas + '&charge=0';
    return data;
  }

  // Each orientation puts the subgroup axes in the convention of engine.js.
  // Lengths (Å) are representative single bonds; these models are idealized.
  const lengths = {
    C:{H:1.087, F:1.35, Cl:1.77, Br:1.94, I:2.14},
    Si:{H:1.48, F:1.56, Cl:2.02, Br:2.15, I:2.43}
  };
  function tetrahedral(counts, formula) {
    const center = counts.has('C') ? 'C' : 'Si';
    if (counts.get(center) !== 1) return [];
    const bondLengths = lengths[center];
    const ligands = [...counts].filter(([kind]) => kind !== center)
      .sort(([a, n], [b, m]) => m - n || a.localeCompare(b, 'en'));
    if (ligands.some(([kind]) => !Number.isFinite(bondLengths[kind])) ||
        ligands.reduce((sum, [,n]) => sum + n, 0) !== 4) return [];

    const s = Math.sqrt(2/3), c = 1 / Math.sqrt(3);
    let group, directions;
    if (ligands.length === 1) {
      group = 'Td';
      directions = E.orbit(group, [0,0,1]).positions;
    } else if (ligands[0][1] === 3) {
      group = 'C3v';
      directions = [[Math.sqrt(8)/3,0,-1/3], [-Math.sqrt(2)/3,s,-1/3], [-Math.sqrt(2)/3,-s,-1/3], [0,0,1]];
    } else if (ligands.length === 2) {
      group = 'C2v';
      directions = [[s,0,c], [-s,0,c], [0,s,-c], [0,-s,-c]];
    } else {
      group = ligands.length === 3 ? 'Cs' : 'C1';
      directions = [[c,0,s], [c,0,-s], [-c,s,0], [-c,-s,0]];
    }
    const kinds = ligands.flatMap(([kind,n]) => Array(n).fill(kind));
    const atoms = [[center,0,0,0], ...directions.map((direction, i) =>
      [kinds[i], ...direction.map(x => bondLengths[kinds[i]] * x)])];
    if (group === 'C1') return [
      model('tetra-a', '四面体 · 对映体 A', group, atoms),
      model('tetra-b', '四面体 · 对映体 B', group, atoms.map(([kind,x,y,z]) => [kind,x,y,-z]))
    ];
    const name = formula === 'CH4' ? '甲烷 · 正四面体' : center === 'C' ? '四面体碳中心' : '四面体硅中心';
    return [model('tetra', name, group, atoms)];
  }

  // Ideal planar alkenes. C=C is along z (1,1) or x (cis/trans).
  function dichloroethenes() {
    const halfCC = 0.67, h = 1.08, cl = 1.72, sin60 = Math.sqrt(3) / 2;
    const gem = [], cis = [], trans = [];
    for (const side of [-1,1]) {
      const x = side * halfCC, xH = x + side*h/2, xCl = x + side*cl/2;
      const kind = side === 1 ? 'Cl' : 'H', length = side === 1 ? cl : h;
      gem.push(['C',0,0,x], [kind,sin60*length,0,x + side*length/2], [kind,-sin60*length,0,x + side*length/2]);
      cis.push(['C',x,0,0], ['H',xH,0,-sin60*h], ['Cl',xCl,0,sin60*cl]);
      trans.push(['C',x,0,0], ['H',xH,-side*sin60*h,0], ['Cl',xCl,side*sin60*cl,0]);
    }
    return [model('gem','1,1-二氯乙烯','C2v',gem), model('cis','顺式-1,2-二氯乙烯','C2v',cis),
      model('trans','反式-1,2-二氯乙烯','C2h',trans)];
  }

  const records = new Map();
  for (const entry of [...library.organics, ...library.complexes]) {
    const {counts, charge} = parseFormula(entry.formula), key = S.formatFormula(counts);
    if (!records.has(key)) records.set(key, []);
    records.get(key).push({entry, charge});
  }

  function lookup(input) {
    const {counts, charge} = parseFormula(input), formula = S.formatFormula(counts);
    let candidates;
    if (charge) candidates = [];
    else switch (formula) {
      // The two C2H6O coordinate sets are the trans ethanol and dimethyl ether
      // cartesians in NIST CCCBDB (CAS 64-17-5 and 115-10-6, respectively).
      case 'C2H6O': candidates = [model('ethanol-trans','乙醇 · 反式构象','Cs',ethanol,'64175'),
        model('dimethyl-ether','二甲醚','C2v',ether,'115106')]; break;
      case 'C2H2Cl2': candidates = dichloroethenes(); break;
      case 'H2O': candidates = [model('water','水 · 弯曲形','C2v',[
        ['O',0,0,0], ['H',0.75695,0,0.58588], ['H',-0.75695,0,0.58588]])]; break;
      case 'CO2': candidates = [model('carbon-dioxide','二氧化碳 · 线形（有限子群）','D4h',[
        ['C',0,0,0], ['O',0,0,1.16], ['O',0,0,-1.16]])]; break;
      case 'C6H6': candidates = [model('benzene','苯 · 平面六元环','D6h',[
        ...E.orbit('D6h',[1.397,0,0]).positions.map(p => ['C',...p]),
        ...E.orbit('D6h',[2.481,0,0]).positions.map(p => ['H',...p])])]; break;
      case 'H3N': candidates = [model('ammonia','氨 · 三角锥形','C3v',[
        ['N',0,0,0], ...E.orbit('C3v',[0.94,0,-0.38]).positions.map(p => ['H',...p])])]; break;
      case 'BF3': candidates = [model('boron-trifluoride','三氟化硼 · 平面三角形','D3h',[
        ['B',0,0,0], ...E.orbit('D3h',[1.31,0,0]).positions.map(p => ['F',...p])])]; break;
      case 'F6S': candidates = [model('sulfur-hexafluoride','六氟化硫 · 正八面体','Oh',[
        ['S',0,0,0], ...E.orbit('Oh',[0,0,1.56]).positions.map(p => ['F',...p])])]; break;
      default: candidates = tetrahedral(counts, formula);
    }
    for (const {entry, charge:ionicCharge} of records.get(formula) || []) {
      if (charge && charge !== ionicCharge) continue;
      const candidate = model(entry.id, entry.name, entry.group, entry.atoms(), entry.cas);
      if (entry.cas) candidate.geometry = '对称化 NIST 参考几何';
      if (entry.cid) {
        candidate.geometry = 'PubChem 计算构象';
        candidate.sourceURL = 'https://pubchem.ncbi.nlm.nih.gov/compound/' + entry.cid;
        candidate.conformerID = entry.conformerID;
      }
      if (ionicCharge) Object.assign(candidate, {charge:ionicCharge, formula:entry.formula, display:speciesDisplay(entry.formula)});
      candidates.push(candidate);
    }
    const composition = S.formatFormula(counts, true);
    return charge ? {formula:'[' + formula + ']' + chargeSuffix(charge),
      display:candidates[0]?.display || '[' + composition + ']' + chargeSuffix(charge, true), candidates}
      : {formula, display:composition, candidates};
  }

  function catalog() {
    const organic = [
      {formula:'CH4', name:'甲烷 · 正四面体'}, {formula:'C6H6', name:'苯 · 平面六元环'},
      {formula:'C2H6O', name:'乙醇 · 反式构象'}, {formula:'C2H6O', name:'二甲醚'},
      ...dichloroethenes().map(c => ({formula:'C2H2Cl2', name:c.name})), ...library.organics
    ];
    return [[ '常见有机物', organic ], [ '代表性配合物', library.complexes ]].map(([category, entries]) => {
      const labels = new Map();
      for (const {formula, name} of entries) {
        if (!labels.has(formula)) labels.set(formula, []);
        labels.get(formula).push(name);
      }
      return {category, items:Array.from(labels, ([formula, names]) => ({formula, display:speciesDisplay(formula), names}))};
    });
  }

  const api = {lookup, catalog};
  if (commonJS) module.exports = api;
  root.FormulaModels = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
