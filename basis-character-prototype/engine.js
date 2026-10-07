/* Independent geometry/basis engine. No dependency on pointgroup-reducer. */
(function (root) {
  'use strict';
  const EPS = 1e-9;
  const VERSION = '0.4.2';
  class BasisError extends Error {
    constructor(code, message, detail = {}) { super(message); this.name = 'BasisError'; this.code = code; this.detail = detail; }
  }
  const fail = (code, message, detail) => { throw new BasisError(code, message, detail); };
  const eye = () => [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const transpose = m => m[0].map((_, i) => m.map(r => r[i]));
  const matmul = (a, b) => a.map(r => b[0].map((_, j) => r.reduce((s, v, k) => s + v * b[k][j], 0)));
  const apply = (m, v) => m.map(r => r.reduce((s, x, i) => s + x * v[i], 0));
  const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
  const norm = a => Math.sqrt(dot(a, a));
  const distance = (a, b) => norm(a.map((x, i) => x - b[i]));
  const clean = x => Math.abs(x) < 1e-12 ? 0 : Math.abs(x - Math.round(x)) < 1e-12 ? Math.round(x) : x;
  const key = m => m.flat().map(x => Math.round(x * 1e9)).join(',');
  const det = m => m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  const rz = theta => [[Math.cos(theta), -Math.sin(theta), 0], [Math.sin(theta), Math.cos(theta), 0], [0, 0, 1]];
  const diag = (x, y, z) => [[x, 0, 0], [0, y, 0], [0, 0, z]];
  const maxdiff = (a, b) => Math.max(0, ...a.flat().map((v, i) => Math.abs(v - b.flat()[i])));
  function closeGroup(generators) {
    const operations = [eye()], seen = new Set([key(eye())]);
    for (let i = 0; i < operations.length; i++) {
      for (const g of generators) {
        const m = matmul(g, operations[i]).map(r => r.map(clean)), k = key(m);
        if (!seen.has(k)) { seen.add(k); operations.push(m); }
        if (operations.length > 256) fail('group_limit', '空间操作未形成预期的有限点群。');
      }
    }
    return operations;
  }
  const definitions = {
    C1: { generators: [], size: 1, note: '仅单位操作。' },
    Cs: { generators: [diag(1, 1, -1)], size: 2, note: '镜面为 xy。' },
    Ci: { generators: [diag(-1, -1, -1)], size: 2, note: '反演中心为原点。' },
    C2v: { generators: [rz(Math.PI), diag(1, -1, 1)], size: 4, note: 'C₂ 沿 z；镜面为 xz、yz。' },
    C3v: { generators: [rz(2 * Math.PI / 3), diag(1, -1, 1)], size: 6, note: 'C₃ 沿 z；一个垂直镜面为 xz。' },
    C6v: { generators: [rz(Math.PI / 3), diag(1, -1, 1)], size: 12, note: 'C₆ 沿 z；σᵥ 包含 xz，σᵈ 与之错开 30°。' },
    D2h: { generators: [diag(1, -1, -1), diag(-1, 1, -1), diag(-1, -1, -1)], size: 8, note: '三条 C₂ 轴沿 x、y、z；反演中心为原点。' },
    D6h: { generators: [rz(Math.PI / 3), diag(1, -1, -1), diag(-1, -1, -1)], size: 24, note: 'C₆ 沿 z；C₂′ 穿过 +x；σᵥ 包含 xz。苯模板的对位碳位于 x 轴。' },
    Oh: { generators: [rz(Math.PI / 2), [[0, 0, 1], [1, 0, 0], [0, 1, 0]], diag(-1, -1, -1)], size: 48, note: '立方坐标取向；三个 C₄ 轴沿 x、y、z。' }
  };
  const originalGroups = new Set(Object.keys(definitions));
  const sh = diag(1, 1, -1), sv = diag(1, -1, 1), c2x = diag(1, -1, -1), inversion = diag(-1, -1, -1);
  const supportedNames = ['C1', 'Cs', 'Ci'];
  for (const [family, suffix] of [['C', ''], ['C', 'v'], ['C', 'h'], ['D', ''], ['D', 'h'], ['D', 'd']]) {
    for (let n = 2; n <= 12; n++) {
      const name = family + n + suffix, r = rz(2 * Math.PI / n);
      let generators, size;
      if (family === 'C') {
        generators = suffix === 'v' ? [r, sv] : suffix === 'h' ? [r, sh] : [r];
        size = suffix ? 2 * n : n;
      } else {
        generators = suffix === 'd' ? [matmul(rz(Math.PI / n), sh), c2x] : suffix === 'h' ? [r, c2x, sh] : [r, c2x];
        size = suffix ? 4 * n : 2 * n;
      }
      if (!definitions[name]) definitions[name] = { generators, size, axialOrder: suffix === 'd' ? 2 * n : n,
        note: '主轴沿 z；角度 φ 从 +x 向 +y 测量。' + (family === 'D' ? '一条平面内 C₂ 轴沿 x。' : '') + (suffix === 'v' ? '一个垂直镜面为 xz。' : suffix === 'h' ? '水平镜面为 xy。' : suffix === 'd' ? 'S' + (2 * n) + ' 沿 z，镜面平分相邻平面内 C₂ 轴。' : '') };
      supportedNames.push(name);
    }
  }
  for (let n = 2; n <= 12; n++) {
    const name = 'S' + 2 * n;
    definitions[name] = { generators: [matmul(rz(Math.PI / n), sh)], size: 2 * n, axialOrder: 2 * n, note: '旋转反射轴沿 z；生成元为旋转 π/' + n + ' 后对 xy 反射。' };
    supportedNames.push(name);
  }
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  function alignment(axis, xReference) {
    const z = axis.map(v => v / norm(axis));
    const projection = dot(xReference, z), rawX = xReference.map((v, i) => v - projection * z[i]);
    const x = rawX.map(v => v / norm(rawX)), y = cross(z, x);
    return transpose([x, y, z]); // columns are the new frame axes in original coordinates
  }
  const cyclicXYZ = [[0, 0, 1], [1, 0, 0], [0, 1, 0]];
  const tetraFrame = alignment([1, 1, 1], [1, -1, 0]);
  const tetraChange = m => matmul(transpose(tetraFrame), matmul(m, tetraFrame));
  const tetraGenerators = [rz(2 * Math.PI / 3), tetraChange(c2x)];
  definitions.T = { generators: tetraGenerators, size: 12, note: '一条 C₃ 轴沿 z；一个四面体顶点在 +z，另一顶点的 x 分量为 0、y 为负。' };
  definitions.Th = { generators: [...tetraGenerators, inversion], size: 24, note: definitions.T.note + '另含反演。' };
  definitions.Td = { generators: [...tetraGenerators, tetraChange([[0, 1, 0], [1, 0, 0], [0, 0, 1]])], size: 24, note: definitions.T.note + '另含镜面与旋转反射。' };
  definitions.O = { generators: [rz(Math.PI / 2), cyclicXYZ], size: 24, note: '立方坐标取向；三个 C₄ 轴沿 x、y、z。' };
  const phi = (1 + Math.sqrt(5)) / 2;
  const icosaFrame = alignment([0, 1, phi], [1, 0, 0]);
  const icosaGenerators = [rz(2 * Math.PI / 5), matmul(transpose(icosaFrame), matmul(cyclicXYZ, icosaFrame))];
  definitions.I = { generators: icosaGenerators, size: 60, note: '一条 C₅ 轴沿 z，一个二十面体顶点在 +z；由标准顶点 (0,±1,±φ) 的共同坐标变换构造。' };
  definitions.Ih = { generators: [...icosaGenerators, inversion], size: 120, note: definitions.I.note + '另含反演。' };
  supportedNames.push('T', 'Th', 'Td', 'O', 'Oh', 'I', 'Ih');
  const superscript = n => String(n).split('').map(c => '⁰¹²³⁴⁵⁶⁷⁸⁹'[Number(c)]).join('');
  const subscript = n => String(n).split('').map(c => '₀₁₂₃₄₅₆₇₈₉'[Number(c)]).join('');
  const gcd = (a, b) => b ? gcd(b, a % b) : a;
  function piFraction(k, n) {
    if (k === 0) return '0'; const d = gcd(k, n); k /= d; n /= d;
    return (k === 1 ? '' : k) + 'π' + (n === 1 ? '' : '/' + n);
  }
  function rotationLabel(n, k) {
    if (!k) return 'E'; const d = gcd(n, k), order = n / d, power = k / d;
    return 'C' + subscript(order) + (power === 1 ? '' : superscript(power));
  }
  const groupCache = new Map();
  function group(name) {
    if (groupCache.has(name)) return groupCache.get(name);
    const definition = definitions[name];
    if (!definition) fail('unsupported_group', '此独立初版尚未提供该点群的真实空间操作。');
    const matrices = closeGroup(definition.generators);
    if (matrices.length !== definition.size) fail('group_size', '空间点群操作数校验失败。');
    const indexes = new Map(matrices.map((m, i) => [key(m), i]));
    const multiply = matrices.map(a => matrices.map(b => indexes.get(key(matmul(a, b)))));
    if (multiply.some(row => row.some(x => x === undefined))) fail('group_closure', '空间操作不满足群封闭。');
    if (matrices.some(m => maxdiff(matmul(m, transpose(m)), eye()) > EPS)) fail('group_orthogonal', '空间操作不是正交变换。');
    const inverse = matrices.map(m => indexes.get(key(transpose(m))));
    if (inverse.some(i => i === undefined)) fail('group_inverse', '空间操作的逆元校验失败。');
    const remaining = new Set(matrices.map((_, i) => i));
    let classes = [];
    while (remaining.size) {
      const rep = remaining.values().next().value;
      const members = [...new Set(matrices.map((_, h) => multiply[multiply[h][rep]][inverse[h]]))].sort((a, b) => a - b);
      members.forEach(i => remaining.delete(i));
      classes.push({ representative: rep, members, size: members.length });
    }
    function representativeLabel(m, i) {
      if (i === 0) return 'E';
      if (maxdiff(m, diag(-1, -1, -1)) < EPS) return 'i';
      if (name !== 'Oh' && maxdiff(m, diag(1, 1, -1)) < EPS) return 'σₕ(xy)';
      if (!originalGroups.has(name)) {
        const axialOrder = definition.axialOrder;
        if (axialOrder) {
          const planeDet = m[0][0] * m[1][1] - m[0][1] * m[1][0];
          if (planeDet > 0) {
            const angle = (Math.atan2(m[1][0], m[0][0]) + 2 * Math.PI) % (2 * Math.PI);
            const k = Math.round(angle * axialOrder / (2 * Math.PI)) % axialOrder;
            return m[2][2] > 0 ? rotationLabel(axialOrder, k) + '(z)' : 'S(z;φ=' + piFraction(2 * k, axialOrder) + ')';
          }
          const angle = (Math.atan2(m[1][0], m[0][0]) / 2 + Math.PI) % Math.PI;
          const k = Math.round(angle * axialOrder / Math.PI) % axialOrder;
          if (m[2][2] > 0) return k === 0 ? 'σ(xz)' : 2 * k === axialOrder ? 'σ(yz)' : 'σ(φ=' + piFraction(k, axialOrder) + ')';
          return 'C₂(φ=' + piFraction(k, axialOrder) + ')';
        }
        const proper = det(m) > 0, p = proper ? m : m.map(row => row.map(v => -v));
        const tr = p[0][0] + p[1][1] + p[2][2];
        const angle = Math.acos(Math.max(-1, Math.min(1, (tr - 1) / 2)));
        let label = '';
        for (let order = 2; order <= 12 && !label; order++) for (let power = 1; power <= Math.floor(order / 2); power++) {
          if (Math.abs(angle - 2 * Math.PI * power / order) < 1e-8) { label = rotationLabel(order, power); break; }
        }
        if (!label) fail('operation_label', '无法确定实际旋转操作的阶数。');
        if ((name === 'T' || name === 'Th') && label === 'C₃') {
          const candidate = proper ? rz(2 * Math.PI / 3) : matmul(inversion, rz(2 * Math.PI / 3));
          const plus = indexes.get(key(candidate));
          label += classes.find(c => c.members.includes(i)).members.includes(plus) ? '⁺' : '⁻';
        }
        if (name === 'O' && label === 'C₂') label += p.every((row, j) => Math.abs(row[j]) > 0.9) ? '(坐标轴)' : '(棱轴)';
        if (name === 'Td' && !proper) return Math.abs(tr + 1) < EPS ? 'σᵈ' : 'S₄';
        return proper ? label : 'i·' + label;
      }
      const proper = det(m) > 0;
      if (name === 'Oh') {
        const p = proper ? m : m.map(r => r.map(x => -x));
        const tr = p[0][0] + p[1][1] + p[2][2];
        let label;
        if (Math.abs(tr - 1) < EPS) label = 'C₄';
        else if (Math.abs(tr) < EPS) label = 'C₃';
        else if (Math.abs(tr + 1) < EPS) label = p.every((r, j) => Math.abs(r[j]) > 0.9) ? 'C₂(坐标轴)' : 'C₂(棱轴)';
        else label = 'E';
        return proper ? label : 'i·' + label;
      }
      if (name === 'D2h' || name === 'Cs' || name === 'Ci') {
        const labels = [
          [diag(1, -1, -1), 'C₂(x)'], [diag(-1, 1, -1), 'C₂(y)'], [diag(-1, -1, 1), 'C₂(z)'],
          [diag(1, -1, 1), 'σ(xz)'], [diag(-1, 1, 1), 'σ(yz)']
        ];
        return (labels.find(([a]) => maxdiff(a, m) < EPS) || [null, 'g' + i])[1];
      }
      if (name === 'C2v') return maxdiff(m, rz(Math.PI)) < EPS ? 'C₂(z)' : maxdiff(m, diag(1, -1, 1)) < EPS ? 'σᵥ(xz)' : 'σᵥ(yz)';
      if (name === 'D6h') {
        const canonical = [
          [rz(Math.PI / 3), 'C₆'], [rz(2 * Math.PI / 3), 'C₃'], [rz(Math.PI), 'C₂(z)'],
          [diag(1, -1, -1), 'C₂′'], [matmul(rz(Math.PI / 3), diag(1, -1, -1)), 'C₂″'],
          [matmul(diag(-1, -1, -1), rz(Math.PI / 3)), 'S₃'], [matmul(diag(-1, -1, -1), rz(2 * Math.PI / 3)), 'S₆'],
          [diag(-1, 1, 1), 'σᵈ'], [diag(1, -1, 1), 'σᵥ']
        ];
        for (const [canonicalMatrix, label] of canonical) {
          const ci = indexes.get(key(canonicalMatrix));
          if (ci !== undefined && classes.find(c => c.members.includes(i)).members.includes(ci)) return label;
        }
      }
      if (proper) {
        const c = Math.max(-1, Math.min(1, (m[0][0] + m[1][1]) / 2));
        const angle = Math.acos(c);
        return Math.abs(angle - Math.PI / 3) < EPS ? 'C₆' : Math.abs(angle - 2 * Math.PI / 3) < EPS ? 'C₃' : 'C₂(z)';
      }
      if (name === 'C3v') return 'σᵥ';
      // For C6v, conjugacy, not rotation angle alone, separates the mirrors.
      const sv = indexes.get(key(diag(1, -1, 1)));
      return classes.find(c => c.members.includes(i)).members.includes(sv) ? 'σᵥ' : 'σᵈ';
    }
    classes = classes.map(c => ({ ...c, label: representativeLabel(matrices[c.representative], c.representative) }));
    const frequencies = new Map(); classes.forEach(c => frequencies.set(c.label, (frequencies.get(c.label) || 0) + 1));
    const occurrences = new Map(); classes.forEach(c => { if (frequencies.get(c.label) > 1) { const label = c.label, index = (occurrences.get(label) || 0) + 1; occurrences.set(label, index); c.label += ' [' + index + ']'; } });
    const order = name === 'D6h' ? ['E', 'C₆', 'C₃', 'C₂(z)', 'C₂′', 'C₂″', 'i', 'S₃', 'S₆', 'σₕ(xy)', 'σᵈ', 'σᵥ'] : name === 'C2v' ? ['E', 'C₂(z)', 'σᵥ(xz)', 'σᵥ(yz)'] : null;
    if (order) classes.sort((a, b) => order.indexOf(a.label) - order.indexOf(b.label));
    classes.forEach((c, i) => { c.id = name + ':class:' + i; c.display = (c.size > 1 ? c.size : '') + c.label; });
    const result = { name, note: definition.note, matrices, multiply, inverse, classes, generatorIndexes: definition.generators.map(m => indexes.get(key(m))), size: matrices.length };
    groupCache.set(name, result); return result;
  }
  function vector(value, field) {
    if (!Array.isArray(value) || value.length !== 3 || value.some(x => typeof x !== 'number' || !Number.isFinite(x))) fail('invalid_vector', field + '必须是三个有限数。');
    return value.slice();
  }
  function tolerance(spec) {
    const t = spec.tolerance === undefined ? 1e-6 : spec.tolerance;
    if (typeof t !== 'number' || !Number.isFinite(t) || t < 1e-10 || t > 0.01) fail('invalid_tolerance', '位置容差需在 1e−10 至 0.01 之间。');
    return t;
  }
  function orbit(name, seed, tol = 1e-6) {
    tolerance({ tolerance: tol }); seed = vector(seed, '代表位置');
    const g = group(name), positions = [], operationToPosition = [];
    for (const m of g.matrices) {
      const point = apply(m, seed).map(clean);
      const matches = positions.map((p, i) => distance(p, point) <= tol ? i : -1).filter(i => i >= 0);
      if (matches.length > 1) fail('ambiguous_orbit', '位置去重存在多个候选，请减小容差。');
      let index = matches[0];
      if (index === undefined) { index = positions.length; positions.push(point); }
      operationToPosition.push(index);
    }
    const stabilizerSize = g.matrices.filter(m => distance(apply(m, seed), seed) <= tol).length;
    if (positions.length * stabilizerSize !== g.size) fail('orbit_stabilizer', '位置容差导致展开数量不一致，请调整容差或坐标。');
    return { positions, count: positions.length, stabilizerSize, operationToPosition };
  }
  function validateSites(spec) {
    const tol = tolerance(spec);
    if (!Array.isArray(spec.sites) || !spec.sites.length || spec.sites.length > 120) fail('site_count', '请输入 1 至 120 个中心。');
    const ids = new Set();
    const sites = spec.sites.map(s => {
      if (!s || typeof s.id !== 'string' || !s.id.trim() || ids.has(s.id)) fail('site_id', '中心编号必须唯一且非空。');
      ids.add(s.id);
      if (typeof s.kind !== 'string' || !s.kind.trim()) fail('site_kind', '每个中心需要元素或等价类型。');
      return { id: s.id, kind: s.kind.trim(), position: vector(s.position, '中心 ' + s.id + ' 的坐标') };
    });
    for (let i = 0; i < sites.length; i++) for (let j = 0; j < i; j++) {
      if (distance(sites[i].position, sites[j].position) <= tol) fail('coincident_sites', '中心 ' + sites[i].id + ' 与 ' + sites[j].id + ' 坐标重合。多个轨道应引用同一个中心。');
    }
    return { sites, tol };
  }
  function positionMaps(g, sites, tol) {
    return g.matrices.map((m, gi) => {
      const mapping = sites.map(s => {
        const target = apply(m, s.position);
        const matches = sites.map((t, i) => t.kind === s.kind && distance(t.position, target) <= tol ? i : -1).filter(i => i >= 0);
        if (matches.length !== 1) fail(matches.length ? 'ambiguous_mapping' : 'missing_site', '操作 g' + gi + ' 后，中心 ' + s.id + (matches.length ? ' 对应多个位置。' : ' 缺少同类型目标位置。'), { operation: gi, matrix: m, site: s.id, target });
        return matches[0];
      });
      if (new Set(mapping).size !== sites.length) fail('mapping_bijection', '操作 g' + gi + ' 未形成一一位置映射。');
      return mapping;
    });
  }
  function inverseSmall(a) {
    const n = a.length, augmented = a.map((r, i) => [...r, ...Array.from({ length: n }, (_, j) => i === j ? 1 : 0)]);
    for (let j = 0; j < n; j++) {
      let p = j; for (let i = j + 1; i < n; i++) if (Math.abs(augmented[i][j]) > Math.abs(augmented[p][j])) p = i;
      if (Math.abs(augmented[p][j]) < 1e-10) fail('dependent_basis', '同一中心和径向类型的函数线性相关，请去掉重复方向或分量。');
      [augmented[p], augmented[j]] = [augmented[j], augmented[p]];
      const scale = augmented[j][j]; augmented[j] = augmented[j].map(v => v / scale);
      for (let i = 0; i < n; i++) if (i !== j) {
        const f = augmented[i][j]; augmented[i] = augmented[i].map((v, k) => v - f * augmented[j][k]);
      }
    }
    return augmented.map(r => r.slice(n));
  }
  const bucketKey = f => JSON.stringify([f.site, f.radial, f.family]);
  // 实球谐 d 的五个正交、单位 Frobenius 范数张量；f(x)=xᵀQx。
  // xy 等非对角项与平方项的相对归一化必须一致，否则混合系数错误。
  const dComponents = ['dxy', 'dxz', 'dyz', 'dx2-y2', 'dz2'];
  const dTensors = {
    dxy: [[0, 1 / Math.sqrt(2), 0], [1 / Math.sqrt(2), 0, 0], [0, 0, 0]],
    dxz: [[0, 0, 1 / Math.sqrt(2)], [0, 0, 0], [1 / Math.sqrt(2), 0, 0]],
    dyz: [[0, 0, 0], [0, 0, 1 / Math.sqrt(2)], [0, 1 / Math.sqrt(2), 0]],
    'dx2-y2': diag(1 / Math.sqrt(2), -1 / Math.sqrt(2), 0),
    dz2: diag(-1 / Math.sqrt(6), -1 / Math.sqrt(6), 2 / Math.sqrt(6))
  };
  function frame(value) {
    if (value === undefined || value === null) return eye();
    if (!Array.isArray(value) || value.length !== 3) fail('invalid_frame', '局部坐标系需要三个轴，按矩阵的列排列。');
    const m = value.map(row => vector(row, '局部坐标系'));
    if (maxdiff(matmul(transpose(m), m), eye()) > 1e-8 || Math.abs(det(m) - 1) > 1e-8) fail('invalid_frame', '局部 x/y/z 轴必须是单位正交的右手坐标系。');
    return m;
  }
  function dTensor(component, localFrame) {
    if (!dComponents.includes(component)) fail('invalid_d_component', '请选择 dxy、dxz、dyz、dx2-y2 或 dz2。');
    const a = frame(localFrame);
    return matmul(a, matmul(dTensors[component], transpose(a)));
  }
  const angularVector = f => f.family === 'd' ? f.tensor.flat() : f.direction;
  function validatedFunctions(spec, sites) {
    if (!Array.isArray(spec.functions) || !spec.functions.length || spec.functions.length > 180) fail('function_count', '请选择 1 至 180 个独立基函数。');
    const siteIds = new Set(sites.map(s => s.id)), ids = new Set(), buckets = new Map();
    const functions = spec.functions.map((f, i) => {
      if (!f || typeof f.id !== 'string' || !f.id.trim() || ids.has(f.id)) fail('function_id', '基函数编号必须唯一且非空。');
      ids.add(f.id);
      if (!siteIds.has(f.site)) fail('unknown_site', '基函数 ' + f.id + ' 引用了不存在的中心。');
      if (typeof f.radial !== 'string' || !f.radial.trim()) fail('missing_radial', '基函数 ' + f.id + ' 需要径向类型标识。');
      if (!['s', 'p', 'd'].includes(f.family)) fail('unsupported_family', '目前支持 s、p 和五维实球谐 d。');
      let direction = null;
      if (f.family === 'p') {
        direction = vector(f.direction, 'p 方向'); const length = norm(direction);
        if (length < 1e-10) fail('zero_direction', 'p 方向不能为零向量。');
        direction = direction.map(x => x / length);
      }
      const result = { id: f.id, site: f.site, radial: f.radial.trim(), family: f.family, direction, batch: String(f.batch || f.family), label: String(f.label || f.id) };
      if (f.family === 'd') {
        result.component = f.component; result.frame = frame(f.frame);
        result.tensor = dTensor(f.component, result.frame);
      }
      const k = bucketKey(result);
      if (!buckets.has(k)) buckets.set(k, []); buckets.get(k).push(i);
      return result;
    });
    const inverses = new Map();
    for (const [k, indexes] of buckets) {
      if (functions[indexes[0]].family === 's') { if (indexes.length > 1) fail('dependent_basis', '同一中心上重复选择了相同径向类型的 s 函数。'); }
      else {
        const family = functions[indexes[0]].family, limit = family === 'd' ? 5 : 3;
        if (indexes.length > limit) fail('dependent_basis', '同一中心和径向类型最多有 ' + limit + ' 个独立 ' + family + ' 函数。');
        inverses.set(k, inverseSmall(indexes.map(i => indexes.map(j => dot(angularVector(functions[i]), angularVector(functions[j]))))));
      }
    }
    return { functions, buckets, inverses };
  }
  function sparseProductError(a, b, c) {
    const n = a.length; let err = 0;
    for (let i = 0; i < n; i++) {
      const row = Array(n).fill(0);
      for (let k = 0; k < n; k++) if (Math.abs(a[i][k]) > 1e-12) for (let j = 0; j < n; j++) if (Math.abs(b[k][j]) > 1e-12) row[j] += a[i][k] * b[k][j];
      for (let j = 0; j < n; j++) err = Math.max(err, Math.abs(row[j] - c[i][j]));
    }
    return err;
  }
  function calculate(spec) {
    if (!spec || typeof spec !== 'object') fail('invalid_spec', '输入项目格式有误。');
    const g = group(spec.group), { sites, tol } = validateSites(spec), maps = positionMaps(g, sites, tol);
    const { functions, buckets, inverses } = validatedFunctions(spec, sites), n = functions.length;
    const siteIndex = new Map(sites.map((s, i) => [s.id, i]));
    let maxResidual = 0;
    const matrices = g.matrices.map((r, gi) => {
      const d = Array.from({ length: n }, () => Array(n).fill(0));
      functions.forEach((f, j) => {
        const targetSite = sites[maps[gi][siteIndex.get(f.site)]].id;
        const targetKey = bucketKey({ ...f, site: targetSite }), targets = buckets.get(targetKey);
        if (!targets) fail('basis_not_closed', '基函数 ' + f.label + ' 在操作 g' + gi + ' 后，目标中心 ' + targetSite + ' 缺少同径向类型的 ' + f.family + ' 函数。', { operation: gi, matrix: r, function: f.id, targetSite });
        if (f.family === 's') { d[targets[0]][j] = 1; return; }
        const moved = f.family === 'd' ? matmul(r, matmul(f.tensor, transpose(r))).flat() : apply(r, f.direction);
        const rhs = targets.map(i => dot(angularVector(functions[i]), moved));
        const coeffs = applyGeneric(inverses.get(targetKey), rhs);
        const recovered = Array(moved.length).fill(0);
        coeffs.forEach((coefficient, k) => angularVector(functions[targets[k]]).forEach((v, a) => { recovered[a] += coefficient * v; }));
        const residual = distance(recovered, moved); maxResidual = Math.max(maxResidual, residual);
        if (residual > 1e-7) fail('basis_not_closed', '基函数 ' + f.label + ' 在操作 g' + gi + ' 后产生所选集合之外的 ' + f.family + ' 分量，请补齐相关函数。', { operation: gi, matrix: r, function: f.id, targetSite, movedAngularVector: moved, residual });
        targets.forEach((i, k) => { d[i][j] = clean(coeffs[k]); });
      });
      return d;
    });
    const identityError = Math.max(...matrices[0].flat().map((v, k) => Math.abs(v - (Math.floor(k / n) === k % n ? 1 : 0))));
    let representationError = identityError;
    for (const generator of g.generatorIndexes) for (let i = 0; i < g.size; i++) representationError = Math.max(representationError, sparseProductError(matrices[generator], matrices[i], matrices[g.multiply[generator][i]]));
    if (representationError > 1e-7) fail('representation_relation', '基函数变换未通过群关系检查。', { representationError });
    const parent = Array.from({ length: n }, (_, i) => i);
    const find = x => parent[x] === x ? x : (parent[x] = find(parent[x]));
    const union = (a, b) => { parent[find(a)] = find(b); };
    const links = [];
    matrices.forEach((d, gi) => d.forEach((row, i) => row.forEach((v, j) => {
      if (i !== j && Math.abs(v) > 1e-9) {
        union(i, j);
        if (functions[i].batch !== functions[j].batch && !links.some(l => l.from === functions[j].batch && l.to === functions[i].batch)) links.push({ from: functions[j].batch, to: functions[i].batch, operation: gi, sourceFunction: functions[j].id, targetFunction: functions[i].id, coefficient: v });
      }
    })));
    const components = new Map();
    functions.forEach((_, i) => { const k = find(i); if (!components.has(k)) components.set(k, []); components.get(k).push(i); });
    const trace = (d, ids) => ids.reduce((s, i) => s + d[i][i], 0);
    const classCharacters = ids => g.classes.map(c => {
      const values = c.members.map(gi => trace(matrices[gi], ids));
      if (Math.max(...values) - Math.min(...values) > 1e-7) fail('class_trace', '封闭空间在同一共轭类内的 trace 不一致。');
      return clean(values[0]);
    });
    const blocks = [...components.values()].map((ids, i) => ({ id: 'block-' + (i + 1), indices: ids, functionIds: ids.map(j => functions[j].id), batches: [...new Set(ids.map(j => functions[j].batch))], dimension: ids.length, characters: classCharacters(ids) }));
    const batchNames = [...new Set(functions.map(f => f.batch))];
    const batches = batchNames.map(name => {
      const indices = functions.map((f, i) => f.batch === name ? i : -1).filter(i => i >= 0), inside = new Set(indices);
      const mixed = links.filter(l => l.from === name || l.to === name);
      const closed = matrices.every(d => indices.every(j => d.every((row, i) => inside.has(i) || Math.abs(row[j]) < 1e-9)));
      return { name, dimension: indices.length, closed, characters: closed ? classCharacters(indices) : null, diagonalContributionsByOperation: matrices.map(d => trace(d, indices)), linkedBatches: [...new Set(mixed.flatMap(l => [l.from, l.to]).filter(b => b !== name))], evidence: mixed };
    });
    const equivalentBlocks = [];
    for (let i = 0; i < blocks.length; i++) for (let j = 0; j < i; j++) {
      if (blocks[i].characters.every((v, k) => Math.abs(v - blocks[j].characters[k]) < 1e-7)) equivalentBlocks.push([blocks[j].id, blocks[i].id]);
    }
    const totalCharacters = classCharacters(Array.from({ length: n }, (_, i) => i));
    if (Math.abs(totalCharacters[g.classes.findIndex(c => c.label === 'E')] - n) > 1e-7) fail('dimension_check', '单位操作特征标与函数数量不一致。');
    return {
      schemaVersion: 1, engineVersion: VERSION, status: 'valid', group: g.name, dimension: n,
      conventions: { origin: [0, 0, 0], action: 'U(g)phi_j = sum_i phi_i D_ij(g)', positionTolerance: tol, angularTolerance: 1e-7, groupNote: g.note, angularBasis: 'real s/p/d; d = symmetric traceless unit-Frobenius tensors; no AO overlap normalization', dAction: 'Q -> R Q R^T; frame columns are local axes in global coordinates', reductionIntegrated: false },
      classes: g.classes.map(c => ({ id: c.id, label: c.label, display: c.display, size: c.size, operationIndexes: c.members, representative: c.representative })),
      operations: g.matrices.map((matrix, i) => ({ id: 'g' + i, matrix, sitePermutation: maps[i], diagonalContributions: functions.map((_, j) => matrices[i][j][j]) })),
      functions, sites, batches, blocks, equivalentBlocks, crossBatchLinks: links, totalCharacters,
      checks: { spatialGroupOrder: g.size, positionBijections: true, basisClosed: true, basisIndependent: true, maxAngularResidual: maxResidual, representationError, representationChecked: 'identity and every generator times every operation', classTracesConsistent: true },
      representationMatrices: matrices
    };
  }
  function applyGeneric(m, v) { return m.map(row => dot(row, v)); }
  function template(name) {
    const sites = [], functions = [];
    const add = (site, radial, family, axis, batch) => functions.push({ id: site.id + ':' + radial + ':' + axis, site: site.id, radial, family, direction: family === 'p' ? ({ px: [1, 0, 0], py: [0, 1, 0], pz: [0, 0, 1] })[axis] : null, batch, label: site.id + ' ' + radial + (family === 'p' ? axis.slice(1) : '') });
    let groupName;
    if (name === 'benzene') {
      groupName = 'D6h';
      for (const [kind, radius] of [['C', 1], ['H', 1.75]]) for (let k = 0; k < 6; k++) sites.push({ id: kind + k, kind, position: [radius * Math.cos(k * Math.PI / 3), radius * Math.sin(k * Math.PI / 3), 0].map(clean) });
      sites.forEach(s => { if (s.kind === 'H') add(s, '1s', 's', 's', 'H 1s'); else { add(s, '2s', 's', 's', 'C 2s'); for (const axis of ['px', 'py', 'pz']) add(s, '2p', 'p', axis, 'C 2' + axis); } });
    } else if (name === 'icosahedron') {
      groupName = 'Ih'; orbit('Ih', [0, 0, 1]).positions.forEach((position, k) => sites.push({ id: 'X' + k, kind: 'X', position }));
      sites.forEach(s => add(s, 's', 's', 's', 'X s'));
    } else if (name === 'water') {
      groupName = 'C2v'; sites.push({ id: 'O0', kind: 'O', position: [0, 0, 0] }, { id: 'H0', kind: 'H', position: [0.8, 0, 0.6] }, { id: 'H1', kind: 'H', position: [-0.8, 0, 0.6] });
      sites.filter(s => s.kind === 'H').forEach(s => add(s, '1s', 's', 's', 'H 1s'));
    } else if (name === 'central-c2v' || name === 'central-oh') {
      groupName = name === 'central-oh' ? 'Oh' : 'C2v'; sites.push({ id: 'X0', kind: 'X', position: [0, 0, 0] });
      ['px', 'py', 'pz'].forEach(axis => add(sites[0], 'p', 'p', axis, 'X ' + axis));
    } else if (name === 'central-d-oh' || name === 'central-d-c2v') {
      groupName = name === 'central-d-oh' ? 'Oh' : 'C2v';
      sites.push({ id: 'M0', kind: 'M', position: [0, 0, 0] });
      dComponents.forEach(component => functions.push({ id: 'M0:3d:' + component, site: 'M0', radial: '3d', family: 'd', component, frame: eye(), batch: 'M ' + component, label: 'M0 3' + component }));
    } else fail('template', '未知示例。');
    return { schemaVersion: 1, group: groupName, tolerance: 1e-6, sites, functions, note: name === 'benzene' ? '理想正六边形；半径为示意值，坐标单位自定，不代表实验键长。' : name === 'icosahedron' ? '单位球面上的正二十面体 12 个顶点；每个顶点一个 s 函数。' : '教学几何；只定义对称变换，不计算能量。' };
  }
  const api = { VERSION, BasisError, groupNames: supportedNames, group, orbit, calculate, template, apply, matmul, transpose, distance, dComponents, dTensor, frame };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.BasisEngine = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
