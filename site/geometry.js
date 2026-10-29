// Parametric ring geometry (mm). No dependencies: runs in the browser and in Node.
export const DEFAULTS = {
  band1:     { ID: 19, w: 4.5, t: 1.5, n: 8,  fr: 1.35, va: 0.6, gd: 0.18 },
  band2:     { ID: 17, w: 4.0, t: 1.4, n: 7,  fr: 1.2,  va: 0.6, gd: 0.18 },
  solitaire: { ID: 17, w: 2.6, t: 1.3, n: 11, fr: 0.72, va: 0.6, gd: 0.13, stone: 5.2, prongs: 6 },
};
export const LABELS = { band1: 'Wide band', band2: 'Band', solitaire: 'Solitaire' };
export const CONTROLS = [
  ['ID', 'Inner diameter', 14, 24, 0.1],
  ['w', 'Width', 1.5, 8, 0.1],
  ['t', 'Thickness', 0.8, 3, 0.05],
  ['n', 'Flowers around', 3, 20, 1],
  ['fr', 'Flower size', 0.3, 1.8, 0.05],
  ['va', 'Vine wave', 0, 1.0, 0.05],
  ['gd', 'Engraving depth', 0, 0.35, 0.01],
  ['stone', 'Stone diameter', 3, 8, 0.1, 'solitaire'],
  ['prongs', 'Prongs', 4, 8, 1, 'solitaire'],
];

const TAU = Math.PI * 2;
const mod = (a, b) => ((a % b) + b) % b;
const clip = (x) => Math.min(1, Math.max(0, x));
const sm = (d, e) => { const t = clip(0.5 + d / (2 * e)); return t * t * (3 - 2 * t); }; // soft edge, d>0 inside

// linear colours: polished gold relief, near-black oxidised recess
const GOLD = [0.80, 0.50, 0.07], DARK = [0.17, 0.095, 0.022]; // bright satin relief / antique-gold recess

