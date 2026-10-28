// Parametric ring geometry (mm). No dependencies, so it runs in browser and Node.
export const DEFAULTS = {
  band1:     { ID: 19, w: 4.5, t: 1.5, n: 8,  fr: 1.1, va: 0.55, gd: 0.15 },
  band2:     { ID: 17, w: 4.0, t: 1.4, n: 7,  fr: 1.0, va: 0.5,  gd: 0.15 },
  solitaire: { ID: 17, w: 2.2, t: 1.3, n: 12, fr: 0.7, va: 0.35, gd: 0.10, stone: 5.2, prongs: 6 },
};
export const LABELS = { band1: 'Wide band', band2: 'Band', solitaire: 'Solitaire' };
export const CONTROLS = [
  ['ID', 'Inner diameter', 14, 24, 0.1],
  ['w', 'Width', 1.5, 8, 0.1],
  ['t', 'Thickness', 0.8, 3, 0.05],
  ['n', 'Flowers around', 3, 20, 1],
  ['fr', 'Flower size', 0.3, 2, 0.05],
  ['va', 'Vine wave', 0, 1.2, 0.05],
  ['gd', 'Engraving depth', 0, 0.4, 0.01],
  ['stone', 'Stone diameter', 3, 8, 0.1, 'solitaire'],
  ['prongs', 'Prongs', 4, 8, 1, 'solitaire'],
];

const mod = (a, b) => ((a % b) + b) % b;
const clip = (x) => Math.min(1, Math.max(0, x));

function torus(P, N, M) {
  const idx = new Uint32Array(N * M * 6); let k = 0;
  for (let i = 0; i < N; i++) for (let j = 0; j < M; j++) {
    const a = i * M + j, b = ((i + 1) % N) * M + j, c = ((i + 1) % N) * M + (j + 1) % M, d = i * M + (j + 1) % M;
    idx[k++] = a; idx[k++] = b; idx[k++] = c; idx[k++] = a; idx[k++] = c; idx[k++] = d;
  }
  return { pos: P, idx };
}

function band(p, shoulderOnly, NT = 720, M = 40) {
  const Ri = p.ID / 2, Ro = Ri + p.t, w = p.w, per = 2 * Math.PI * Ro / p.n;
  const P = new Float32Array(NT * 2 * M * 3);
  for (let i = 0; i < NT; i++) {
    const th = (i / NT) * 2 * Math.PI, s = th * Ro, sc = s % per;
    let mask = 1;
    if (shoulderOnly) {
      const d = Math.abs(mod(th - Math.PI / 2 + Math.PI, 2 * Math.PI) - Math.PI);
      mask = clip((d - 0.45) / 0.25) * clip((2.2 - d) / 0.25);
    }
    const ds = mod(s + per / 2, per) - per / 2;
    const vz0 = p.va * Math.sin(2 * Math.PI * sc / per);
    for (let j = 0; j < M; j++) {
      const z = -w / 2 + (w * j) / (M - 1);
      let disp = -p.gd * Math.exp(-(((z - vz0) / 0.22) ** 2));
      const rho = Math.hypot(ds, z), phi = Math.atan2(z, ds);
      const petal = p.fr * (0.55 + 0.45 * Math.abs(Math.cos(2.5 * phi)));
      if (rho < petal && rho > p.fr * 0.22) disp -= p.gd;
      if (rho < p.fr * 0.22) disp += 0.06;
      if (Math.abs(Math.abs(z) - (w / 2 - 0.3)) < 0.1) disp += 0.07;
      disp *= mask;
      const R = Ro + 0.12 * (1 - (2 * z / w) ** 2) + disp;
      let o = (i * 2 * M + j) * 3;
      P[o] = R * Math.cos(th); P[o + 1] = R * Math.sin(th); P[o + 2] = z;
      const zi = w / 2 - (w * j) / (M - 1);
      const Rin = Ri - 0.08 * (1 - (2 * zi / w) ** 2);
      o = (i * 2 * M + M + j) * 3;
      P[o] = Rin * Math.cos(th); P[o + 1] = Rin * Math.sin(th); P[o + 2] = zi;
    }
  }
  return { shell: torus(P, NT, 2 * M), top: Ro + 0.12 };
}

