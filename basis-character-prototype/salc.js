/* Symmetry-adapted linear combinations in the input AO order. */
(function (root) {
  'use strict';
  const commonJS = typeof module !== 'undefined' && module.exports;
  const E = commonJS ? require('./engine.js') : root.BasisEngine;
  const A = commonJS ? require('./reducer-adapter.js') : root.ReducerAdapter;
  const R = commonJS ? require('./reduction-engine.js') : root.ReductionEngine;
  const tolerance = 1e-7;
  const rankTolerance = 1e-9;

  function failed(detail) {
    throw new E.BasisError('salc_verification', 'SALC 未通过投影、维数或正交性校验。', detail);
  }

  // Complex vectors use interleaved real/imaginary parts. Their angular
  // coordinates implement the input metric without forming a squared Gram matrix.
  function angularCoordinates(functions) {
    const offsets = new Map();
    let size = 0;
    const columns = functions.map(f => {
      const key = JSON.stringify([f.site, f.radial, f.family]);
      const values = f.family === 's' ? [1] : f.family === 'p' ? f.direction : f.tensor.flat();
      if (!offsets.has(key)) {
        offsets.set(key, size);
        size += values.length;
      }
      return {offset: offsets.get(key), values};
    });
    return coefficients => {
      const angular = new Float64Array(2 * size);
      columns.forEach(({offset, values}, j) => {
        const re = coefficients[2 * j], im = coefficients[2 * j + 1];
        if (re || im) values.forEach((value, k) => {
          angular[2 * (offset + k)] += value * re;
          angular[2 * (offset + k) + 1] += value * im;
        });
      });
      return {coefficients, angular};
    };
  }

  function inner(a, b) {
    let re = 0, im = 0;
    for (let k = 0; k < a.length; k += 2) {
      re += a[k] * b[k] + a[k + 1] * b[k + 1];
      im += a[k] * b[k + 1] - a[k + 1] * b[k];
    }
    return {re, im};
  }

  function subtractMultiple(target, vector, re, im) {
    for (let k = 0; k < target.length; k += 2) {
      target[k] -= re * vector[k] - im * vector[k + 1];
      target[k + 1] -= re * vector[k + 1] + im * vector[k];
    }
  }

  function removeComponents(v, basis) {
    for (let pass = 0; pass < 2; pass++) for (const u of basis) {
      const {re, im} = inner(u.angular, v.angular);
      if (re || im) {
        subtractMultiple(v.angular, u.angular, re, im);
        subtractMultiple(v.coefficients, u.coefficients, re, im);
      }
    }
    return Math.sqrt(inner(v.angular, v.angular).re);
  }

  function independent(v, basis, embed) {
    const length = removeComponents(v, basis);
    if (length <= rankTolerance) return null;
    // Recompute the metric image from the coefficients that will be exported.
    return embed(v.coefficients.map(x => x / length));
  }

  // The character projector selects all copies at once. Within that isotypic
  // space select one partner line in each copy by restricting to a subgroup.
  // A rank-one real sign projector keeps real-type irreps real. In particular,
  // the four-dimensional icosahedral G needs the commuting involutions of V4.
  function partnerFilter(group, chars, dimension) {
    if (dimension === 1) return [[0, 1]];
    function rankOne(operations, signs) {
      const trace = operations.reduce((s, op, i) => s + signs[i] * chars[op].re, 0) / operations.length;
      if (Math.abs(trace - 1) < rankTolerance) {
        return operations.map((op, i) => [op, signs[i] / operations.length]);
      }
    }
    const involutions = [];
    for (let g = 1; g < group.size; g++) {
      const powers = [0];
      for (let p = g; p !== 0; p = group.multiply[p][g]) powers.push(p);
      if (powers.length === 2) involutions.push(g);
      for (const sign of powers.length % 2 ? [1] : [1, -1]) {
        const found = rankOne(powers, powers.map((_, k) => sign ** k));
        if (found) return found;
      }
    }
    for (const a of involutions) for (const b of involutions) {
      const ab = group.multiply[a][b];
      if (a >= b || ab !== group.multiply[b][a]) continue;
      for (const x of [1, -1]) for (const y of [1, -1]) {
        const found = rankOne([0, a, b, ab], [1, x, y, x * y]);
        if (found) return found;
      }
    }
    failed({reason: 'partner projector', group: group.name, dimension});
  }

  function projectorWeights(group, chars, dimension) {
    const line = partnerFilter(group, chars, dimension);
    const weights = chars.map(() => ({re: 0, im: 0}));
    for (const [h, factor] of line) for (let g = 0; g < group.size; g++) {
      const entry = weights[group.multiply[h][g]];
      const scale = factor * dimension / group.size;
      entry.re += scale * chars[g].re;
      entry.im -= scale * chars[g].im;
    }
    return weights;
  }

  function sparseColumns(matrix) {
    const columns = matrix.map(() => []);
    matrix.forEach((row, i) => row.forEach((value, j) => {
      if (value !== 0) columns[j].push([i, value]);
    }));
    return columns;
  }

  function columnProjection(operations, weights, j, n) {
    const result = new Float64Array(2 * n);
    weights.forEach(({re, im}, g) => {
      if (re || im) for (const [i, v] of operations[g][j]) {
        result[2 * i] += v * re;
        result[2 * i + 1] += v * im;
      }
    });
    return result;
  }

  function transform(operation, input, embed) {
    const c = input.coefficients, target = new Float64Array(c.length);
    operation.forEach((column, j) => {
      const re = c[2 * j], im = c[2 * j + 1];
      if (re || im) for (const [i, value] of column) {
        target[2 * i] += value * re;
        target[2 * i + 1] += value * im;
      }
    });
    return embed(target);
  }

  function partners(seed, dimension, generators, embed) {
    const vectors = [seed];
    for (let i = 0; i < vectors.length && vectors.length < dimension; i++) {
      for (const generator of generators) {
        const v = independent(transform(generator, vectors[i], embed), vectors, embed);
        if (v) vectors.push(v);
        if (vectors.length === dimension) break;
      }
    }
    if (vectors.length !== dimension) failed({reason: 'partner count', dimension, obtained: vectors.length});
    return vectors;
  }

  function selectSeeds(operations, weights, n, multiplicity, embed, irrep) {
    // A nearly symmetry-forbidden AO can have a genuine but tiny projection.
    // Pivot before normalizing so that cancellation in it is not amplified.
    const candidates = Array.from({length: n}, (_, j) => embed(columnProjection(operations, weights, j, n)));
    const norms = candidates.map(v => Math.sqrt(inner(v.angular, v.angular).re));
    const seeds = [];
    while (seeds.length < multiplicity) {
      let best = 0;
      for (let j = 1; j < n; j++) if (norms[j] > norms[best] * (1 + 1e-12)) best = j;
      if (norms[best] <= rankTolerance) failed({reason: 'multiplicity', irrep, expected: multiplicity, obtained: seeds.length});
      const seed = independent(candidates[best], seeds, embed);
      norms[best] = 0;
      if (!seed) continue;
      seeds.push(seed);
      if (seeds.length === multiplicity) break;
      for (let j = 0; j < n; j++) {
        if (norms[j] > rankTolerance) norms[j] = removeComponents(candidates[j], [seed]);
      }
    }
    return seeds;
  }

  function packed(vector) {
    const c = vector.coefficients;
    const coefficients = Array.from({length: c.length / 2}, (_, j) => {
      const re = c[2 * j], im = c[2 * j + 1];
      return im === 0 ? re : {re, im};
    });
    return {coefficients};
  }

  function verifyCopy(vectors, all, chars, representatives, operations, generators, embed, checks) {
    for (const v of vectors) {
      for (const u of [...all, v]) {
        const overlap = inner(u.angular, v.angular);
        checks.orthogonalityError = Math.max(checks.orthogonalityError, Math.hypot(overlap.re - (u === v ? 1 : 0), overlap.im));
      }
      all.push(v);
      for (const generator of generators) {
        const residual = removeComponents(transform(generator, v, embed), vectors);
        checks.invarianceError = Math.max(checks.invarianceError, residual);
      }
    }
    for (const g of representatives) {
      let re = 0, im = 0;
      for (const v of vectors) {
        const diagonal = inner(v.angular, transform(operations[g], v, embed).angular);
        re += diagonal.re;
        im += diagonal.im;
      }
      checks.characterError = Math.max(checks.characterError, Math.hypot(re - chars[g].re, im - chars[g].im));
    }
  }

  function calculate(basisResult) {
    const decomposition = R.integrate(basisResult, A);
    const group = E.group(basisResult.group), n = basisResult.dimension;
    const table = R.table(group.name), classOf = Array(group.size);
    for (const {source_index, target_index} of decomposition.mapping) {
      for (const g of group.classes[source_index].members) classOf[g] = target_index;
    }
    const operations = basisResult.representationMatrices.map(sparseColumns);
    const generators = group.generatorIndexes.map(i => operations[i]);
    const representatives = group.classes.map(c => c.representative);
    const embed = angularCoordinates(basisResult.functions);
    const checks = {orthogonalityError: 0, invarianceError: 0, characterError: 0, tolerance};
    const all = [], spaces = [];

    for (const {irrep, multiplicity, dimension} of decomposition.total.terms) {
      const row = table.X[table.irreps.indexOf(irrep)];
      const chars = classOf.map(c => R.z(row[c]));
      const weights = projectorWeights(group, chars, dimension);
      const seeds = selectSeeds(operations, weights, n, multiplicity, embed, irrep);
      const copies = [];
      for (const seed of seeds) {
        const vectors = partners(seed, dimension, generators, embed);
        verifyCopy(vectors, all, chars, representatives, operations, generators, embed, checks);
        copies.push({vectors: vectors.map(packed)});
      }
      spaces.push({irrep, dimension, multiplicity, copies});
    }
    if (all.length !== n || ![checks.orthogonalityError, checks.invarianceError, checks.characterError].every(e => e <= tolerance)) failed(checks);
    return {group: group.name, dimension: n, functionIds: basisResult.functions.map(f => f.id), metric: 'onsite-angular', spaces, checks};
  }

  const api = {calculate};
  if (commonJS) module.exports = api;
  root.SalcEngine = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