// ---------- engraved pattern (unrolled band, x along circumference, z across) ----------
const sdSeg = (px, pz, ax, az, bx, bz) => {
  const vx = bx - ax, vz = bz - az, t = clip(((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz || 1));
  return Math.hypot(px - ax - t * vx, pz - az - t * vz);
};
function leafMask(x, z, cx, cz, ang, len, wid, e) {
  const c = Math.cos(ang), s = Math.sin(ang), dx = x - cx, dz = z - cz;
  const lx = dx * c + dz * s, ly = -dx * s + dz * c, t = lx / len;
  if (t < -0.05 || t > 1.05) return [0, 0];
  const tt = clip(t);
  const hw = wid * Math.pow(Math.max(0, Math.sin(Math.PI * Math.pow(tt, 0.8))), 0.9);
  const rib = t > 0.14 && t < 0.86 ? sm(0.03 - Math.abs(ly), e * 0.5) : 0;
  return [sm(hw - Math.abs(ly), e), rib];
}
function flowerMask(x, z, cx, cz, fr, e) {
  const dx = x - cx, dz = z - cz, rho = Math.hypot(dx, dz);
  if (rho > fr * 1.1 + e) return [0, 0];
  const phi = Math.atan2(dz, dx);
  const pet = fr * (0.42 + 0.58 * Math.pow(0.5 + 0.5 * Math.cos(5 * phi), 0.6));
  const a = mod(phi + Math.PI / 5, TAU / 5) - Math.PI / 5;
  const c = Math.max(
    sm(0.045 * fr - rho * Math.abs(a), e * 0.5) * sm(0.86 * fr - rho, e) * sm(rho - 0.3 * fr, e),
    sm(0.05 * fr - Math.abs(rho - 0.2 * fr), e * 0.5));
  return [sm(pet - rho, e), c];
}
function curlMask(x, z, C, e) {
  // arched stem (quadratic bezier, tangent into the spiral) back to the flower
  let m = 0, d = 1e9, px = C.Ex, pz = C.Ez;
  for (let i = 1; i <= 10; i++) {
    const t = i / 10, u = 1 - t, qx = u * u * C.Ex + 2 * u * t * C.Mx + t * t * C.Fx, qz = u * u * C.Ez + 2 * u * t * C.Mz + t * t * C.Fz;
    d = Math.min(d, sdSeg(x, z, px, pz, qx, qz)); px = qx; pz = qz;
  }
  m = sm(C.sw - d, e);
  const dx = x - C.cx, dz = z - C.cz, rho = Math.hypot(dx, dz);
  if (rho < C.rout + C.tw * 2 + e) {
    const psi = mod(C.sgn * (Math.atan2(dz, dx) - C.th0), TAU);
    for (let th = psi; th <= C.TH; th += TAU) {
      const f = th / C.TH;
      m = Math.max(m, sm(C.tw * (1.15 - 0.7 * f) - Math.abs(rho - (C.rin + (C.rout - C.rin) * f)), e));
    }
    m = Math.max(m, sm(C.tw * 1.6 - Math.hypot(x - C.bx, z - C.bz), e)); // bulb at the inner end
  }
  return m;
}
// per-tile geometry; rebuilt per column because the solitaire's half-width tapers
export function makeQ(p, per, hw, e) {
  return { per, hw, fr: p.fr, a: (0.12 + 0.42 * p.va) * hw, ws: 0.05 * hw + 0.06, e };
}
// returns 1 = raised satin gold, 0 = recessed antique gold.
// One tile = a sine vine through a big flower (centre) and small flowers (tile joints), paired leaves at each crest, berry clusters opposite.
export function relief(x, z, q) {
  const { per, hw, fr, a, ws, e } = q;
  const k = TAU / per, sl = a * k * Math.cos(k * x);
  let m = sm(ws - Math.abs(z - a * Math.sin(k * x)) / Math.sqrt(1 + sl * sl), e), c = 0;
  const fl = flowerMask(x, z, 0, 0, fr, e); m = Math.max(m, fl[0]); c = fl[1];
  const L = 0.2 * per, wd = 0.17 * L, rb = 0.07 * hw + 0.07;
  for (const s of [-1, 1]) {
    const f2 = flowerMask(x, z, s * per / 2, 0, 0.42 * fr, e);          // small flower on the tile joint
    m = Math.max(m, f2[0]); c = Math.max(c, f2[1]);
    const xc = s * per / 4, zc = s * a;                                  // vine crest
    for (const [ang, len] of [[s * 0.45, L], [s * (Math.PI - 0.45), 0.85 * L]]) {
      const l = leafMask(x, z, xc, zc, ang, len, wd, e);
      m = Math.max(m, l[0]); c = Math.max(c, l[1]);
    }
    for (const [dx, dz, r] of [[0, -0.62 * hw, rb], [0.12 * per, -0.48 * hw, 0.75 * rb], [-0.12 * per, -0.48 * hw, 0.75 * rb]])
      m = Math.max(m, sm(r - Math.hypot(x - xc - dx, z - s * dz), e));    // berries
  }
  const az = Math.abs(z);                                                // pin-stripe next to the polished rim
  c = Math.max(c, sm(0.03 - Math.abs(az - (hw - 0.42)), e * 0.5));
  return clip(m - c);
}

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
function band(p, solitaire, quality) {
  const step = quality === 'draft' ? 0.12 : 0.055;
  const Ri = p.ID / 2, Ro = Ri + p.t, per = TAU * Ro / p.n;
  const NT = Math.max(240, Math.ceil(TAU * Ro / step));
  const rf = 0.32, Kf = quality === 'draft' ? 4 : 8, Wn = 5, Mi = 10;
  const Mo = Math.max(24, Math.ceil(((solitaire ? p.w * 1.3 : p.w) - 2 * rf) / step));
  const S = 2 * Kf + Wn, Mt = Mo + Mi + 2 * S;
  const P = new Float32Array(NT * Mt * 3), C = new Float32Array(NT * Mt * 3);
  const e = Math.max(1.5 * step, 0.07);
  for (let i = 0; i < NT; i++) {
    const th = (i / NT) * TAU;
    const d = Math.abs(mod(th - Math.PI / 2 + Math.PI, TAU) - Math.PI); // angle from top
    const shoulder = solitaire ? clip((d - 0.38) / 0.25) * clip((2.2 - d) / 0.25) : 1;
    const hwid = solitaire ? (p.w / 2) * (1 + 0.28 * (1 + Math.cos(d)) / 2) : p.w / 2;
    const ds = mod((th - Math.PI / 2) * Ro + per / 2, per) - per / 2;
    const q = makeQ(p, per, hwid, e);
    const ct = Math.cos(th), st = Math.sin(th);
    let o = i * Mt * 3;
    const put = (R, z, c0, c1, c2) => { P[o] = R * ct; P[o + 1] = R * st; P[o + 2] = z; C[o] = c0; C[o + 1] = c1; C[o + 2] = c2; o += 3; };
    const zt = (hwid - rf) / hwid, Rt = Ro + DOME * (1 - zt * zt), Rie = Ri - 0.08 * (1 - zt * zt);
    // outer face with engraving
    for (let j = 0; j < Mo; j++) {
      const zn = (-1 + (2 * j) / (Mo - 1)) * zt, z = zn * hwid;
      const r = 1 + (relief(ds, z, q) - 1) * shoulder;
      const nz = Math.sin(ds * 91.7 + z * 57.3 + i * 0.37) * 43758.5453, g = nz - Math.floor(nz); // fine grain in the recess
      const R = Ro + DOME * (1 - zn * zn) - p.gd * (1 - r) + (1 - r) * 0.014 * (g - 0.5);
      put(R, z, DARK[0] * (0.8 + 0.4 * g) * (1 - r) + GOLD[0] * r, DARK[1] * (0.8 + 0.4 * g) * (1 - r) + GOLD[1] * r, DARK[2] * (0.8 + 0.4 * g) * (1 - r) + GOLD[2] * r);
    }
    // rounded edge: outer fillet, wall, inner fillet (+z side), inner bore, then the -z side back
    const edge = [];
    for (let k = 1; k <= Kf; k++) { const a = (k / Kf) * Math.PI / 2; edge.push([hwid - rf + rf * Math.sin(a), Rt - rf * (1 - Math.cos(a))]); }
    for (let j = 1; j <= Wn; j++) edge.push([hwid, (Rt - rf) + (Rie + rf - (Rt - rf)) * (j / (Wn + 1))]);
    for (let k = 0; k < Kf; k++) { const a = (k / Kf) * Math.PI / 2; edge.push([hwid - rf + rf * Math.cos(a), Rie + rf - rf * Math.sin(a)]); }
    for (const [z, R] of edge) put(R, z, GOLD[0], GOLD[1], GOLD[2]);
    for (let j = 0; j < Mi; j++) {
      const zn = zt * (1 - (2 * j) / (Mi - 1)), R = Ri - 0.08 * (1 - zn * zn);
      put(R, zn * hwid, GOLD[0], GOLD[1], GOLD[2]);
    }
    for (let k = S - 1; k >= 0; k--) put(edge[k][1], -edge[k][0], GOLD[0], GOLD[1], GOLD[2]);
  }
  return { shell: { ...torus(P, NT, Mt), col: C }, top: Ro + DOME };
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
