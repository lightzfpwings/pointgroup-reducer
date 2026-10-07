/* 独立适配器：只重排 c，不调用约化器，也不改变引擎的共轭类。 */
(function(root) {
  'use strict';
  const E = typeof module !== 'undefined' && module.exports ? require('./engine.js') : root.BasisEngine;
  const catalog = typeof module !== 'undefined' && module.exports ? require('./reducer-catalog.js') : root.ReducerCatalog;
  const polyhedral = {
    T: ['E', 'C₃⁺', 'C₃⁻', 'C₂'],
    Th: ['E', 'C₃⁺', 'C₃⁻', 'C₂', 'i', 'i·C₃⁺', 'i·C₃⁻', 'i·C₂'],
    Td: ['E', 'C₃', 'C₂', 'S₄', 'σᵈ'],
    O: ['E', 'C₃', 'C₂(坐标轴)', 'C₄', 'C₂(棱轴)'],
    Oh: ['E', 'C₃', 'C₂(坐标轴)', 'C₄', 'C₂(棱轴)', 'i', 'i·C₃', 'i·C₂(坐标轴)', 'i·C₄', 'i·C₂(棱轴)'],
    I: ['E', 'C₅', 'C₅²', 'C₃', 'C₂'],
    Ih: ['E', 'C₅', 'C₅²', 'C₃', 'C₂', 'i', 'i·C₅', 'i·C₅²', 'i·C₃', 'i·C₂']
  };
  function mapping(name) {
    const g = E.group(name), target = catalog.groups[name];
    if (!target || target.h !== g.size || target.classes.length !== g.classes.length) throw new Error('原模块点群快照与当前群不一致。');
    // 轴向群按同一 xyz 中的实际矩阵匹配；多面体参考矩阵仅编码角度/宇称，
    // 必须使用明确的类对应约定，保留 C3 正负及两类 C2，不能用 trace 猜类。
    const indices = target.classes.map((_, j) => {
      if (polyhedral[name]) return g.classes.findIndex(c => c.label === polyhedral[name][j]);
      const matrix = target.representatives[j];
      const op = g.matrices.findIndex(m => m.flat().every((v, k) => Math.abs(v - matrix.flat()[k]) < 1e-8));
      return g.classes.findIndex(c => c.members.includes(op));
    });
    if (indices.some(i => i < 0) || new Set(indices).size !== indices.length || indices.some((i, j) => g.classes[i].size !== target.class_sizes[j])) throw new Error('无法唯一核对原模块的共轭类映射；未输出对齐向量。');
    return { target, indices, method: polyhedral[name] ? 'explicit polyhedral class correspondence' : 'actual spatial representative matrix membership' };
  }
  function align(result) {
    if (!result || result.status !== 'valid') throw new Error('需要通过验证的特征标结果。');
    const {target, indices, method} = mapping(result.group), g = E.group(result.group);
    if (result.classes.length !== g.classes.length || result.classes.some((c, i) => c.id !== g.classes[i].id || c.label !== g.classes[i].label || c.size !== g.classes[i].size)) throw new Error('结果的类顺序不符合引擎约定，请重新计算。');
    const reorder = values => {
      if (!Array.isArray(values) || values.length !== indices.length || values.some(x => !Number.isFinite(x))) throw new Error('特征标向量长度或数值无效。');
      return indices.map(i => values[i]);
    };
    return {
      schema_version: 1, application: 'basis-character-reducer-bridge', point_group: result.group,
      h: target.h, classes: target.classes.slice(), class_sizes: target.class_sizes.slice(),
      c: reorder(result.totalCharacters), dimension: result.dimension,
      blocks: result.blocks.map(b => ({id:b.id, label:b.batches.join(' + '), dimension:b.dimension, c:reorder(b.characters)})),
      mapping: indices.map((i, j) => ({target_index:j, target_class:target.classes[j], source_index:i, source_class_id:result.classes[i].id})),
      mapping_method: method, target_provenance: catalog.provenance,
      characters_weighted: false, reductionIntegrated: false,
      note: 'c 按原模块列顺序，每类一个数；不可约分解由原模块执行。'
    };
  }
  const api = {mapping, align};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.ReducerAdapter = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
