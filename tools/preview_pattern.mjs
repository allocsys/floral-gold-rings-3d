// writes an unrolled pattern preview (PGM) for a quick visual check: node tools/preview_pattern.mjs band1 out.pgm
import { writeFileSync } from 'node:fs';
import { DEFAULTS, relief, makeQ } from '../site/geometry.js';
const k = process.argv[2] || 'band1', p = DEFAULTS[k], Ro = p.ID / 2 + p.t, per = 2 * Math.PI * Ro / p.n;
const W = 1400, H = Math.round(W * p.w / (2 * per)), e = 0.02;
const q = makeQ(p, per, p.w / 2, e);
const buf = Buffer.alloc(W * H);
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) buf[y * W + x] = 255 * relief(((((x / W) * 2 - 1) * per * 1.5 + per / 2) % per + per) % per - per / 2, (0.5 - y / H) * p.w, q);
writeFileSync(process.argv[3] || 'pattern.pgm', Buffer.concat([Buffer.from(`P5 ${W} ${H} 255\n`), buf]));
