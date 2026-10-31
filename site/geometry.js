// Parametric ring geometry (mm). No dependencies: runs in the browser and in Node.
// Both bands (band1, band2) carry the engraved floral relief (relief_band.js, derived from reference/rings_flat.png), repeated REPEATS times around the ring.
import { RELIEF_BAND } from './relief_band.js';
export const DEFAULTS = {
  band1:     { ID: 19, w: 4.5, t: 1.5, relief: 0.4 },
  band2:     { ID: 17, w: 4.0, t: 1.4, relief: 0.4 },
  solitaire: { ID: 17, w: 2.6, t: 1.3, stone: 5.2, prongs: 6 },
};
export const LABELS = { band1: 'Wide band', band2: 'Band', solitaire: 'Solitaire' };
export const CONTROLS = [
  ['ID', 'Inner diameter', 14, 24, 0.1],
  ['w', 'Width', 1.5, 8, 0.1],
  ['t', 'Thickness', 0.8, 3, 0.05],
  ['relief', 'Relief depth', 0, 0.8, 0.05, ['band1', 'band2']],
  ['stone', 'Stone diameter', 3, 8, 0.1, 'solitaire'],
  ['prongs', 'Prongs', 4, 8, 1, 'solitaire'],
];

const TAU = Math.PI * 2;
const mod = (a, b) => ((a % b) + b) % b;

// ---------- mesh helpers ----------
function torus(P, N, M) {
  const idx = new Uint32Array(N * M * 6); let k = 0;
  for (let i = 0; i < N; i++) for (let j = 0; j < M; j++) {
    const a = i * M + j, b = ((i + 1) % N) * M + j, c = ((i + 1) % N) * M + (j + 1) % M, d = i * M + (j + 1) % M;
    idx[k++] = a; idx[k++] = b; idx[k++] = c; idx[k++] = a; idx[k++] = c; idx[k++] = d;
  }
  return { pos: P, idx };
}
const DOME = 0.26;

