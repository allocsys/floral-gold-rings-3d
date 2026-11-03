import { DEFAULTS, buildRing, toSTL } from './geometry.js';
for (const k of Object.keys(DEFAULTS)) {
  const t0 = Date.now();
  const sh = buildRing(k, DEFAULTS[k], 'draft');
  let nt = 0;
  for (const s of sh) {
    for (let i = 0; i < s.pos.length; i++) if (!Number.isFinite(s.pos[i])) throw new Error(`${k}: non-finite coordinate`);
    if (!(s.volume > 0)) throw new Error(`${k}: non-positive volume ${s.volume}`);
    nt += s.idx.length / 3;
  }
  if (toSTL(sh).byteLength !== 84 + nt * 50) throw new Error(`${k}: bad STL size`);
  console.log(k, 'ok', sh.length, 'shells', nt, 'tris', Date.now() - t0, 'ms');
}
// ultra quality (relief bands only): finer mesh, same shape (volume within 0.3% of fine)
for (const k of ['band1', 'band2']) {
  const f = buildRing(k, DEFAULTS[k], 'fine'), u = buildRing(k, DEFAULTS[k], 'ultra');
  const vf = f.reduce((a, s) => a + s.volume, 0), vu = u.reduce((a, s) => a + s.volume, 0), tf = f.reduce((a, s) => a + s.idx.length, 0), tu = u.reduce((a, s) => a + s.idx.length, 0);
  if (!(tu > 3 * tf)) throw new Error(`${k}: ultra not finer (${tu} vs ${tf} indices)`);
  if (Math.abs(vu / vf - 1) > 0.003) throw new Error(`${k}: ultra volume ${vu} vs fine ${vf}`);
  console.log(k, 'ultra ok', tu / 3, 'tris vs fine', tf / 3, 'vol ratio', (vu / vf).toFixed(5));
}
