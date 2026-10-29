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
