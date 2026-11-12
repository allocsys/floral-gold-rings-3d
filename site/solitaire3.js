// Solitaire 3: fully parametric (no GLB), mm. Ring axis = z, stone at +y, head symmetric about the plane x = 0.
// Parts: shank (flower / leaf / vine relief on both shoulders), gallery cup, 4 ball-tip prongs on the diagonals, faceted round brilliant (kind 'gem').
// Only the inner diameter ID is adjustable; the head and the ornament keep their size in mm.
const TAU = Math.PI * 2;
const sstep = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

// ---------- shank profile (s = arc length from the head along the outer face, mm) ----------
const hwAt = s => 1.0 + 1.2 * Math.exp(-Math.pow(s / 7, 1.6)) + 0.2 * Math.exp(-(((s - 8) / 5) ** 2)); // + a little extra width under the ornament   // half width: 2.2 at the head -> 1.0 at the back
const tAt = s => 1.65 + 0.30 * Math.exp(-Math.pow(s / 5, 1.5));  // wall thickness: 1.95 at the head -> 1.65
const RF = 0.32, DOME = 0.16; // edge fillet radius, outer face dome

// ---------- ornament: raised relief h(s, z) in mm on each shoulder ----------
const S0 = 2.7, LAM = 3.1, NCELL = 3, AMP = 0.36; // first flower at S0 + LAM/2, pitch LAM, stem wave amplitude AMP
const H_STEM = 0.20, H_LEAF = 0.27, H_PET = 0.33, H_BEAD = 0.42; // bold relief
function buildOrnament() {
  const P = []; // primitives with a bounding box [s0, s1, z0, z1]
  const usable = s => hwAt(s) - RF - 0.08;
  const stemZ = s => AMP * Math.sin(TAU * (s - (S0 + LAM / 2)) / LAM);
  const sEnd = S0 + LAM / 2 + (NCELL - 1) * LAM + LAM / 2;
  P.push({ t: 'stem', a: 2.0, b: sEnd, w: 0.17, bb: [2.0 - 0.2, sEnd + 0.2, -AMP - 0.2, AMP + 0.2] });
  for (let i = 0; i < NCELL; i++) {
    const sc = S0 + LAM / 2 + i * LAM;
    const R = Math.min(0.76, usable(sc));
    P.push({ t: 'flower', s: sc, R, bb: [sc - R, sc + R, -R, R] });
    for (const sg of [-1, 1]) { // leaf at each stem peak, pointing away from the head
      const pk = sc + sg * LAM / 4; // stem peak
      const zp = stemZ(pk), side = Math.sign(zp) || 1;
      const ang = 50 * Math.PI / 180, ds = Math.cos(ang), dz = side * Math.sin(ang);
      const L = Math.min(1.05, Math.max(0.4, (usable(pk) - Math.abs(zp)) / Math.sin(ang)));
      const tip = [pk + ds * L, zp + dz * L];
      P.push({ t: 'leaf', s: pk, z: zp, ds, dz, L, W: 0.33, bb: [Math.min(pk, tip[0]) - 0.3, Math.max(pk, tip[0]) + 0.3, Math.min(zp, tip[1]) - 0.3, Math.max(zp, tip[1]) + 0.3] });
    }
    // tendril (spiral) at each boundary between flowers, alternating sides; the last one ends the vine
    const b = sc + LAM / 2, sig = i % 2 === 0 ? 1 : -1;
    const r0 = Math.min(0.62, (usable(b) - 0.1) / 2);
    const turns = 1.1, rEnd = 0.3 * r0, th = turns * TAU, pts = [];
    for (let k = 0; k <= 64; k++) {
      const q = k / 64, r = r0 - (r0 - rEnd) * q, a = -sig * Math.PI / 2 + sig * q * th;
      pts.push([b + r * Math.cos(a), sig * r0 + r * Math.sin(a)]);
    }
    const cs = b, cz = sig * r0;
    P.push({ t: 'spiral', pts, w: 0.105, bead: pts[64], bb: [cs - r0 - 0.2, cs + r0 + 0.2, cz - r0 - 0.2, cz + r0 + 0.2] });
  }
  const PET = 5, petals = [];
  const height = (s, z) => {
    let h = 0;
    for (const p of P) {
      if (s < p.bb[0] || s > p.bb[1] || z < p.bb[2] || z > p.bb[3]) continue;
      let v = 0;
      if (p.t === 'stem') {
        if (s < p.a || s > p.b) continue;
        const slope = AMP * TAU / LAM * Math.cos(TAU * (s - (S0 + LAM / 2)) / LAM);
        const d = Math.abs(z - stemZ(s)) / Math.sqrt(1 + slope * slope), q = d / p.w;
        if (q < 1) v = H_STEM * (1 - q * q) * sstep(p.a, p.a + 0.5, s); // tapers in at the head end (no hard step)
      } else if (p.t === 'flower') {
        const ds = s - p.s, dz = z, rr = Math.hypot(ds, dz), R = p.R;
        if (rr < 0.17 * R / 0.6) { const q = rr / (0.17 * R / 0.6); v = Math.max(v, H_BEAD * (1 - q * q)); }
        for (let k = 0; k < PET; k++) {
          const pa = k * TAU / PET + Math.PI / 2 * 0, ca = Math.cos(pa), sa = Math.sin(pa);
          const u = ds * ca + dz * sa - 0.36 * R / 0.6, w = -ds * sa + dz * ca;
          const q2 = (u / (0.27 * R / 0.6)) ** 2 + (w / (0.20 * R / 0.6)) ** 2;
          if (q2 < 1) v = Math.max(v, H_PET * (1 - q2));
        }
      } else if (p.t === 'leaf') {
        const rs = s - p.s, rz = z - p.z, u = (rs * p.ds + rz * p.dz) / p.L, w = (-rs * p.dz + rz * p.ds);
        if (u > 0 && u < 1) {
          const wid = p.W * Math.pow(Math.sin(Math.PI * u), 0.85) * (p.L / 0.85 > 0.6 ? 1 : 0.8), q = Math.abs(w) / Math.max(wid, 1e-4);
          if (q < 1) v = H_LEAF * (1 - q * q) * (1 - 0.3 * Math.exp(-((w / 0.07) ** 2)));
        }
      } else if (p.t === 'spiral') {
        let d2 = 1e9;
        for (let k = 0; k < 64; k++) {
          const ax = p.pts[k][0], az = p.pts[k][1], bx = p.pts[k + 1][0], bz = p.pts[k + 1][1], ex = bx - ax, ez = bz - az;
          const t = Math.min(1, Math.max(0, ((s - ax) * ex + (z - az) * ez) / (ex * ex + ez * ez))), dx = s - ax - t * ex, dzz = z - az - t * ez;
          d2 = Math.min(d2, dx * dx + dzz * dzz);
        }
        const q = Math.sqrt(d2) / p.w; if (q < 1) v = H_STEM * (1 - q * q);
        const bq = Math.hypot(s - p.bead[0], z - p.bead[1]) / 0.15; if (bq < 1) v = Math.max(v, 0.32 * (1 - bq * bq));
      }
      if (v > h) h = v;
    }
    return h;
  };
  return { height, sEnd };
}

