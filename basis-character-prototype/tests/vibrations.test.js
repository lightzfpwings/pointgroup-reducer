'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine.js');
const V = require('../vibrations.js');

const atom = (id, kind, position) => ({id, kind, position});
const terms = representation => Object.fromEntries(representation.terms.map(t => [t.irrep, t.multiplicity]));
function coordinated(group, centre, ligand, seed) {
  return {group, sites: [atom(centre, centre, [0,0,0]),
    ...E.orbit(group, seed).positions.map((p, i) => atom(ligand + i, ligand, p))]};
}

test('water vibrations use all three nuclei, independent of AO selection', () => {
  const water = E.template('water');
  const r = V.calculate({group: water.group, sites: water.sites});
  assert.deepEqual(V.calculate(water), r);
  assert.equal(r.geometry, 'nonlinear');
  assert.deepEqual(r.fixedAtoms, [3, 1, 3, 1]);
  assert.deepEqual(r.cartesian.c, [9, -1, 3, 1]);
  assert.deepEqual(terms(r.vibrations), {A1: 2, B1: 1}); // molecular plane is xz
  assert.deepEqual(r.counts, {irBands: 3, ramanBands: 3, silentBands: 0, totalBands: 3, irComponents: 3, ramanComponents: 3});
  const yz = {...water, sites: water.sites.map(s => ({...s, position: [s.position[1], s.position[0], s.position[2]]}))};
  assert.deepEqual(terms(V.calculate(yz).vibrations), {A1: 2, B2: 1});
});

test('methane distinguishes 9 coordinates, 4 fundamental bands and 2 IR-active bands', () => {
  // NIST CCCBDB experimental fundamental assignments: https://cccbdb.nist.gov/exp2x.asp?casno=74828
  const r = V.calculate(coordinated('Td', 'C', 'H', [0,0,1]));
  assert.deepEqual(terms(r.vibrations), {A1: 1, E: 1, T2: 2});
  assert.deepEqual(terms(r.rotations), {T1: 1});
  assert.deepEqual(terms(r.irDipole), {T2: 1});
  assert.deepEqual(terms(r.ramanTensor), {A1: 1, E: 1, T2: 1});
  assert.deepEqual(r.counts, {irBands: 2, ramanBands: 4, silentBands: 0, totalBands: 4, irComponents: 6, ramanComponents: 9});
});

test('CO2 in D4h retains the doubly degenerate bend and omits the axial rotation', () => {
  const s = coordinated('D4h', 'C', 'O', [0,0,1]);
  const r = V.calculate(s);
  assert.equal(r.geometry, 'linear');
  assert.equal(r.degreesOfFreedom, 4);
  assert.deepEqual(terms(r.rotations), {Eg: 1});
  assert.deepEqual(terms(r.vibrations), {A1g: 1, A2u: 1, Eu: 1});
  assert.deepEqual(r.activities.map(a => [a.degeneracy,a.irActive,a.ramanActive]), [[1,false,true],[1,true,false],[2,true,false]]);
  assert.deepEqual(r.counts, {irBands: 2, ramanBands: 1, silentBands: 0, totalBands: 3, irComponents: 3, ramanComponents: 1});
  // The smaller group resolves the two bending coordinates into distinct finite-group rows.
  assert.equal(V.calculate({...s, group: 'D2h'}).counts.totalBands, 4);
});

test('linear geometry can have an arbitrary direction and an offset from the origin', () => {
  for (const sites of [
    [atom('a','C',[2,3,0]), atom('b','O',[5,7,0])],  // line in the mirror plane
    [atom('a','H',[2,3,1]), atom('b','H',[2,3,-1])] // line normal to mirror plane
  ]) {
    const r = V.calculate({group: 'Cs', sites});
    assert.equal(r.geometry, 'linear');
    assert.deepEqual(terms(r.vibrations), {"A'": 1});
    assert.equal(r.rotations.dimension, 2);
  }
  const sites = [atom('a','H',[0,0,-1]), atom('b','H',[0,0,1])];
  const h2 = V.calculate({group:'D4h', sites});
  assert.deepEqual([h2.counts.irBands, h2.counts.ramanBands], [0,1]);
  const hd = V.calculate({group:'C4v', sites:[sites[0], {...sites[1], kind:'D'}]});
  assert.deepEqual([hd.counts.irBands, hd.counts.ramanBands], [1,1]);
});

