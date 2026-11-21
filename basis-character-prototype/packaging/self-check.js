// 纯 ECMAScript 计算检查，与窗口渲染和系统对话框验收分开。
(function () {
  const assert = (ok, message) => { if (!ok) throw Error(message); };
  const names = ['benzene','water','central-c2v','central-oh','icosahedron','central-d-c2v','central-d-oh'];
  const dimensions = [30,2,3,3,12,5,5], blocks = [4,1,3,1,1,5,2];
  const examples = names.map((name,i) => {
    const r = BasisEngine.calculate(BasisEngine.template(name));
    const reduced = ReductionEngine.integrate(r, ReducerAdapter);
    assert(r.dimension === dimensions[i] && r.blocks.length === blocks[i] && reduced.total.valid, name);
    return {name, dimension:r.dimension, blocks:r.blocks.length, characters:r.totalCharacters, checks:r.checks,
      reduced:reduced.total.valid, terms:reduced.total.terms, reductionResidual:reduced.total.integer_residual};
  });
  assert(JSON.stringify(examples[0].characters) === '[30,0,0,0,2,0,0,0,0,18,0,6]', 'benzene characters');
  const water = BasisEngine.template('water');
  const salc = SalcEngine.calculate(BasisEngine.calculate(water));
  assert(salc.spaces.map(s => s.irrep).join(',') === 'A1,B1', 'water SALC symmetry');
  for (const [i, space] of salc.spaces.entries()) {
    const [a, b] = space.copies[0].vectors[0].coefficients;
    assert(Math.abs(a*a - .5) < 1e-8 && Math.abs(a*b - (i ? -.5 : .5)) < 1e-8, 'water SALC coefficients');
  }
  const spectrum = VibrationEngine.calculate(water);
  assert(spectrum.degreesOfFreedom === 3 && spectrum.counts.irBands === 3 && spectrum.counts.ramanBands === 3, 'water vibrations');
  const isomerCounts = FormulaModels.lookup('C2H6O').candidates.map(candidate => {
    const input = {...candidate, tolerance:1e-6, vibrationOrigin:'centroid'};
    assert(VibrationEngine.review(input).atomCount === 9, candidate.id);
    const {irBands,ramanBands} = VibrationEngine.calculate(input).counts;
    return [irBands,ramanBands];
  });
  assert(JSON.stringify(isomerCounts) === '[[21,21],[17,21]]', 'formula isomer activities');
  const platinum = FormulaModels.lookup('Pt(NH3)2Cl2').candidates;
  assert(platinum.map(c => c.group).join(',') === 'C2v,C2h', 'platinum stereoisomers');
  const ion = FormulaModels.lookup('[Fe(CN)6]4-').candidates[0];
  const ionSpectrum = VibrationEngine.calculate({...ion, tolerance:1e-6, vibrationOrigin:'centroid'});
  assert(ion.charge === -4 && ionSpectrum.degreesOfFreedom === 33 && ionSpectrum.counts.irBands === 4, 'ferrocyanide');
  const groups = BasisEngine.groupNames.map(name => {
    const g = BasisEngine.group(name);
    const pInput = BasisEngine.template('central-c2v'), dInput = BasisEngine.template('central-d-oh');
    pInput.group = dInput.group = name;
    const p = BasisEngine.calculate(pInput), d = BasisEngine.calculate(dInput), a = ReducerAdapter.align(d);
    const error = Math.max(...g.classes.map((c,i) => {
      const m = g.matrices[c.representative], square = BasisEngine.matmul(m,m), tr = m[0][0]+m[1][1]+m[2][2];
      return Math.abs((tr*tr+square[0][0]+square[1][1]+square[2][2])/2-1-d.totalCharacters[i]);
    }));
    const representationError = Math.max(p.checks.representationError, d.checks.representationError);
    assert(p.dimension === 3 && d.dimension === 5 && error < 1e-7 &&
      representationError < 1e-7 && a.classes.length === g.classes.length, name);
    return {group:name, order:g.size, classes:g.classes.length, dimension:p.dimension,
      dDimension:d.dimension, representationError, dTraceError:error, alignedClasses:a.classes.length};
  });
  const tables = ReductionEngine.groupNames.map(name => {
    const table = ReductionEngine.table(name), r = ReductionEngine.reduce(name,table.X[0]);
    assert(r.valid && r.integer_a[0] === 1, name);
    return {group:name, classes:table.classes.length, orthogonalityError:table.orthogonalityError};
  });
  assert(BasisUpdates.compare('0.10.0','0.9.9') > 0, 'numeric update versions');
  const languages = I18n.languages.map(language => { I18n.setLanguage(language); return {language,title:I18n.translate('点群与基函数')}; });
  assert(groups.length === 87 && tables.length === 423 && languages.length === 3 && languages[2].title === 'Point Groups & Basis Functions', 'catalog/language count');
  assert(Math.abs(ReductionEngine.number('sqrt(3)/2') - Math.sqrt(3)/2) < 1e-12, 'expression parser');
  return JSON.stringify({status:'passed', runtime:'Jint (pure ECMAScript)', version:BasisEngine.VERSION, reductionVersion:ReductionEngine.VERSION,
    examples, waterSalcChecks:salc.checks, waterVibrationCounts:spectrum.counts, isomerCounts, supportedPointGroups:groups.length, expandedGroupChecks:groups,
    reductionTables:tables, languages, reductionIntegrated:true, uiLaunched:false});
})();