function revolve(prof, n = 48) {
  const M = prof.length, P = new Float32Array(n * M * 3);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * 2 * Math.PI, c = Math.cos(a), s = Math.sin(a);
    for (let j = 0; j < M; j++) { const o = (i * M + j) * 3; P[o] = prof[j][0] * c; P[o + 1] = prof[j][0] * s; P[o + 2] = prof[j][1]; }
  }
  return torus(P, n, M);
}
// local z-axis -> world +Y, then offset in x / z
function toUp(sh, x0 = 0, z0 = 0) {
  const p = sh.pos;
  for (let i = 0; i < p.length; i += 3) { const x = p[i], y = p[i + 1], z = p[i + 2]; p[i] = x + x0; p[i + 1] = z; p[i + 2] = -y + z0; }
  return sh;
}
function fixWinding(sh) {
  const { pos, idx } = sh; let v = 0;
  for (let i = 0; i < idx.length; i += 3) {
    const a = idx[i] * 3, b = idx[i + 1] * 3, c = idx[i + 2] * 3;
    v += pos[a] * (pos[b + 1] * pos[c + 2] - pos[b + 2] * pos[c + 1])
       - pos[a + 1] * (pos[b] * pos[c + 2] - pos[b + 2] * pos[c]) + pos[a + 2] * (pos[b] * pos[c + 1] - pos[b + 1] * pos[c]);
  }
  sh.volume = Math.abs(v) / 6; // winding is flipped below so the stored volume is the positive, outward one
  if (v < 0) for (let i = 0; i < idx.length; i += 3) { const t = idx[i + 1]; idx[i + 1] = idx[i + 2]; idx[i + 2] = t; }
  return sh;
}

// returns [{pos, idx, kind:'metal'|'stone'}]
export function buildRing(kind, p) {
  const shells = [];
  if (kind !== 'solitaire') {
    shells.push({ ...band(p, false).shell, kind: 'metal' });
  } else {
    const { shell, top } = band(p, true);
    shells.push({ ...shell, kind: 'metal' });
    const sr = p.stone / 2, gy = top + 0.65 * sr;
    shells.push({ ...toUp(revolve([[0, gy + 0.385 * sr], [0.6 * sr, gy + 0.385 * sr], [sr, gy], [sr, gy - 0.06 * sr], [0, gy - 0.675 * sr]], 64)), kind: 'stone' });
    shells.push({ ...toUp(revolve([[0, top - 0.3], [Math.min(1.3, sr * 0.5), top - 0.3], [sr - 0.3, gy - 0.5], [0.9, gy - 0.5], [0, top + 0.6]], 48)), kind: 'metal' });
    for (let k = 0; k < p.prongs; k++) {
      const a = (k * 2 * Math.PI) / p.prongs, rr = sr + 0.05;
      shells.push({ ...toUp(revolve([[0, top - 0.2], [0.32, top - 0.2], [0.28, gy + 0.2], [0.3, gy + 0.35 * sr], [0, gy + 0.44 * sr]], 16), rr * Math.cos(a), rr * Math.sin(a)), kind: 'metal' });
    }
  }
  return shells.map(fixWinding);
}

export function toSTL(shells) {
  let nt = 0; for (const s of shells) nt += s.idx.length / 3;
  const buf = new ArrayBuffer(84 + nt * 50), dv = new DataView(buf); dv.setUint32(80, nt, true);
  let o = 84;
  for (const { pos, idx } of shells) for (let i = 0; i < idx.length; i += 3) {
    const a = idx[i] * 3, b = idx[i + 1] * 3, c = idx[i + 2] * 3;
    const ux = pos[b] - pos[a], uy = pos[b + 1] - pos[a + 1], uz = pos[b + 2] - pos[a + 2];
    const vx = pos[c] - pos[a], vy = pos[c + 1] - pos[a + 1], vz = pos[c + 2] - pos[a + 2];
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const l = Math.hypot(nx, ny, nz) || 1; nx /= l; ny /= l; nz /= l;
    for (const v of [nx, ny, nz]) { dv.setFloat32(o, v, true); o += 4; }
    for (const q of [a, b, c]) for (let k = 0; k < 3; k++) { dv.setFloat32(o, pos[q + k], true); o += 4; }
    o += 2;
  }
  return buf;
}
