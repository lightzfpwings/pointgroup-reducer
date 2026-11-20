/* Fundamental vibrations and first-order electric-dipole IR / symmetric-tensor Raman selection. */
(function (root) {
  'use strict';
  const commonJS = typeof module !== 'undefined' && module.exports;
  const E = commonJS ? require('./engine.js') : root.BasisEngine;
  const A = commonJS ? require('./reducer-adapter.js') : root.ReducerAdapter;
  const R = commonJS ? require('./reduction-engine.js') : root.ReductionEngine;
  const subtract = (a, b) => a.map((x, i) => x - b[i]);
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const trace = m => m[0][0] + m[1][1] + m[2][2];
  const cross = (a, b) => [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]];
  const clean = x => Math.abs(x - Math.round(x)) < 1e-10 ? Math.round(x) || 0 : x;

  function classify({sites, tolerance, group, permutations}) {
    if (sites.length === 1) return {geometry: 'atomic'};
    // The longest bond gives a well-conditioned axis, independent of site order for a line.
    let start, direction, diameter = 0;
    for (let i = 1; i < sites.length; i++) {
      for (let j = 0; j < i; j++) {
        const delta = subtract(sites[i].position, sites[j].position);
        const length = Math.hypot(...delta);
        if (length > diameter) {
          diameter = length;
          direction = delta;
          start = sites[j].position;
        }
      }
    }
    if (!Number.isFinite(diameter)) throw new E.BasisError('invalid_vector', '分子坐标的跨度超出数值范围。');
    const axis = direction.map(x => x / diameter);
    const linear = sites.every(s => Math.hypot(...cross(subtract(s.position, start), axis)) <= tolerance + 8 * Number.EPSILON * diameter);
    if (!linear) return {geometry: 'nonlinear'};

    // Every isometry of a finite ordered set on a line preserves or reverses its order.
    // This identifies the sign even when coordinates have been rounded by the user.
    const ordered = sites.map((site, index) => ({index, t: dot(subtract(site.position, start), axis)}))
      .sort((a, b) => a.t - b.t).map(entry => entry.index);
    const reversed = ordered.slice().reverse();
    function ambiguousAxis() {
      throw new E.BasisError('vibration_axis', '位置容差下无法确定与点群相容的分子轴，请检查坐标或减小容差。');
    }
    const signs = permutations.map(p => {
      if (ordered.every(i => p[i] === i)) return 1;
      if (ordered.every((i, k) => p[i] === reversed[k])) return -1;
      ambiguousAxis();
    });

    // Average onto the exact invariant line through the symmetry-averaged midpoint.
    // Refuse a line when this projection collapses sites or exceeds position tolerance.
    const midpoint = start.map((x, i) => x + direction[i] / 2);
    const projected = [0, 0, 0], shift = [0, 0, 0];
    group.matrices.forEach((m, op) => {
      const transformed = E.apply(m, axis), moved = subtract(E.apply(m, midpoint), midpoint);
      for (let k = 0; k < 3; k++) {
        projected[k] += signs[op] * transformed[k] / group.size;
        shift[k] += moved[k] / group.size;
      }
    });
    const norm = Math.hypot(...projected);
    if (!(norm >= 1e-8)) ambiguousAxis();
    const exactAxis = projected.map(x => x / norm);
    const center = midpoint.map((x, k) => x + shift[k]);
    const offsets = ordered.map(i => subtract(sites[i].position, center));
    const parameters = offsets.map(point => dot(point, exactAxis));
    const reversible = signs.includes(-1);
    let previous = -Infinity;
    for (const [k, point] of offsets.entries()) {
      const t = reversible ? parameters[k] / 2 - parameters[parameters.length - 1 - k] / 2 : parameters[k];
      const deviation = Math.hypot(...point.map((x, d) => x - t * exactAxis[d]));
      if (!(t - previous > tolerance && deviation <= tolerance + 8 * Number.EPSILON * diameter)) ambiguousAxis();
      previous = t;
    }
    return {geometry: 'linear', signs};
  }

  // Six real coordinates in an orthonormal Frobenius basis. In particular the
  // xy seed has equal entries 1/√2 at (x,y) and (y,x).
  const tensorComponents = [[0,0], [1,1], [2,2], [0,1], [0,2], [1,2]];
  function asTensor(coordinates) {
    const matrix = Array.from({length: 3}, () => [0, 0, 0]);
    tensorComponents.forEach(([i, j], k) => {
      matrix[i][j] = matrix[j][i] = coordinates[k] * (i === j ? 1 : Math.SQRT1_2);
    });
    return matrix;
  }
  const tensorSeeds = tensorComponents.map((_, k) => {
    const coordinates = Array(6).fill(0);
    coordinates[k] = 1;
    return asTensor(coordinates);
  });

  // Each column is the image of a Cartesian seed under the real character
  // projector, expressed in orthonormal coordinates.
  function projectedBasis(images, weights, expectedRank) {
    const basis = [];
    for (const [column, seed] of images[0].entries()) {
      const vector = seed.map(() => 0);
      for (const [op, weight] of weights.entries()) {
        images[op][column].forEach((value, i) => { vector[i] += weight * value; });
      }
      for (const axis of basis) {
        const overlap = axis.reduce((sum, value, i) => sum + value * vector[i], 0);
        axis.forEach((value, i) => { vector[i] -= overlap * value; });
      }
      const length = Math.hypot(...vector);
      if (length <= 1e-8) continue;
      const unit = vector.map(x => clean(x / length));
      const sign = Math.sign(unit.find(x => Math.abs(x) > 1e-8));
      basis.push(unit.map(x => x ? sign * x : 0));
    }
    if (basis.length !== expectedRank) {
      throw new E.BasisError('vibration_reduction', '振动或活性表示未通过约化检查。');
    }
    return basis;
  }

  function activityRows(group, indices, table, vibrations, dipole, tensor) {
    const classOf = Array(group.size);
    indices.forEach((source, column) => {
      for (const op of group.classes[source].members) classOf[op] = column;
    });
    const dipoleImages = group.matrices.map(E.transpose);
    const tensorImages = group.matrices.map((m, op) => tensorSeeds.map(seed => {
      const moved = E.matmul(m, E.matmul(seed, dipoleImages[op]));
      return tensorComponents.map(([i, j]) =>
        i === j ? moved[i][i] : (moved[i][j] + moved[j][i]) * Math.SQRT1_2);
    }));
    const activities = [], used = new Set();
    for (let i = 0; i < table.X.length; i++) {
      const multiplicity = vibrations.integer_a[i];
      if (!multiplicity || used.has(i)) continue;
      // Real displacements pair a complex irrep with its conjugate at the same frequency.
      const conjugate = table.X[i].map(R.conj);
      const j = table.X.findIndex(row => row.every((v, k) => R.abs(R.add(v, R.mul(-1, conjugate[k]))) < 1e-8));
      if (j < 0 || vibrations.integer_a[j] !== multiplicity || dipole.integer_a[j] !== dipole.integer_a[i] || tensor.integer_a[j] !== tensor.integer_a[i]) {
        throw new E.BasisError('vibration_reduction', '振动或活性表示未通过约化检查。');
      }
      used.add(j);
      const irreps = j === i ? [table.irreps[i]] : [table.irreps[i], table.irreps[j]];
      const degeneracy = irreps.length * table.X[i][0];
      // For a conjugate pair, the sum of its two central projectors has
      // real weights 2 d Re(χ) / |G| and selects the whole real partner space.
      const weights = classOf.map(k => degeneracy * R.z(table.X[i][k]).re / group.size);
      const irDirections = projectedBasis(dipoleImages, weights, dipole.integer_a[i] * degeneracy);
      const ramanTensors = projectedBasis(tensorImages, weights, tensor.integer_a[i] * degeneracy).map(asTensor);
      activities.push({irreps, multiplicity, degeneracy, degreesOfFreedom: multiplicity * degeneracy,
        irActive: dipole.integer_a[i] > 0, ramanActive: tensor.integer_a[i] > 0, irDirections, ramanTensors});
    }
    return activities;
  }

  function prepareGeometry(spec) {
    const origin = spec?.vibrationOrigin;
    if (origin !== undefined && origin !== 'input' && origin !== 'centroid') {
      throw new E.BasisError('invalid_origin', '坐标单位或对称原点设置无效。');
    }
    const action = E.siteAction(spec, {useCentroid: origin === 'centroid'});
    return {action, ...classify(action)};
  }

  function review(spec) {
    const {action, geometry} = prepareGeometry(spec);
    const {group, sites, permutations, origin} = action;
    let maxDeviation = 0;
    permutations.forEach((targets, op) => {
      sites.forEach((site, i) => {
        const moved = E.apply(group.matrices[op], site.position);
        maxDeviation = Math.max(maxDeviation, E.distance(moved, sites[targets[i]].position));
      });
    });
    return {geometry, group: group.name, atomCount: sites.length, operations: group.size, maxDeviation, origin};
  }

  function calculate(spec) {
    const {action, geometry, signs} = prepareGeometry(spec);
    const {group, sites, permutations, tolerance} = action;
    const table = R.table(group.name);
    const dipole = group.matrices.map(trace);
    const fixed = permutations.map(p => p.reduce((count, target, i) => count + Number(target === i), 0));
    const displacement = dipole.map((v, i) => fixed[i] * v);
    const rotation = group.matrices.map((m, i) => {
      if (geometry === 'atomic') return 0;
      const parity = Math.sign(dot(m[0], cross(m[1], m[2])));
      // Axial vectors transform by det(R) R. For a line, rotation about its own
      // axis has zero displacement and its 1-D representation must be removed.
      const axisCharacter = signs ? signs[i] : 0;
      return parity * (dipole[i] - axisCharacter);
    });
    const vibration = displacement.map((v, i) => v - dipole[i] - rotation[i]);
    // Character of Sym²(V) = (χ(g)² + χ(g²))/2, including the isotropic trace.
    const tensor = dipole.map((v, i) => (v * v + dipole[group.multiply[i][i]]) / 2);

    const {indices} = A.mapping(group.name);
    function classVector(values) {
      return indices.map(source => {
        const {members, representative} = group.classes[source];
        const value = values[representative];
        if (!members.every(i => Math.abs(values[i] - value) < 1e-7)) {
          throw new E.BasisError('class_trace', '同一共轭类的特征标不一致。');
        }
        return clean(value);
      });
    }
    function reduce(values) {
      const result = R.reduce(group.name, classVector(values));
      if (!result.valid) throw new E.BasisError('vibration_reduction', '振动或活性表示未通过约化检查。');
      return result;
    }
    const translations = reduce(dipole), rotations = reduce(rotation), cartesian = reduce(displacement);
    const vibrations = reduce(vibration), ramanTensor = reduce(tensor);
    const degreesOfFreedom = 3 * sites.length - 3 - ({atomic: 0, linear: 2, nonlinear: 3})[geometry];
    if (vibrations.dimension !== degreesOfFreedom) throw new E.BasisError('dimension_check', '单位操作特征标与维数不符。');
    const activities = activityRows(group, indices, table, vibrations, translations, ramanTensor);
    const counts = {irBands: 0, ramanBands: 0, silentBands: 0, totalBands: 0, irComponents: 0, ramanComponents: 0};
    for (const row of activities) {
      counts.totalBands += row.multiplicity;
      if (row.irActive) { counts.irBands += row.multiplicity; counts.irComponents += row.degreesOfFreedom; }
      if (row.ramanActive) { counts.ramanBands += row.multiplicity; counts.ramanComponents += row.degreesOfFreedom; }
      if (!row.irActive && !row.ramanActive) counts.silentBands += row.multiplicity;
    }
    return {schemaVersion: 1, group: group.name, geometry, atomCount: sites.length, degreesOfFreedom, origin: action.origin,
      classes: table.classes.slice(), classSizes: table.sizes.slice(), fixedAtoms: classVector(fixed), positionTolerance: tolerance,
      cartesian, translations, rotations, vibrations, irDipole: translations, ramanTensor, activities, counts};
  }

  function template(name) {
    let sites, group;
    if (name === 'methane') {
      group = 'Td';
      sites = [{id: 'C', kind: 'C', position: [0, 0, 0]},
        ...E.orbit(group, [0, 0, 1]).positions.map((position, i) => ({id: 'H' + (i + 1), kind: 'H', position}))];
    } else if (name === 'carbon-dioxide') {
      group = 'D4h';
      sites = [{id: 'C', kind: 'C', position: [0, 0, 0]},
        {id: 'O1', kind: 'O', position: [0, 0, -1]}, {id: 'O2', kind: 'O', position: [0, 0, 1]}];
    } else throw new E.BasisError('template', '未知示例。');
    return {schemaVersion: 1, group, sites, functions: [], tolerance: 1e-6, note: ''};
  }

  const api = {review, calculate, template};
  if (commonJS) module.exports = api;
  root.VibrationEngine = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