// ---------- shank: closed (ring x section) grid ----------
function shank(Ri, quality) {
  const fine = quality !== 'draft', stepO = fine ? 0.035 : 0.09, stepC = fine ? 0.14 : 0.25;
  const Mo = fine ? 84 : 30, Kf = fine ? 8 : 4, Wn = 4, Mi = fine ? 14 : 8;
  const Rref = Ri + 1.9, orn = buildOrnament();
  // section angles psi in [-pi, pi): fine steps over the ornament zone, coarse elsewhere
  const psis = []; let psi = -Math.PI;
  while (psi < Math.PI - 1e-6) {
    psis.push(psi); const s = Math.abs(psi) * Rref;
    const st = s > 1.9 && s < orn.sEnd + 0.4 ? stepO : (s < 4 ? 0.08 : stepC);
    psi += st / Rref;
  }
  const N = psis.length, M = Mo + 2 * Kf + 2 * Wn + Mi;
  const P = new Float32Array(N * M * 3);
  for (let i = 0; i < N; i++) {
    const psi = psis[i], s = Math.abs(psi) * Rref, hw = hwAt(s), Ro = Ri + tAt(s), sn = Math.sin(psi), cs = Math.cos(psi);
    let o = i * M * 3;
    const put = (R, z) => { P[o] = R * sn; P[o + 1] = R * cs; P[o + 2] = z; o += 3; };
    const zt = (hw - RF) / hw, Rt = Ro + DOME * (1 - zt * zt), Rie = Ri - 0.06 * (1 - zt * zt);
    const inOrn = s > 1.9 && s < orn.sEnd + 0.4;
    for (let j = 0; j < Mo; j++) {
      const zn = (-1 + (2 * j) / (Mo - 1)) * zt, z = zn * hw;
      let R = Ro + DOME * (1 - zn * zn);
      if (inOrn) { const fe = sstep(0, 0.14, hw - RF - Math.abs(z)); if (fe > 0) R += fe * orn.height(s, z); }
      put(R, z);
    }
    const edge = [];
    for (let k = 1; k <= Kf; k++) { const a = (k / Kf) * Math.PI / 2; edge.push([hw - RF + RF * Math.sin(a), Rt - RF * (1 - Math.cos(a))]); }
    for (let j = 1; j <= Wn; j++) edge.push([hw, (Rt - RF) + (Rie + RF - (Rt - RF)) * (j / (Wn + 1))]);
    for (let k = 0; k < Kf; k++) { const a = (k / Kf) * Math.PI / 2; edge.push([hw - RF + RF * Math.cos(a), Rie + RF - RF * Math.sin(a)]); }
    for (const [z, R] of edge) put(R, z);
    for (let j = 0; j < Mi; j++) { const zn = zt * (1 - (2 * j) / (Mi - 1)); put(Ri - 0.06 * (1 - zn * zn), zn * hw); }
    for (let k = Kf + Wn + Kf - 1; k >= 0; k--) put(edge[k][1], -edge[k][0]);
  }
  const idx = new Uint32Array(N * M * 6); let k = 0;
  for (let i = 0; i < N; i++) for (let j = 0; j < M; j++) {
    const a = i * M + j, b = ((i + 1) % N) * M + j, c = ((i + 1) % N) * M + (j + 1) % M, d = i * M + (j + 1) % M;
    idx[k++] = a; idx[k++] = b; idx[k++] = c; idx[k++] = a; idx[k++] = c; idx[k++] = d;
  }
  return { pos: P, idx };
}

