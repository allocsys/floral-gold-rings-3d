// node tools/export_stl.mjs  ->  writes fine-quality STLs into models/
import { writeFileSync, mkdirSync } from 'node:fs';
import { DEFAULTS, GLB_KINDS, buildRing, toSTL } from '../site/geometry.js';
const names = { band1: 'ring_1_wide_band', band2: 'ring_2_band' };
mkdirSync('models', { recursive: true });
for (const k of Object.keys(DEFAULTS).filter(k => !GLB_KINDS.includes(k))) {
  const buf = Buffer.from(toSTL(buildRing(k, DEFAULTS[k], 'fine')));
  writeFileSync(`models/${names[k]}.stl`, buf);
  console.log(names[k], (buf.length / 1e6).toFixed(1), 'MB');
}
