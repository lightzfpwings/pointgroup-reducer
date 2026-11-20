'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const F = require('../formula-models.js'), S = require('../structure.js'), V = require('../vibrations.js');

test('neutral formulas match by element totals and preserve case and isotope labels', () => {
  for (const input of [' (CH₃)₂O ', 'C2H5OH', 'H6OC2', 'C2 H6 O']) {
    assert.equal(F.lookup(input).formula, 'C2H6O');
    assert.deepEqual(F.lookup(input).candidates.map(c => c.id), ['ethanol-trans','dimethyl-ether']);
  }
  assert.equal(F.lookup('((CH2)2)3').formula,'C6H12');
  assert.equal(F.lookup('Co').formula,'Co');
  assert.equal(F.lookup('CO').formula,'CO');
  assert.equal(F.lookup('D2O').formula,'D2O');
  assert.equal(F.lookup('C120').candidates.length,0);
  for (const invalid of ['', 'ch4', 'Xx2', 'CH0', 'C01H4', 'CH3)', '(CH3', 'C()2', '2H2O', 'CH4++', 'CuSO4·5H2O', 'C121', '(C2H6)16', 'H'.repeat(513)]) {
    assert.throws(() => F.lookup(invalid), undefined, invalid);
  }
});

test('coordination formulas distinguish charges, ligand multiplicity and an omitted charge', () => {
  for (const query of ['[Fe(CN)6]4-', '[Fe(CN)₆]⁴⁻', 'Fe(CN)6^4-', '[Fe(CN)6]4−', '[C6FeN6]4-']) {
    const listing = F.lookup(query);
    assert.deepEqual(listing.candidates.map(c => [c.id,c.charge]), [['ferrocyanide',-4]]);
    assert.equal(listing.display, '[Fe(CN)₆]⁴⁻');
    assert.equal(F.lookup(listing.formula).candidates[0].id, 'ferrocyanide');
  }
  assert.deepEqual(F.lookup('[Fe(CN)6]').candidates.map(c => c.id), ['ferrocyanide','ferricyanide']);
  assert.equal(F.lookup('[Fe(CN)6]3-').candidates[0].id, 'ferricyanide');
  assert.equal(F.lookup('[Ag(NH3)2]+').candidates[0].charge, 1);
  for (const query of ['[Fe(CN)6]2-', 'CH4+', '[PtCl4]2+']) assert.deepEqual(F.lookup(query).candidates, []);
  assert.equal(F.lookup('NH4+').formula, '[H4N]+');
  for (const query of ['[Fe(CN)6', 'Fe(CN)6]', '[PtCl4]02-', '[PtCl4]0-', '[PtCl4]2--', '[]+']) {
    assert.throws(() => F.lookup(query), undefined, query);
  }
});

test('every catalog candidate has the indexed atoms, closes its group and yields the full 3N decomposition', () => {
  const ids = new Set();
  for (const section of F.catalog()) for (const item of section.items) {
    const listing = F.lookup(item.formula);
    assert.equal(listing.candidates.length, item.names.length, item.formula);
    for (const candidate of listing.candidates) {
      assert(!ids.has(candidate.id), candidate.id);
      ids.add(candidate.id);
      const counts = new Map();
      for (const site of candidate.sites) counts.set(site.kind, (counts.get(site.kind) || 0) + 1);
      assert.equal(S.formatFormula(counts), listing.formula.replace(/^\[|\]\d*[+-]$/g, ''), candidate.id);
      const input = {...candidate, vibrationOrigin:'centroid', tolerance:1e-6};
      const expected = 3 * candidate.sites.length - (V.review(input).geometry === 'linear' ? 5 : 6);
      const result = V.calculate(input);
      assert.equal(result.degreesOfFreedom, expected, candidate.id);
      assert(result.counts.irBands > 0 && result.counts.ramanBands > 0, candidate.id);
    }
  }
  assert.equal(ids.size, 67);
});

test('the glucose anomers and alanine enantiomers retain their source stereochemistry', () => {
  function handedness(candidate, neighbors) {
    const [a,b,c,d] = neighbors.map(id => candidate.sites[id-1].position);
    const [u,v,w] = [a,b,c].map(p => p.map((x,i) => x-d[i]));
    return Math.sign(u[0]*(v[1]*w[2]-v[2]*w[1]) - u[1]*(v[0]*w[2]-v[2]*w[0]) + u[2]*(v[0]*w[1]-v[1]*w[0]));
  }
  for (const [formula, ids, cids, atoms] of [
    ['C6H12O6',['alpha-d-glucose','beta-d-glucose'],[79025,64689],[1,5,10,17]],
    ['C3H7NO2',['l-alanine','d-alanine'],[5950,71080],[3,5,6,7]]
  ]) {
    const candidates = F.lookup(formula).candidates;
    assert.deepEqual(candidates.map(c => c.id), ids);
    assert.deepEqual(candidates.map(c => Number(c.sourceURL.split('/').pop())), cids);
    const signs = candidates.map(c => handedness(c,atoms));
    assert.equal(signs[0]*signs[1], -1);
    assert(candidates.every(c => c.geometry === 'PubChem 计算构象' && c.conformerID));
  }
});

