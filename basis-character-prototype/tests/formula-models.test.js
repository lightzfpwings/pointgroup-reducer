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
  for (const invalid of ['', 'ch4', 'Xx2', 'CH0', 'C01H4', 'CH3)', '(CH3', 'C()2', '2H2O', 'CH4+', 'CuSO4·5H2O', 'C121', '(C2H6)16', 'H'.repeat(513)]) {
    assert.throws(() => F.lookup(invalid), undefined, invalid);
  }
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
