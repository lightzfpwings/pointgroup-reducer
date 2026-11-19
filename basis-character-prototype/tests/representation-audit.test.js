'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine.js');
const A = require('../reducer-adapter.js');
const R = require('../reduction-engine.js');

test('all sites must implement the group law even when only the axial site carries orbitals', () => {
  const spec = {
    group: 'C6', tolerance: 0.01,
    sites: [
      { id: 'H1', kind: 'H', position: [0.009, 0, 0] },
      { id: 'H2', kind: 'H', position: [-0.009, 0, 0] },
      { id: 'C', kind: 'C', position: [0, 0, 1] }
    ],
    functions: [{ id: 's', site: 'C', radial: '2s', family: 's' }]
  };
  // Independent nearest matches make C6 fix the H sites and C6² swap them.
  for (const calculate of [E.siteAction, E.calculate]) {
    assert.throws(() => calculate(spec), error => error.code === 'mapping_bijection');
  }
  const water = E.template('water');
  assert.deepEqual(E.siteAction(water).permutations, E.calculate(water).operations.map(op => op.sitePermutation));
});

test('orbit expansion rejects a tolerance partition with the right orbit-stabilizer count but no group action', () => {
  assert.throws(() => E.orbit('D6h', [0.006, 0, 0], 0.01), error => error.code === 'orbit_stabilizer');
  assert.equal(E.orbit('D6h', [0.006, 0, 0], 1e-6).count, 6);
});

test('complete oblique p bases retain their C3v representation at very different direction scales', () => {
  const spec = E.template('central-c2v');
  spec.group = 'C3v';
  spec.functions[0].direction = [1e300, 0, 0];
  spec.functions[1].direction = [1e300, 1e297, 0];
  const basis = E.calculate(spec);
  assert(basis.checks.maxAngularResidual < 1e-11);
  assert(basis.checks.representationError < 1e-8);
  const reduced = R.integrate(basis, A).total;
  assert.deepEqual(reduced.terms.map(t => [t.irrep, t.multiplicity]), [['A1', 1], ['E', 1]]);
});

test('manual complex arithmetic keeps tiny components and finite quotients across scales', () => {
  assert.deepEqual(R.number('1e-13i * 1e13'), { re: 0, im: 1 });
  assert.equal(R.number('1e200 / 1e200'), 1);
  assert.equal(R.number('1e-220 / 1e-220'), 1);
  assert.deepEqual(R.number('(1e200+1e200i)/(1e200-1e200i)'), { re: 0, im: 1 });
  assert.equal(R.number('(1e-320i+1e-320)/(1e-320i+1e-320)'), 1);
  assert.equal(R.number('(-10)^20'), 1e20);
  assert.equal(R.number('i^2'), -1);
  assert.deepEqual(R.number('sqrt(-1)'), { re: 0, im: 1 });
  assert.throws(() => R.number('1/1e999'), R.ReductionError);
  const r = R.reduce('C1', [{ re: 1, im: 2e-13 }], 1e-14);
  assert.equal(r.valid, false);
  assert.deepEqual(r.c, [{ re: 1, im: 2e-13 }]);
  assert.equal(R.reduce('C1', [1e20]).valid, false);
});