test('alkene and platinum stereoisomers have distinct geometries and selection rules', () => {
  const angleAtMetal = c => {
    const pt = c.sites.find(s => s.kind === 'Pt'), [a,b] = c.sites.filter(s => s.kind === 'Cl');
    return S.measure(a, pt, b).angle;
  };
  const [cis,trans] = F.lookup('[PtCl2(NH3)2]').candidates;
  assert(Math.abs(angleAtMetal(cis)-90)<1e-6 && Math.abs(angleAtMetal(trans)-180)<1e-6);
  assert.deepEqual([cis,trans].map(c => [c.group,spectrum(c).counts.irBands]), [['C2v',22],['C2h',15]]);
  const alkene = F.lookup('C4H8').candidates;
  assert.deepEqual(alkene.map(c => c.id), ['cis-butene','trans-butene','isobutene','cyclobutane']);
  assert.deepEqual(alkene.map(c => spectrum(c).degreesOfFreedom), [30,30,30,30]);
  const ferrocene = F.lookup('Fe(C5H5)2').candidates;
  assert.deepEqual(ferrocene.map(c => [c.group,spectrum(c).degreesOfFreedom]), [['D5h',57],['D5d',57]]);
});

function spectrum(candidate) {
  return V.calculate({...candidate, tolerance:1e-6, vibrationOrigin:'centroid'});
}

test('each isomer supplies its own geometry and spectrum, including isomers in the same group', () => {
  const examples = {
    CH4:[['Td',9,2,4]], H2O:[['C2v',3,3,3]], CO2:[['D4h',4,2,1]],
    C2H6O:[['Cs',21,21,21],['C2v',21,17,21]],
    C2H2Cl2:[['C2v',12,11,12],['C2v',12,10,12],['C2h',12,6,6]]
  };
  for (const [formula,expected] of Object.entries(examples)) {
    const listing = F.lookup(formula);
    assert.deepEqual(listing.candidates.map(candidate => {
      assert.equal(S.composition(candidate.sites),listing.display);
      const r = spectrum(candidate);
      if (candidate.id === 'trans') assert(r.activities.every(a => a.irActive !== a.ramanActive));
      return [candidate.group,r.degreesOfFreedom,r.counts.irBands,r.counts.ramanBands];
    }),expected);
  }
  const changed = F.lookup('C2H6O').candidates[0];
  changed.sites[0].position[0] = 900;
  assert.equal(F.lookup('C2H6O').candidates[0].sites[0].position[0],1.1879);
  for (const [formula,group] of [['NH3','C3v'],['BF3','D3h'],['SF6','Oh'],['C6H6','D6h']]) {
    const listing = F.lookup(formula), candidate = listing.candidates[0];
    assert.equal(S.composition(candidate.sites),listing.display);
    assert.equal(spectrum(candidate).group,group);
  }
});

test('all neutral tetrahedral substitutions satisfy the declared symmetry and retain distinct mirror images', () => {
  const kinds = ['H','F','Cl','Br','I'];
  for (const center of ['C','Si']) {
    for (let i=0; i<5; i++) for (let j=i; j<5; j++) for (let k=j; k<5; k++) for (let l=k; l<5; l++) {
      const ligands = [kinds[i],kinds[j],kinds[k],kinds[l]];
      const listing = F.lookup(center + ligands.join(''));
      const pattern = [...new Set(ligands)].map(kind => ligands.filter(k => k === kind).length).sort().join('');
      const group = {'4':'Td','13':'C3v','22':'C2v','112':'Cs','1111':'C1'}[pattern];
      assert.equal(listing.candidates.length, group === 'C1' ? 2 : 1);
      for (const candidate of listing.candidates) {
        assert.equal(candidate.group,group);
        assert.equal(S.composition(candidate.sites),listing.display);
        assert.equal(V.review({...candidate, tolerance:1e-6, vibrationOrigin:'centroid'}).geometry,'nonlinear');
      }
      if (group === 'C1') {
        const handedness = candidate => {
          const [a,b,c] = candidate.sites.slice(1,4).map(s => s.position);
          return Math.sign(a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0]));
        };
        const [left,right] = listing.candidates;
        assert.equal(Math.abs(handedness(left)),1);
        assert.equal(handedness(left),-handedness(right));
      }
    }
  }
});
