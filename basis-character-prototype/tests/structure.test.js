'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const S = require('../structure.js');
const V = require('../vibrations.js');

test('single-frame XYZ preserves a blank comment, signed/scientific Å coordinates and isotope identity', () => {
  const parsed = S.parseXYZ('\uFEFF3\r\n\r\nO 0 -0.5 +2\r\nh +1E-2 -.5 3.2\r\nD -1D-2 -.5 3.2\r\n');
  assert.equal(parsed.note,'');
  assert.deepEqual(parsed.sites.map(s=>s.kind), ['O','H','D']);
  assert.deepEqual(parsed.sites[1].position, [.01,-.5,3.2]);
  assert.equal(S.composition(parsed.sites),'DHO');
  assert.throws(() => V.review({...parsed,group:'C2v'}),{code:'missing_site'});
  const centered = {...parsed,group:'Cs'}; // Cs mirror is xy; this orientation is incompatible.
  assert.throws(() => V.review(centered),{code:'missing_site'});
});

test('reject incomplete, multi-frame, malformed, unknown or coincident XYZ atoms', () => {
  for (const text of ['0\nempty','121\nlarge','2.5\na','3\nO 0 0 0\nH 1 0 0\nH -1 0 0',
    '1\na\nO 0 0 0\n1\nb\nH 1 1 1','1\na\nC 0x2 0 1','1\na\nO 0 Infinity 0',
    '1\na\nO 1 0','1\na\nO 0 1 2 .3','1\na\nXx 0 0 0','2\na\nO 0 0 0\nC 0 0 0']) {
    assert.throws(() => S.parseXYZ(text), undefined, text);
  }
  assert.throws(() => S.parseXYZ('2\na\nC 0 0 0\nH 1 2 NaN'), e => e.code === 'xyz_coordinates' && e.detail.line === 4);
});

test('molecular review checks rigid motions and symmetry without modifying input coordinates', () => {
  const shifted = S.parseXYZ('3\nCO2\nO 6 3 3.84\nC 6 3 5\nO 6 3 6.16');
  const spec = {...shifted,group:'D4h'}, before = JSON.stringify(spec);
  const info = V.review(spec), spectrum = V.calculate(spec);
  assert.equal(info.geometry,'linear'); assert.equal(info.operations,16); assert(info.maxDeviation < 1e-12);
  assert.deepEqual(info.origin,spectrum.origin); assert.equal(spectrum.degreesOfFreedom,4);
  assert.equal(JSON.stringify(spec),before);
  const single = S.parseXYZ('1\nHelium\nHe 8 9 -5');
  assert.equal(V.review({...single,group:'Oh'}).geometry,'atomic');
  assert.deepEqual(S.measure(single.sites[0], single.sites[0]),{});
});
