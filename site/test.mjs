// Smoke test (CI, before every Pages deploy): tab table is consistent and every model file the viewer loads exists and is a GLB.
import { readFileSync, existsSync } from 'node:fs';
import { DEFAULTS, LABELS, CONTROLS } from './geometry.js';
const dir = new URL('.', import.meta.url).pathname;
const fail = m => { throw new Error(m); };
for (const k of Object.keys(DEFAULTS)) {
  if (!LABELS[k]) fail(`${k}: no label`);
  if (!(DEFAULTS[k].ID > 0)) fail(`${k}: bad ID`);
}
if (Object.keys(LABELS).length !== Object.keys(DEFAULTS).length) fail('LABELS / DEFAULTS mismatch');
for (const [key, , min, max, step, only] of CONTROLS) {
  if (!(min < max && step > 0)) fail(`control ${key}: bad range`);
  for (const k of [].concat(only || [])) if (!DEFAULTS[k]) fail(`control ${key}: unknown tab ${k}`);
}
const html = readFileSync(dir + 'index.html', 'utf8');
for (const f of ['band_meshy_tile.glb', 'solitaire_meshy2.glb', 'solitaire_6.glb', 'solitaire_6_stone.bin']) {
  if (!html.includes(f)) fail(`index.html does not reference ${f}`);
  if (!existsSync(dir + f)) fail(`missing ${f}`);
  if (f.endsWith('.glb') && readFileSync(dir + f).subarray(0, 4).toString() !== 'glTF') fail(`${f}: not a GLB`);
}
console.log('ok:', Object.keys(DEFAULTS).join(', '));
