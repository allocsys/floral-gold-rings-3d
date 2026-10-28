// node tools/export_stl.mjs  ->  writes fine-quality STLs into models/
import { writeFileSync, mkdirSync } from 'node:fs';
import { DEFAULTS, buildRing, toSTL } from '../site/geometry.js';
const names = { band1: 'ring_1_wide_band', band2: 'ring_2_band', solitaire: 'ring_3_solitaire' };
mkdirSync('models', { recursive: true });
for (const k of Object.keys(DEFAULTS)) {
  const buf = Buffer.from(toSTL(buildRing(k, DEFAULTS[k], 'fine')));
  writeFileSync(`models/${names[k]}.stl`, buf);
  console.log(names[k], (buf.length / 1e6).toFixed(1), 'MB');
}
