import { DEFAULTS, buildRing, toSTL } from './geometry.js';
for (const k of Object.keys(DEFAULTS)) {
  const sh = buildRing(k, DEFAULTS[k]);
  let nt = 0;
  for (const s of sh) {
    if (![...s.pos.slice(0, 3000)].every(Number.isFinite)) throw new Error(k + ': NaN');
    if (!(s.volume > 0)) throw new Error(`${k}: non-positive volume ${s.volume}`);
    nt += s.idx.length / 3;
  }
  const stl = toSTL(sh);
  if (stl.byteLength !== 84 + nt * 50) throw new Error(k + ': bad STL size');
  console.log(k, 'ok', sh.length, 'shells', nt, 'tris', sh.reduce((a, s) => a + s.volume, 0).toFixed(1), 'mm3');
}
