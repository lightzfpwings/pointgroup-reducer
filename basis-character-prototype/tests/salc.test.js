'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine.js');
const R = require('../reduction-engine.js');
const S = require('../salc.js');

function near(a, b, tolerance = 1e-8) {
  assert(R.abs(R.add(a, R.mul(-1, b))) < tolerance, JSON.stringify([a, b]));
}

function regular(group) {
  const sites = E.orbit(group, [.271, .483, .695]).positions.map((position, i) => ({id: 'X' + i, kind: 'X', position}));
  return {group, sites, functions: sites.map(s => ({id: 's' + s.id, site: s.id, radial: '1s', family: 's'}))};
}

// Compute the input-basis Gram form explicitly, independently of the SALC implementation.
function overlapMatrix(functions) {
  const angular = f => f.family === 's' ? [1] : f.family === 'p' ? f.direction : f.tensor.flat();
  return functions.map(f => functions.map(h => {
    if (f.site !== h.site || f.radial !== h.radial || f.family !== h.family) return 0;
    return angular(f).reduce((sum, v, i) => sum + v * angular(h)[i], 0);
  }));
}

const transform = (matrix, c) => matrix.map(row => row.reduce((s, v, i) => R.add(s, R.mul(v, c[i])), 0));
const dot = (v, w) => v.reduce((s, x, i) => R.add(s, R.mul(R.conj(x), w[i])), 0);

function checkVectors(result, salcs) {
  const gram = overlapMatrix(result.functions);
  const all = [];
  salcs.spaces.forEach(space => space.copies.forEach(copy => {
    const vectors = copy.vectors.map(v => v.coefficients);
    assert.equal(vectors.length, space.dimension);
    for (const v of vectors) {
      all.push(v);
      const gramV = transform(gram, v);
      all.forEach(u => near(dot(u, gramV), u === v ? 1 : 0));
      for (const operation of result.representationMatrices) {
        const image = transform(operation, v), gramImage = transform(gram, image);
        const coordinates = vectors.map(u => dot(u, gramImage));
        const residual = image.map((x, i) =>
          vectors.reduce((s, u, j) => R.add(s, R.mul(u[i], R.mul(-1, coordinates[j]))), x));
        const residualNorm2 = R.abs(dot(residual, transform(gram, residual)));
        assert(residualNorm2 < 1e-16, String(residualNorm2));
      }
    }
  }));
  assert.equal(all.length, result.dimension);
}

test('the two H 1s orbitals in xz water give normalized sum and difference', () => {
  const basis = E.calculate(E.template('water')), result = S.calculate(basis);
  assert.deepEqual(result.functionIds, basis.functions.map(f => f.id));
  assert.deepEqual(result.spaces.map(s => s.irrep), ['A1', 'B1']);
  result.spaces.forEach((space, i) => {
    const [h0, h1] = space.copies[0].vectors[0].coefficients;
    near(h0, Math.SQRT1_2);
    near(h1, (i ? -1 : 1) * Math.SQRT1_2);
  });
});

test('complex C3 conjugate SALCs have the eigenvalue of their named table row', () => {
  const input = E.template('central-oh');
  input.group = 'C3';
  input.functions = input.functions.slice(0, 2);
  const basis = E.calculate(input), result = S.calculate(basis);
  const g = E.group('C3').generatorIndexes[0];
  assert.deepEqual(result.spaces.map(s => s.irrep), ['E1+', 'E1-']);
  const rows = result.spaces.map(s => s.copies[0].vectors[0].coefficients);
  rows[0].forEach((v, j) => near(v, R.conj(rows[1][j])));
  assert(Math.abs(R.z(rows[0][1]).im) > .7);
  rows.forEach((row, j) => {
    const image = transform(basis.representationMatrices[g], row);
    const eigenvalue = {re: -.5, im: (j === 0 ? 1 : -1) * Math.sqrt(3) / 2};
    row.forEach((v, i) => near(image[i], R.mul(eigenvalue, v)));
  });
  checkVectors(basis, result);
});

test('multiple E copies within one closed C3v block are individually invariant', () => {
  const basis = E.calculate(regular('C3v')), result = S.calculate(basis);
  assert.equal(basis.blocks.length, 1);
  const space = result.spaces.find(s => s.irrep === 'E');
  assert.equal(space.copies.length, 2);
  checkVectors(basis, result);
  const [first, second] = space.copies.map(copy => copy.vectors.map(v => v.coefficients));
  for (const matrix of basis.representationMatrices) for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) {
    near(dot(first[i], transform(matrix, first[j])), dot(second[i], transform(matrix, second[j])));
  }
});

test('skew p and independently rotated d inputs use the on-site angular metric', () => {
  const p = E.template('central-oh');
  p.group = 'C3v';
  p.functions[1].direction = [1, .001, 0];
  const d = E.template('central-d-c2v');
  const angle = .31, c = Math.cos(angle), s = Math.sin(angle);
  d.functions[0].frame = [[c, -s, 0], [s, c, 0], [0, 0, 1]];
  for (const spec of [p, d]) {
    const basis = E.calculate(spec), salcs = S.calculate(basis);
    assert.equal(salcs.metric, 'onsite-angular');
    checkVectors(basis, salcs);
  }
});

test('an almost symmetry-forbidden first AO does not spoil a well-conditioned SALC', () => {
  const spec = E.template('central-c2v');
  spec.group = 'C3v';
  const directions = [[1e-9, .93e-9, 1], [1, 0, 0], [0, 1, 0]];
  spec.functions.forEach((f, i) => { f.direction = directions[i]; });
  const basis = E.calculate(spec);
  checkVectors(basis, S.calculate(basis));
});

test('every irrep in all 87 supported regular representations yields d orthogonal copies of size d', () => {
  for (const group of E.groupNames) {
    const basis = E.calculate(regular(group)), salcs = S.calculate(basis);
    assert.equal(salcs.dimension, E.group(group).size, group);
    assert.deepEqual(salcs.spaces.map(s => s.irrep), R.table(group).irreps, group);
    for (const s of salcs.spaces) {
      assert.equal(s.copies.length, s.dimension, group + ' ' + s.irrep);
      assert(s.copies.every(copy => copy.vectors.length === s.dimension), group + ' ' + s.irrep);
      if (s.dimension > 1) assert(s.copies.every(copy => copy.vectors.every(v => v.coefficients.every(c => typeof c === 'number'))), group);
    }
    for (const name of ['orthogonalityError', 'invarianceError', 'characterError']) {
      assert(salcs.checks[name] < 1e-9, group + ' ' + name);
    }
  }
});

test('integrity checks reject the wrong irrep action even with correct dimensions and character metadata', () => {
  const basis = E.calculate(E.template('water'));
  basis.representationMatrices = basis.representationMatrices.map(() => [[1, 0], [0, 1]]);
  assert.throws(() => S.calculate(basis), error => error.code === 'salc_verification');
});
