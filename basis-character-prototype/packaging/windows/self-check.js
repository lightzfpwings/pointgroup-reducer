// 纯 ECMAScript 计算检查，与窗口渲染和系统对话框验收分开。
(function () {
  const assert = (ok, message) => { if (!ok) throw Error(message); };
  const names = ['benzene','water','central-c2v','central-oh','icosahedron','central-d-c2v','central-d-oh'];
  const dimensions = [30,2,3,3,12,5,5], blocks = [4,1,3,1,1,5,2];
  const examples = names.map((name,i) => {
    const r = BasisEngine.calculate(BasisEngine.template(name));
    const reduced = ReductionEngine.integrate(r, ReducerAdapter);
    assert(r.dimension === dimensions[i] && r.blocks.length === blocks[i] && reduced.total.valid, name);
    return {name, dimension:r.dimension, blocks:r.blocks.length, characters:r.totalCharacters, reductionResidual:reduced.total.integer_residual};
  });
  assert(JSON.stringify(examples[0].characters) === '[30,0,0,0,2,0,0,0,0,18,0,6]', 'benzene characters');
  const groups = BasisEngine.groupNames.map(name => {
    const g = BasisEngine.group(name);
    const pInput = BasisEngine.template('central-c2v'), dInput = BasisEngine.template('central-d-oh');
    pInput.group = dInput.group = name;
    const p = BasisEngine.calculate(pInput), d = BasisEngine.calculate(dInput), a = ReducerAdapter.align(d);
    const error = Math.max(...g.classes.map((c,i) => {
      const m = g.matrices[c.representative], square = BasisEngine.matmul(m,m), tr = m[0][0]+m[1][1]+m[2][2];
      return Math.abs((tr*tr+square[0][0]+square[1][1]+square[2][2])/2-1-d.totalCharacters[i]);
    }));
    assert(p.dimension === 3 && d.dimension === 5 && error < 1e-7 && Math.max(p.checks.representationError,d.checks.representationError) < 1e-7 && a.classes.length === g.classes.length, name);
    return {group:name, dTraceError:error};
  });
  const tables = ReductionEngine.groupNames.map(name => {
    const table = ReductionEngine.table(name), r = ReductionEngine.reduce(name,table.X[0]);
    assert(r.valid && r.integer_a[0] === 1, name);
    return {group:name, orthogonalityError:table.orthogonalityError};
  });
  const languages = I18n.languages.map(language => { I18n.setLanguage(language); return {language,title:I18n.translate('点群与基函数')}; });
  assert(groups.length === 87 && tables.length === 423 && languages.length === 3 && languages[2].title === 'Point Groups & Basis Functions', 'catalog/language count');
  return JSON.stringify({status:'passed',runtime:'Jint (pure ECMAScript)',version:BasisEngine.VERSION,reductionVersion:ReductionEngine.VERSION,examples,supportedPointGroups:groups.length,expandedGroupChecks:groups,reductionTables:tables,languages,reductionIntegrated:true,uiLaunched:false});
})();
