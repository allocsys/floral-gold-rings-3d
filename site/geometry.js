// Parametric ring geometry (mm). No dependencies: runs in the browser and in Node.
export const DEFAULTS = {
  band1:     { ID: 19, w: 4.5, t: 1.5, n: 4,  fr: 1.35, va: 0.6, gd: 0.18 },
  band2:     { ID: 17, w: 4.0, t: 1.4, n: 4,  fr: 1.2,  va: 0.6, gd: 0.18 },
  solitaire: { ID: 17, w: 2.6, t: 1.3, n: 4, fr: 0.72, va: 0.6, gd: 0.13, stone: 5.2, prongs: 6 },
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
const GOLD = [0.80, 0.50, 0.07], DARK = [0.02, 0.011, 0.003]; // bright satin relief / antique-gold recess

// ---------- engraved pattern (unrolled band, x along circumference, z across) ----------
const sdSeg = (px, pz, ax, az, bx, bz) => {
  const vx = bx - ax, vz = bz - az, t = clip(((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz || 1));
  return Math.hypot(px - ax - t * vx, pz - az - t * vz);
};
// leaf: pointed, bent by `curv`, engraved midrib + outline. returns [mask, dark]
function leafMask(x, z, cx, cz, ang, len, wid, e, curv = 0) {
  const c = Math.cos(ang), s = Math.sin(ang), dx = x - cx, dz = z - cz;
  const lx = dx * c + dz * s, t = lx / len;
  if (t < -0.05 || t > 1.05) return [0, 0];
  const tt = clip(t), ly = -dx * s + dz * c - curv * len * tt * tt;
  const hw = wid * Math.pow(Math.max(0, Math.sin(Math.PI * Math.pow(tt, 0.8))), 0.9);
  const m = sm(hw - Math.abs(ly), e);
  const rib = t > 0.12 && t < 0.88 ? sm(0.028 - Math.abs(ly), e * 0.5) : 0;
  const edge = t > 0.04 && t < 0.97 ? sm(0.03 - Math.abs(hw - Math.abs(ly) - 0.06), e * 0.5) * (hw > 0.12 ? 1 : 0) : 0;
  return [m, Math.max(rib, edge) * m];
}
function flowerMask(x, z, cx, cz, fr, e) {
  const dx = x - cx, dz = z - cz, rho = Math.hypot(dx, dz);
  if (rho > fr * 1.1 + e) return [0, 0];
  const phi = Math.atan2(dz, dx);
  const pet = fr * (0.62 + 0.38 * Math.pow(0.5 + 0.5 * Math.cos(5 * phi), 0.5));
  const a = mod(phi + Math.PI / 5, TAU / 5) - Math.PI / 5;
  const m = sm(pet - rho, e);
  const c = Math.max(
    sm(0.03 * fr - rho * Math.abs(a), e * 0.5) * sm(0.86 * fr - rho, e) * sm(rho - 0.3 * fr, e),   // petal creases
    sm(0.05 * fr - Math.abs(rho - 0.2 * fr), e * 0.5));                                             // centre ring
  return [m, c];
}

// ---- scrollwork strokes: tapered ribbons (polyline + width), spirals ----
function catmull(P, sub = 7) {
  const out = [], n = P.length;
  for (let i = 0; i < n - 1; i++) for (let s = 0; s < sub; s++) {
    const t = s / sub, p0 = P[Math.max(0, i - 1)], p1 = P[i], p2 = P[i + 1], p3 = P[Math.min(n - 1, i + 2)];
    out.push([0, 1].map(k => 0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3)));
  }
  out.push(P[n - 1].slice());
  return out;
}
function spiral(cx, cz, r0, r1, turns, dir, phi0, N = 48) {
  const out = [];
  for (let i = 1; i <= N; i++) { const f = i / N, ph = phi0 + dir * f * turns * TAU, r = r0 + (r1 - r0) * f; out.push([cx + r * Math.cos(ph), cz + r * Math.sin(ph)]); }
  return out;
}
function mkStroke(P, w0, w1) {
  const cum = [0]; let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
  for (let i = 0; i < P.length; i++) {
    if (i) cum.push(cum[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    x0 = Math.min(x0, P[i][0]); x1 = Math.max(x1, P[i][0]); z0 = Math.min(z0, P[i][1]); z1 = Math.max(z1, P[i][1]);
  }
  const w = Math.max(w0, w1);
  return { P, cum, L: cum[P.length - 1] || 1, w0, w1, x0: x0 - w - 0.2, x1: x1 + w + 0.2, z0: z0 - w - 0.2, z1: z1 + w + 0.2 };
}
function strokeMask(x, z, S, e) {
  if (x < S.x0 || x > S.x1 || z < S.z0 || z > S.z1) return [0, 0];
  const P = S.P; let best = 1e9, bt = 0;
  for (let i = 0; i < P.length - 1; i++) {
    const ax = P[i][0], az = P[i][1], vx = P[i + 1][0] - ax, vz = P[i + 1][1] - az;
    const l2 = vx * vx + vz * vz || 1e-9, u = clip(((x - ax) * vx + (z - az) * vz) / l2);
    const d = Math.hypot(x - ax - u * vx, z - az - u * vz);
    if (d < best) { best = d; bt = (S.cum[i] + u * Math.sqrt(l2)) / S.L; }
  }
  let w = S.w0 + (S.w1 - S.w0) * bt, g = 0;
  if (S.leaf) { w = S.leaf * Math.min(1, bt / 0.12 + 0.25) * Math.pow(1 - bt, 0.8) + 0.04; }
  const m = sm(w - best, e);
  if (S.leaf && bt > 0.12 && bt < 0.7 && w > 0.2) g = sm(0.03 - best, e * 0.5) * m;
  return [m, g];
}

// Pattern after the high-detail reference: per repeat TWO solid 5-petal flowers (big F1, smaller F2) joined by broad tapered leaf-ribbons that
// cross in an S and curl into spirals (midrib groove), pointed leaves at the flowers, and raised beads in the dark recess.
// Half the motif (F1 -> F2) is drawn, then copied rotated 180 deg about F1, so the repeat is seamless. Motif coords: mm for hw=2, repeat 15.6.
export function makeQ(p, per, hw, e) {
  const kx = per / 15.6, s = hw / 2, U = (X, Z) => [X * kx, Z * s], strokes = [], leaves = [], flw = [], rings = [];
  const sc = 0.75 + 0.4 * p.va;
  const rib = (pts, wmax, curl, g) => {            // pts: motif coords of the body; curl: [centre motif, r0 motif, a0, dir]
    const body = pts.map(q => U(q[0], q[1])), r0 = curl[1] * s * sc, C = U(curl[0][0], curl[0][1]);
    const sp = spiral(C[0], C[1], r0, 0.28 * r0, 1.3, curl[3], curl[2]);
    const all = catmull(body).concat([[C[0] + r0 * Math.cos(curl[2]), C[1] + r0 * Math.sin(curl[2])]], sp).map(q => [g * q[0], g * q[1]]);
    const S = mkStroke(all, wmax * s, wmax * s); S.leaf = wmax * s; strokes.push(S);
  };
  const R2 = (q) => [per / 2 / kx - q[0], -q[1]];     // rotate 180 deg about the half-way point between F1 and F2
  for (const g of [1, -1]) {
    const a0 = -53 * Math.PI / 180, b = [[1.2, -0.45], [2.2, -0.85], [3.3, -0.95], [3.9, -0.8], [4.46, -0.5]];
    rib(b, 0.5, [[4.09, 0.1], 0.72, a0, 1], g);                                           // ribbon from F1: low S-sweep rising into a curl
    // pointed leaves above it and beside F2: X, Z, angle, length, half-width, curvature
    for (const [X, Z, ang, len, w, cv] of [[0.9, 0.85, 0.5, 1.6, 0.38, -0.15], [6.8, -0.75, -0.7, 1.2, 0.34, 0.15]]) {
      const t = [g * X * kx, g * Z * s]; leaves.push([t[0], t[1], ang + (g < 0 ? Math.PI : 0), 1.1 * len * s, 1.3 * w * s, cv]);
    }
    for (const [X, Z, r] of [[5.4, 0.35, 0.12], [5.7, -0.5, 0.1], [4.9, -1.2, 0.12], [3.6, 1.4, 0.1], [2.0, -0.2, 0.1], [5.3, 1.2, 0.09], [3.0, 0.2, 0.09]])
      rings.push([g * X * kx, g * Z * s, r * s, 1]);
  }
  flw.push([per / 2, 0, 0.82 * p.fr]);                                                       // F2 (periodic copy at -per/2 comes from the neighbour repeat)
  return { per, hw, fr: p.fr * 1.05, e, strokes, leaves, flw, rings, kx };
}
// returns 1 = raised gold, 0 = recessed antique gold
export function relief(x, z, q) {
  const { hw, e, per, kx } = q;
  let m = 0, c = 0;
  for (const off of [0, per, -per]) {
    const X = x - off;
    if (X < -9 * kx || X > 9 * kx) continue;
    let vm = 0;
    let vg = 0;
    for (const S of q.strokes) { const r = strokeMask(X, z, S, e); vm = Math.max(vm, r[0]); vg = Math.max(vg, r[1]); }
    if (off === 0) { // flower sits on top of the vine with a thin dark halo around it
      const f0 = flowerMask(X, z, 0, 0, q.fr, e), hal = flowerMask(X, z, 0, 0, q.fr * 1.12 + 0.1, e)[0];
      m = Math.max(m, f0[0], vm * (1 - hal)); c = Math.max(f0[1], vg * (1 - hal));
    } else { m = Math.max(m, vm); c = Math.max(c, vg); }
    for (const F of q.flw) { const f = flowerMask(X, z, F[0], F[1], F[2], e); m = Math.max(m, f[0]); c = Math.max(c, f[1]); }
    for (const L of q.leaves) { const l = leafMask(X, z, L[0], L[1], L[2], L[3], L[4], e, L[5]); m = Math.max(m, l[0]); c = Math.max(c, l[1]); }
    for (const R of q.rings) { const d = Math.hypot(X - R[0], z - R[1]); m = Math.max(m, sm(R[2] - d, e)); if (!R[3]) c = Math.max(c, sm(0.45 * R[2] - d, e)); }
  }
  m *= sm(hw - 0.42 - Math.abs(z), e);                                   // keep clear of the polished rim
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
      const R = Ro + DOME * (1 - zn * zn) - p.gd * (1 - r) + (1 - r) * 0.006 * (g - 0.5);
      put(R, z, DARK[0] * (0.9 + 0.2 * g) * (1 - r) + GOLD[0] * r, DARK[1] * (0.9 + 0.2 * g) * (1 - r) + GOLD[1] * r, DARK[2] * (0.9 + 0.2 * g) * (1 - r) + GOLD[2] * r);
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
