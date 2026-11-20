/* Single-frame XYZ input and an offline orthographic molecular viewer. */
(function (root) {
  'use strict';
  const commonJS = typeof module !== 'undefined' && module.exports;
  const E = commonJS ? require('./engine.js') : root.BasisEngine;
  const elements = new Set(('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og D T').split(' '));
  const decimal = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?$/;
  function parseXYZ(text, tolerance) {
    if (text.length > 2 * 1024 * 1024) throw new Error('输入文件不能超过 2 MiB。');
    const lines = text.trim().split(/\r\n?|\n/);
    const count = Number(lines[0]);
    if (!/^\d+$/.test(lines[0].trim()) || count < 1 || count > 120) {
      throw new Error('XYZ 首行应为 1 至 120 的原子数。');
    }
    if (lines.length !== count + 2) {
      throw new E.BasisError('xyz_count', '请载入单帧 XYZ，保留第二行注释，坐标行数须等于首行原子数。', {expected:count, rows:Math.max(lines.length - 2, 0)});
    }
    const sites = lines.slice(2).map((line, i) => {
      const [symbol, ...coordinates] = line.trim().split(/\s+/);
      const kind = symbol.charAt(0).toUpperCase() + symbol.slice(1).toLowerCase();
      if (!elements.has(kind)) throw new E.BasisError('xyz_element', '无法识别 XYZ 元素符号。', {line:i + 3, symbol:symbol.slice(0,24)});
      const position = coordinates.map(value => Number(value.replace(/[dD]/, 'e')));
      if (position.length !== 3 || coordinates.some(value => !decimal.test(value)) || !position.every(Number.isFinite)) {
        throw new E.BasisError('xyz_coordinates', 'XYZ 每个原子需要三个有限的十进制坐标。', {line:i + 3});
      }
      return {id:kind + (i + 1), kind, position};
    });
    E.validateSites({sites, tolerance});
    return {sites, note:lines[1].trim(), coordinateUnit:'angstrom', vibrationOrigin:'centroid'};
  }

  function composition(sites) {
    const counts = new Map();
    for (const {kind} of sites) counts.set(kind, (counts.get(kind) || 0) + 1);
    return formatFormula(counts, true);
  }

  function formatFormula(counts, subscripts = false) {
    const kinds = Array.from(counts.keys()).sort();
    const order = counts.has('C') ? ['C', ...kinds.filter(k => k === 'H'), ...kinds.filter(k => k !== 'C' && k !== 'H')] : kinds;
    return order.map(k => {
      const n = counts.get(k);
      const suffix = n > 1 ? String(n) : '';
      return k + (subscripts ? suffix.replace(/\d/g, d => '₀₁₂₃₄₅₆₇₈₉'[Number(d)]) : suffix);
    }).join('');
  }

  // The middle atom defines the angle. Measurements always use source coordinates.
  function measure(a, b, c) {
    if (!a || !b || a === b) return {};
    const distance = E.distance(a.position, b.position);
    if (!c || c === a || c === b) return {distance};
    const other = E.distance(c.position, b.position);
    if (!distance || !other) return {distance};
    const cosine = a.position.reduce((sum, value, i) =>
      sum + ((value - b.position[i]) / distance) * ((c.position[i] - b.position[i]) / other), 0);
    return {distance, angle:Math.acos(Math.max(-1, Math.min(1, cosine))) * 180 / Math.PI};
  }

  // Single-bond covalent radii in Å for common elements, Cordero et al.,
  // Dalton Trans. (2008), doi:10.1039/B801115J. Lines are only a display aid.
  const radii = {__proto__:null, H:.31, D:.31, T:.31, Li:1.28, Be:.96, B:.84, C:.76, N:.71, O:.66, F:.57,
    Na:1.66, Mg:1.41, Al:1.21, Si:1.11, P:1.07, S:1.05, Cl:1.02, K:2.03, Ca:1.76,
    V:1.53, Cr:1.39, Fe:1.32, Co:1.26, Ni:1.24, Cu:1.32, Zn:1.22, As:1.19, Se:1.20, Br:1.20,
    Mo:1.54, Pd:1.39, Ag:1.45, I:1.39, W:1.62, Pt:1.36, Au:1.36};
  const colors = {__proto__:null, H:'#fcfdff', D:'#d9edff', T:'#b7daff', C:'#354655', N:'#416cca', O:'#d3574b',
    F:'#79b495', Cl:'#559d68', Br:'#a66047', I:'#896aa7', S:'#e4b73d', P:'#dc8f4f'};
  function inferredBonds(sites) {
    const bonds = [];
    sites.forEach((a,i) => {
      for (let j = 0; j < i; j++) {
        const b = sites[j];
        if (!radii[a.kind] || !radii[b.kind]) continue;
        const distance = E.distance(a.position, b.position);
        if (distance > 0 && distance <= 1.2 * (radii[a.kind] + radii[b.kind])) bonds.push([i,j]);
      }
    });
    return bonds;
  }

  const views = {iso:[-0.48,0.34], xy:[0,Math.PI/2], xz:[0,0], yz:[Math.PI/2,0]};
  function createViewer(canvas) {
    let model = [], bonds = [], marked = [], yaw = views.iso[0], pitch = views.iso[1], drag = null;
    const ctx = canvas.getContext('2d');
    function draw() {
      const width = canvas.clientWidth, height = canvas.clientHeight;
      if (!ctx || !width || !height) return;
      const ratio = Math.min(root.devicePixelRatio || 1, 3);
      const w = Math.round(width * ratio), h = Math.round(height * ratio);
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      ctx.setTransform(ratio,0,0,ratio,0,0);
      ctx.clearRect(0,0,width,height);
      const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      const scale = Math.max(1, Math.min(width - 70, height - 60)) / 2;
      function project([x,y,z]) {
        const side = -sy*x + cy*y;
        return [cy*x + sy*y, side*sp + z*cp, -side*cp + z*sp];
      }
      const points = model.map(({site, pos}, i) => {
        const [u,v,depth] = project(pos);
        return {site, i, x:width/2 + scale*u, y:height/2 - scale*v, depth};
      });
      function line(a,b,color,weight) {
        ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y);
        ctx.strokeStyle = color; ctx.lineWidth = weight; ctx.stroke();
      }
      for (const [a,b] of bonds) line(points[a],points[b],'#a9b9bd',3);
      for (let k = 1; k < marked.length; k++) line(points[marked[k-1]],points[marked[k]],'#15736d',2);
      const radius = Math.max(4,Math.min(14,35/Math.sqrt(Math.max(1,points.length))));
      // Paint back to front without changing the atom order used by measurements.
      for (const {site,i,x,y} of points.sort((a,b) => a.depth - b.depth)) {
        const light = ['H','D','T','S','F','P'].includes(site.kind);
        const r = radius * (['H','D','T'].includes(site.kind) ? .81 : 1);
        ctx.beginPath(); ctx.arc(x,y,r,0,2*Math.PI);
        ctx.fillStyle = colors[site.kind] || '#66838e'; ctx.fill();
        ctx.lineWidth = 1; ctx.strokeStyle = '#73848b'; ctx.stroke();
        if (marked.includes(i)) {
          ctx.beginPath(); ctx.arc(x,y,r+3,0,2*Math.PI); ctx.strokeStyle='#15736d'; ctx.lineWidth=2; ctx.stroke();
        }
        if (r >= 7) {
          ctx.font = 'bold 10px sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
          ctx.fillStyle = light ? '#27353c' : '#fff'; ctx.fillText(site.kind,x,y,2*r-2);
        }
        if (model.length <= 20 || marked.includes(i)) {
          ctx.font='11px sans-serif'; ctx.textAlign='left'; ctx.textBaseline='bottom'; ctx.fillStyle='#263943';
          ctx.fillText(site.id,x+r+4,y-r/2,64);
        }
      }
      // Triad uses the file axes, so camera rotations can be related to the group convention.
      const corner = {x:32,y:height-30};
      ['x','y','z'].forEach((label,k) => {
        const axis = [0,0,0]; axis[k] = 1;
        const [u,v] = project(axis), end = {x:corner.x+18*u,y:corner.y-18*v};
        if (Math.hypot(u,v) < .15) return;
        line(corner,end,'#70808b',1);
        ctx.font='10px sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillStyle='#40505a';
        ctx.fillText(label,corner.x+25*u,corner.y-25*v);
      });
    }
    function rotate(dx,dy) { yaw += dx; pitch = Math.max(-Math.PI/2,Math.min(Math.PI/2,pitch+dy)); draw(); }
    canvas.onpointerdown = e => { if (e.button !== 0) return; canvas.setPointerCapture(e.pointerId); drag=[e.clientX,e.clientY]; };
    canvas.onpointermove = e => {
      if (!drag || !canvas.hasPointerCapture(e.pointerId)) return;
      rotate((drag[0]-e.clientX)*.012,(e.clientY-drag[1])*.012); drag=[e.clientX,e.clientY];
    };
    canvas.onlostpointercapture = () => { drag=null; };
    canvas.onkeydown = e => {
      const delta = {ArrowLeft:[-.12,0], ArrowRight:[.12,0], ArrowUp:[0,.12], ArrowDown:[0,-.12]}[e.key];
      if (delta) { e.preventDefault(); rotate(...delta); }
    };
    if (root.ResizeObserver) new root.ResizeObserver(draw).observe(canvas);
    return {
      setModel(sites, angstroms) {
        const center = E.centroid(sites);
        const offsets = sites.map(s => s.position.map((v,k) => v - center[k]));
        const extent = Math.max(0,...offsets.map(v => Math.hypot(...v)));
        model = Number.isFinite(extent) ? sites.map((site,i) => ({site,pos:offsets[i].map(v => v / (extent || 1))})) : [];
        bonds = angstroms && model.length ? inferredBonds(sites) : [];
        marked = []; draw();
      },
      mark(indices) { marked = indices.filter(i => i >= 0 && i < model.length); draw(); },
      view(name) { [yaw,pitch] = views[name]; draw(); }
    };
  }
  const api = {parseXYZ, composition, formatFormula, isElement:kind => elements.has(kind), measure, createViewer};
  if (commonJS) module.exports = api;
  root.MolecularStructure = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