// ---------- small mesh helpers ----------
class Mesh {
  constructor() { this.p = []; this.i = []; }
  v(x, y, z) { this.p.push(x, y, z); return this.p.length / 3 - 1; }
  tri(a, b, c) { this.i.push(a, b, c); }
  finish() { return { pos: new Float32Array(this.p), idx: new Uint32Array(this.i) }; }
}
function lathe(prof, seg) { // prof = [[rho, y], ...] from the axis (rho 0) round to the axis; surface of revolution about the y axis
  const m = new Mesh(), n = prof.length;
  for (let j = 0; j < seg; j++) for (let k = 0; k < n; k++) { const a = (j / seg) * TAU; m.v(prof[k][0] * Math.cos(a), prof[k][1], prof[k][0] * Math.sin(a)); }
  for (let j = 0; j < seg; j++) for (let k = 0; k < n - 1; k++) {
    const a = j * n + k, b = ((j + 1) % seg) * n + k, c = ((j + 1) % seg) * n + k + 1, d = j * n + k + 1;
    m.tri(a, b, c); m.tri(a, c, d);
  }
  return m;
}
function catmull(pts, per) { // pts of [rho, y, r]; open Catmull-Rom, per samples per span
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let k = 0; k < per; k++) {
      const t = k / per, t2 = t * t, t3 = t2 * t, q = c => 0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2 + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3);
      out.push([q(0), q(1), q(2)]);
    }
  }
  out.push(pts[pts.length - 1].slice()); return out;
}
function prong(alpha, path, ballR, ring) { // tube along a path in the vertical plane at azimuth alpha (x-z plane) + ball tip; path = [[rho, y, r]]
  const m = new Mesh(), d = [Math.cos(alpha), Math.sin(alpha)], bz = [-Math.sin(alpha), Math.cos(alpha)], n = path.length;
  for (let k = 0; k < n; k++) {
    const a = path[Math.max(0, k - 1)], b = path[Math.min(n - 1, k + 1)];
    let tr = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tr, ty); tr /= tl; ty /= tl;
    const nr = -ty, ny = tr; // in-plane normal
    for (let j = 0; j < ring; j++) {
      const th = (j / ring) * TAU, c = Math.cos(th), s = Math.sin(th), r = path[k][2];
      const rho = path[k][0] + r * c * nr, y = path[k][1] + r * c * ny, w = r * s;
      m.v(rho * d[0] + w * bz[0], y, rho * d[1] + w * bz[1]);
    }
  }
  for (let k = 0; k < n - 1; k++) for (let j = 0; j < ring; j++) {
    const a = k * ring + j, b = k * ring + (j + 1) % ring, c = (k + 1) * ring + (j + 1) % ring, e = (k + 1) * ring + j;
    m.tri(a, b, c); m.tri(a, c, e);
  }
  const cap = (k, flip) => { const cx = m.v(...[0, 1, 2].map(c => { let s = 0; for (let j = 0; j < ring; j++) s += m.p[(k * ring + j) * 3 + c]; return s / ring; })); for (let j = 0; j < ring; j++) { const a = k * ring + j, b = k * ring + (j + 1) % ring; flip ? m.tri(cx, b, a) : m.tri(cx, a, b); } };
  cap(0, false); cap(n - 1, true);
  const e = path[n - 1], cx = e[0] * d[0], cy = e[1], cz = e[0] * d[1], SL = 14, ST = 10, base = m.p.length / 3; // ball tip
  for (let st = 0; st <= ST; st++) for (let sl = 0; sl < SL; sl++) { const ph = (st / ST) * Math.PI, th = (sl / SL) * TAU; m.v(cx + ballR * Math.sin(ph) * Math.cos(th), cy + ballR * Math.cos(ph), cz + ballR * Math.sin(ph) * Math.sin(th)); }
  for (let st = 0; st < ST; st++) for (let sl = 0; sl < SL; sl++) { const a = base + st * SL + sl, b = base + st * SL + (sl + 1) % SL, c = base + (st + 1) * SL + (sl + 1) % SL, e2 = base + (st + 1) * SL + sl; m.tri(a, b, c); m.tri(a, c, e2); }
  return m;
}