// ---------- relief map sampling (mip pyramid, bilinear, periodic in u) ----------
const GROUND_COL = [0.14, 0.09, 0.04], GROUND_LO = 0.08, GROUND_HI = 0.55; // viewer tint of the recessed ground (x gold) and the relief-height range it fades over
const REPEATS = 3, FADE = 0.3; // pattern repeats around the ring; relief fades to 0 over the last FADE mm before the rounded edge
let mips = null;
function reliefMips() {
  if (mips) return mips;
  const bin = atob(RELIEF_BAND.b64), a = new Float32Array(bin.length);
  for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i) / 255;
  mips = [{ W: RELIEF_BAND.W, H: RELIEF_BAND.H, a }];
  for (;;) {
    const m = mips[mips.length - 1], W = m.W >> 1, H = m.H >> 1;
    if (W < 8 || H < 4) break;
    const b = new Float32Array(W * H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++)
      b[y * W + x] = (m.a[2 * y * m.W + 2 * x] + m.a[2 * y * m.W + 2 * x + 1] + m.a[(2 * y + 1) * m.W + 2 * x] + m.a[(2 * y + 1) * m.W + 2 * x + 1]) / 4;
    mips.push({ W, H, a: b });
  }
  return mips;
}
function sampleRelief(L, u, v) { // u periodic in [0,1), v in [0,1]
  const x = u * L.W - 0.5, y = Math.min(Math.max(v * L.H - 0.5, 0), L.H - 1);
  const x0 = Math.floor(x), y0 = Math.min(Math.floor(y), L.H - 2), fx = x - x0, fy = y - y0;
  const X0 = mod(x0, L.W), X1 = mod(x0 + 1, L.W), r0 = y0 * L.W, r1 = (y0 + 1) * L.W;
  return (L.a[r0 + X0] * (1 - fx) + L.a[r0 + X1] * fx) * (1 - fy) + (L.a[r1 + X0] * (1 - fx) + L.a[r1 + X1] * fx) * fy;
}
function band(p, solitaire, quality) {
  const rel = !solitaire && p.relief > 0 ? p.relief : 0;
  const step = quality === 'draft' ? 0.12 : rel ? 0.04 : 0.055;
  const Ri = p.ID / 2, Ro = Ri + p.t;
  const NT = Math.max(240, Math.ceil(TAU * Ro / step));
  const rf = 0.32, Kf = quality === 'draft' ? 4 : 8, Wn = 5, Mi = 10;
  const Mo = Math.max(24, Math.ceil(((solitaire ? p.w * 1.3 : p.w) - 2 * rf) / step));
  const S = 2 * Kf + Wn, Mt = Mo + Mi + 2 * S;
  let lv = null;
  if (rel) { // pick the mip level whose pixel size matches the mesh spacing (box prefilter, no aliasing)
    const ms = reliefMips(), pxU = (TAU * Ro / REPEATS) / RELIEF_BAND.W, pxV = p.w / RELIEF_BAND.H;
    lv = ms[Math.min(ms.length - 1, Math.max(0, Math.floor(Math.log2(Math.max(TAU * Ro / NT / pxU, (2 * (p.w / 2 - rf)) / (Mo - 1) / pxV)))))];
  }
  const P = new Float32Array(NT * Mt * 3);
  const C = lv ? new Float32Array(NT * Mt * 3).fill(1) : null; // viewer-only vertex colour: dark bronze ground, full gold on the raised relief
  for (let i = 0; i < NT; i++) {
    const th = (i / NT) * TAU;
    const d = Math.abs(mod(th - Math.PI / 2 + Math.PI, TAU) - Math.PI); // angle from top
    const hwid = solitaire ? (p.w / 2) * (1 + 0.28 * (1 + Math.cos(d)) / 2) : p.w / 2;
    const ct = Math.cos(th), st = Math.sin(th);
    let o = i * Mt * 3;
    const put = (R, z) => { P[o] = R * ct; P[o + 1] = R * st; P[o + 2] = z; o += 3; };
    const zt = (hwid - rf) / hwid, Rt = Ro + DOME * (1 - zt * zt), Rie = Ri - 0.08 * (1 - zt * zt);
    // outer face (domed)
    for (let j = 0; j < Mo; j++) {
      const zn = (-1 + (2 * j) / (Mo - 1)) * zt;
      let R = Ro + DOME * (1 - zn * zn);
      if (lv) { // engraved relief: peaks keep the nominal radius, recesses cut down by `rel` mm, fading out at the rounded edges
        const zf = Math.min(1, (hwid - rf - Math.abs(zn * hwid)) / FADE), fade = zf * zf * (3 - 2 * zf);
        const hv = sampleRelief(lv, mod((i / NT) * REPEATS, 1), (zn / zt + 1) / 2);
        R -= rel * fade * (1 - hv);
        const s = Math.min(1, Math.max(0, (hv - GROUND_LO) / (GROUND_HI - GROUND_LO))), k = s * s * (3 - 2 * s), c = (i * Mt + j) * 3;
        for (let q = 0; q < 3; q++) C[c + q] = GROUND_COL[q] + (1 - GROUND_COL[q]) * (1 - fade + fade * k);
      }
      put(R, zn * hwid);
    }
    // rounded edge: outer fillet, wall, inner fillet (+z side), inner bore, then the -z side back
    const edge = [];
    for (let k = 1; k <= Kf; k++) { const a = (k / Kf) * Math.PI / 2; edge.push([hwid - rf + rf * Math.sin(a), Rt - rf * (1 - Math.cos(a))]); }
    for (let j = 1; j <= Wn; j++) edge.push([hwid, (Rt - rf) + (Rie + rf - (Rt - rf)) * (j / (Wn + 1))]);
    for (let k = 0; k < Kf; k++) { const a = (k / Kf) * Math.PI / 2; edge.push([hwid - rf + rf * Math.cos(a), Rie + rf - rf * Math.sin(a)]); }
    for (const [z, R] of edge) put(R, z);
    for (let j = 0; j < Mi; j++) {
      const zn = zt * (1 - (2 * j) / (Mi - 1));
      put(Ri - 0.08 * (1 - zn * zn), zn * hwid);
    }
    for (let k = S - 1; k >= 0; k--) put(edge[k][1], -edge[k][0]);
  }
  const shell = torus(P, NT, Mt); if (C) shell.col = C;
  return { shell, top: Ro + DOME };
}
function revolve(prof, n = 48) {
  const M = prof.length, P = new Float32Array(n * M * 3);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * TAU, c = Math.cos(a), s = Math.sin(a);
    for (let j = 0; j < M; j++) { const o = (i * M + j) * 3; P[o] = prof[j][0] * c; P[o + 1] = prof[j][0] * s; P[o + 2] = prof[j][1]; }
  }
  return torus(P, n, M);
}
function toUp(sh) { // local z-axis -> world +Y
  const p = sh.pos;
  for (let i = 0; i < p.length; i += 3) { const y = p[i + 1], z = p[i + 2]; p[i + 1] = z; p[i + 2] = -y; }
  return sh;
}
// round-section tube along a smoothed (rho, y, radius) path, rotated about Y by `ang`
function tube(path, ang, segs = 12, sub = 8) {
  const pts = [], n = path.length;
  for (let i = 0; i < n - 1; i++) for (let s = 0; s < sub; s++) {
    const t = s / sub, p0 = path[Math.max(0, i - 1)], p1 = path[i], p2 = path[i + 1], p3 = path[Math.min(n - 1, i + 2)];
    pts.push([0, 1, 2].map(k => 0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3)));
  }
  pts.push(path[n - 1].slice());
  const L = pts.length, P = new Float32Array(L * segs * 3), ca = Math.cos(ang), sa = Math.sin(ang);
  for (let i = 0; i < L; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(L - 1, i + 1)];
    let tx = b[0] - a[0], ty = b[1] - a[1]; const l = Math.hypot(tx, ty) || 1; tx /= l; ty /= l;
    const nx = -ty, ny = tx, rad = Math.max(0, pts[i][2]);
    for (let j = 0; j < segs; j++) {
      const f = (j / segs) * TAU, cx = Math.cos(f) * rad, cz = Math.sin(f) * rad;
      const X = pts[i][0] + cx * nx, Y = pts[i][1] + cx * ny, o = (i * segs + j) * 3;
      P[o] = X * ca - cz * sa; P[o + 1] = Y; P[o + 2] = X * sa + cz * ca;
    }
  }
  const idx = new Uint32Array((L - 1) * segs * 6); let k = 0;
  for (let i = 0; i < L - 1; i++) for (let j = 0; j < segs; j++) {
    const a = i * segs + j, b = (i + 1) * segs + j, c = (i + 1) * segs + (j + 1) % segs, d = i * segs + (j + 1) % segs;
    idx[k++] = a; idx[k++] = b; idx[k++] = c; idx[k++] = a; idx[k++] = c; idx[k++] = d;
  }
  return { pos: P, idx };
}
// faceted round brilliant (8-fold): table, stars, bezels, upper girdle, girdle, pavilion mains, lower girdle
function brilliant(R, gy) {
  const gg = 0.1 * R, hc = 0.32 * R, dp = 0.74 * R;
  const zg0 = gy, zg1 = gy + gg, zt = zg1 + hc, zc = zg0 - dp;
  const pol = (r, a, z) => [r * Math.cos(a), r * Math.sin(a), z];
  const T = [], S = [], Q = [], G = [], B = [];
  for (let k = 0; k < 8; k++) {
    const a = (k * TAU) / 8, am = a + TAU / 16;
    T.push(pol(0.58 * R, a, zt)); S.push(pol(0.80 * R, am, zg1 + 0.45 * hc)); Q.push(pol(0.62 * R, am, zg0 - 0.55 * dp));
  }
  for (let j = 0; j < 16; j++) { const a = (j * TAU) / 16; G.push(pol(R, a, zg1)); B.push(pol(R, a, zg0)); }
  const C = [0, 0, zc], Tc = [0, 0, zt], cen = [0, 0, (zt + zc) / 2], tris = [];
  for (let k = 0; k < 8; k++) {
    const k1 = (k + 1) % 8, km = (k + 7) % 8;
    tris.push([Tc, T[k], T[k1]], [T[k], T[k1], S[k]]);                      // table, stars
    tris.push([T[k], S[km], G[2 * k]], [T[k], G[2 * k], S[k]]);              // bezel kites
    tris.push([S[k], G[2 * k], G[2 * k + 1]], [S[k], G[2 * k + 1], G[(2 * k + 2) % 16]]); // upper girdle
    tris.push([C, Q[km], B[2 * k]], [C, B[2 * k], Q[k]]);                    // pavilion mains
    tris.push([Q[k], B[2 * k], B[2 * k + 1]], [Q[k], B[2 * k + 1], B[(2 * k + 2) % 16]]); // lower girdle
  }
  for (let j = 0; j < 16; j++) { const j1 = (j + 1) % 16; tris.push([G[j], G[j1], B[j1]], [G[j], B[j1], B[j]]); }
  const pos = new Float32Array(tris.length * 9), idx = new Uint32Array(tris.length * 3);
  tris.forEach((t, i) => {
    const [a, b, c] = t, u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    const n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const m = [(a[0] + b[0] + c[0]) / 3 - cen[0], (a[1] + b[1] + c[1]) / 3 - cen[1], (a[2] + b[2] + c[2]) / 3 - cen[2]];
    const o = n[0] * m[0] + n[1] * m[1] + n[2] * m[2] < 0 ? [a, c, b] : [a, b, c]; // convex: orient outward
    o.forEach((q, k) => { pos.set(q, i * 9 + k * 3); idx[i * 3 + k] = i * 3 + k; });
  });
  return { pos, idx };
}
function fixWinding(sh) {
  const { pos, idx } = sh; let v = 0;
  for (let i = 0; i < idx.length; i += 3) {
    const a = idx[i] * 3, b = idx[i + 1] * 3, c = idx[i + 2] * 3;
    v += pos[a] * (pos[b + 1] * pos[c + 2] - pos[b + 2] * pos[c + 1])
       - pos[a + 1] * (pos[b] * pos[c + 2] - pos[b + 2] * pos[c]) + pos[a + 2] * (pos[b] * pos[c + 1] - pos[b + 1] * pos[c]);
  }
  sh.volume = Math.abs(v) / 6;
  if (v < 0) for (let i = 0; i < idx.length; i += 3) { const t = idx[i + 1]; idx[i + 1] = idx[i + 2]; idx[i + 2] = t; }
  return sh;
}