test('complex-conjugate irreps count as one real degenerate frequency per pair', () => {
  const s = coordinated('C3', 'N', 'H', [1,0,1]);
  const r = V.calculate(s);
  assert.deepEqual(terms(r.vibrations), {A: 2, 'E1+': 2, 'E1-': 2});
  assert.deepEqual(r.activities[1], {irreps:['E1+','E1-'], multiplicity:2, degeneracy:2, degreesOfFreedom:4, irActive:true, ramanActive:true});
  assert.equal(r.counts.totalBands, 4);
});

test('octahedral SF6 has mutually exclusive activities and one silent triplet', () => {
  const r = V.calculate(coordinated('Oh', 'S', 'F', [1,0,0]));
  assert.deepEqual(terms(r.vibrations), {A1g:1, Eg:1, T2g:1, T1u:2, T2u:1});
  assert.ok(r.activities.every(row => !(row.irActive && row.ramanActive)));
  assert.deepEqual(r.counts, {irBands:2, ramanBands:3, silentBands:1, totalBands:6, irComponents:6, ramanComponents:6});
});

test('single atoms, incomplete symmetries and invalid/missing atom sets', () => {
  const r = V.calculate({group:'Ih', sites:[atom('He','He',[0,0,0])]});
  assert.equal(r.geometry, 'atomic');
  assert.equal(r.degreesOfFreedom, 0);
  assert.equal(r.rotations.dimension, 0);
  assert.deepEqual(r.activities, []);
  const bad = E.template('water');
  bad.sites[2].kind = 'D';
  assert.throws(() => V.calculate(bad), {code:'missing_site'});
  assert.throws(() => V.calculate({group:'C1', sites:[]}), {code:'site_count'});
  assert.throws(() => V.calculate({group:'C1', sites:[atom('a','H',[0,0,0]), atom('b','H',[0,0,0])]}), {code:'coincident_sites'});
});

test('finite-group spectrum checks dimensions and counts across all supported group families', () => {
  for (const group of E.groupNames) {
    const spec = {group, sites:E.orbit(group,[0.32,0.47,0.73]).positions.map((p,i) => atom('X'+i,'X',p))};
    const r = V.calculate(spec);
    assert.equal(r.cartesian.dimension, 3 * spec.sites.length, group);
    assert.equal(r.rotations.dimension + r.translations.dimension + r.degreesOfFreedom, r.cartesian.dimension, group);
    assert.equal(r.ramanTensor.dimension, 6, group);
    assert.equal(r.activities.reduce((sum,row) => sum + row.degreesOfFreedom,0), r.degreesOfFreedom, group);
  }
});

test('linear geometry uses the actual site ordering and resolves the symmetry axis within tolerance', () => {
  // Distinct site kinds can each match themselves under reflection while the fitted bond
  // exceeds 45° to the plane. Their symmetry-averaged separation is below tolerance.
  const unresolved = {group:'Cs', tolerance:0.01, sites:[
    atom('a','H',[0,0,0.0045]), atom('b','F',[0.007,0,-0.0045])
  ]};
  assert.throws(() => V.calculate(unresolved), {code:'vibration_axis'});
  unresolved.sites[1].position[0] = 0.02;
  assert.deepEqual(terms(V.calculate(unresolved).vibrations), {"A'":1});

  const bent = {group:'C1', tolerance:0.0001, sites:[
    atom('c','C',[0,0.0002,0]), atom('l','O',[-1,0,0]), atom('r','O',[1,0,0])
  ]};
  assert.equal(V.calculate(bent).degreesOfFreedom, 3);
  bent.sites[0].position[1] = 0.00005;
  assert.equal(V.calculate(bent).degreesOfFreedom, 4);
});

test('geometry-only spectroscopy templates run directly and return independent project inputs', () => {
  for (const [name, group, geometry, count, irBands, ramanBands] of [
    ['methane', 'Td', 'nonlinear', 5, 2, 4], ['carbon-dioxide', 'D4h', 'linear', 3, 2, 1]
  ]) {
    const input = V.template(name), result = V.calculate(input);
    assert.deepEqual(input.functions, []);
    assert.deepEqual([result.group,result.geometry,result.atomCount,result.counts.irBands,result.counts.ramanBands], [group,geometry,count,irBands,ramanBands]);
    input.sites.pop();
    assert.equal(V.template(name).sites.length, count);
  }
  assert.throws(() => V.template('unknown'), {code:'template'});
});