// ---------- round brilliant (flat facets: every triangle has its own vertices) ----------
function gem(yg) {
  const m = new Mesh(), Rg = 2.1, Rt = 1.2, yGt = yg + 0.05, yGb = yg - 0.05, yT = yGt + 0.58, yC = yGb - 1.82, yM = yGb - 0.9, Rm = 1.12;
  const ring = (n, R, y, off) => Array.from({ length: n }, (_, k) => { const a = ((k + off) / n) * TAU; return [R * Math.cos(a), y, R * Math.sin(a)]; });
  const Gt = ring(16, Rg, yGt, 0), Gb = ring(16, Rg, yGb, 0), T = ring(8, Rt, yT, 0.5), Mm = ring(8, Rm, yM, 0), C = [0, yC, 0], top = [0, yT, 0];
  const tris = [];
  for (let j = 0; j < 8; j++) {
    tris.push([top, T[j], T[(j + 1) % 8]]); // table
    tris.push([T[j], Gt[(2 * j + 1) % 16], Gt[(2 * j + 2) % 16]], [T[j], Gt[(2 * j + 2) % 16], T[(j + 1) % 8]], [T[(j + 1) % 8], Gt[(2 * j + 2) % 16], Gt[(2 * j + 3) % 16]]); // crown
    tris.push([Mm[j], Gb[(2 * j + 1) % 16], Gb[(2 * j) % 16]], [Mm[j], Gb[(2 * j + 2) % 16], Gb[(2 * j + 1) % 16]]); // lower girdle facets
    tris.push([Mm[j], Gb[(2 * j + 2) % 16], Mm[(j + 1) % 8]]); // between mains
    tris.push([Mm[j], Mm[(j + 1) % 8], C]); // pavilion mains
  }
  for (let k = 0; k < 16; k++) { const a = Gt[k], b = Gt[(k + 1) % 16], c = Gb[(k + 1) % 16], d = Gb[k]; tris.push([a, d, c], [a, c, b]); } // girdle band
  for (const t of tris) { // orient outward from the stone axis
    const [a, b, c] = t, ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, cx = (a[0] + b[0] + c[0]) / 3, cy = (a[1] + b[1] + c[1]) / 3 - (yT + yC) / 2, cz = (a[2] + b[2] + c[2]) / 3;
    const tt = nx * cx + ny * cy + nz * cz >= 0 ? t : [a, c, b];
    m.tri(m.v(...tt[0]), m.v(...tt[1]), m.v(...tt[2]));
  }
  return m;
}

// returns shells [{pos, idx, kind}]
export function buildSolitaire3(p, quality = 'fine') {
  const Ri = p.ID / 2, yg = Ri + 2.75, sh = [];
  sh.push({ ...shank(Ri, quality), kind: 'metal' });
  // gallery cup under the stone: rises out of the shank top, flares to a rim just under the girdle
  const gp = [[0, Ri + 1.5], [2.6, Ri + 1.5], [2.35, Ri + 1.95], [1.98, Ri + 2.3], [1.9, Ri + 2.5], [2.12, yg - 0.2], [2.14, yg - 0.1], [1.9, yg - 0.07], [0, yg - 0.07]];
  const gl = lathe(gp, quality === 'draft' ? 24 : 64); sh.push({ ...gl.finish(), kind: 'metal' });
  // 4 ball-tip prongs on the diagonals: up the gallery, round the girdle edge, over the crown edge
  const cr = y => 2.1 - (y - (yg + 0.05)) * (0.9 / 0.58); // crown surface radius at height y
  const path = catmull([[2.05, Ri + 1.8, 0.34], [2.26, Ri + 2.35, 0.27], [2.33, yg - 0.02, 0.22], [cr(yg + 0.28) + 0.19, yg + 0.28, 0.2], [cr(yg + 0.58) + 0.17, yg + 0.58, 0.18], [1.38, yg + 0.78, 0.17]], 12);
  for (let k = 0; k < 4; k++) sh.push({ ...prong(Math.PI / 4 + k * Math.PI / 2, path, 0.29, quality === 'draft' ? 10 : 16).finish(), kind: 'metal' });
  sh.push({ ...gem(yg).finish(), kind: 'gem' });
  return sh;
}