// returns [{pos, idx, kind:'metal'|'stone', col?}]; quality 'fine' (export) or 'draft' (live dragging)
export function buildRing(kind, p, quality = 'fine') {
  const shells = [];
  if (kind !== 'solitaire') {
    shells.push({ ...band(p, false, quality).shell, kind: 'metal' });
  } else {
    const { shell, top } = band(p, true, quality);
    shells.push({ ...shell, kind: 'metal' });
    const R = p.stone / 2, gy = top + 0.72 * R, zg1 = gy + 0.1 * R;
    shells.push({ ...toUp(brilliant(R, gy)), kind: 'stone' });
    // basket under the stone + gallery rail
    shells.push({ ...toUp(revolve([[0, top - 0.3], [1.4, top - 0.3], [0.92 * R, gy - 0.35], [0, gy - 0.35]], 64)), kind: 'metal' });
    const rc = [0.92 * R, gy - 0.35], rr = 0.17, circ = [];
    for (let k = 0; k < 12; k++) circ.push([rc[0] + rr * Math.cos((k * TAU) / 12), rc[1] + rr * Math.sin((k * TAU) / 12)]);
    shells.push({ ...toUp(revolve(circ, 64)), kind: 'metal' });
    // curved claw prongs
    for (let k = 0; k < p.prongs; k++) {
      const path = [[0.85 * R, top - 0.2, 0.36], [1.04 * R, gy - 0.55 * R, 0.34], [1.06 * R, gy + 0.02 * R, 0.30],
                    [1.00 * R, zg1 + 0.06 * R, 0.27], [0.88 * R, zg1 + 0.19 * R, 0.20], [0.80 * R, zg1 + 0.21 * R, 0]];
      shells.push({ ...tube(path, (k * TAU) / p.prongs + TAU / 16), kind: 'metal' });
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
