// Parametric ring geometry (mm). No dependencies: runs in the browser and in Node.
// Both bands (band1, band2) carry the engraved floral relief (relief_band.js, derived from reference/rings_flat.png), repeated REPEATS times around the ring.
import { RELIEF_BAND } from './relief_band.js?v=relief151';
// RIM margin (band tabs only): WD mm added to the band width; the map keeps its mm size and the extra WD/2 per side is plain ground. URL ?wd=0.3 / ?wd=0.5 to test; no param or 0 = off (prior look).
const WD = (() => { try { const v = parseFloat(new URLSearchParams(location.search).get('wd')); return v > 0 && v <= 1.5 ? Math.round(v * 10) / 10 : 0; } catch (e) { return 0; } })();
export const DEFAULTS = {
  band1:     { ID: 19, w: +(4.5 + WD).toFixed(1), t: 1.5, relief: 0.4 },
  band2:     { ID: 17, w: +(4.0 + WD).toFixed(1), t: 1.4, relief: 0.4 },
  solitaire: { ID: 17 }, // Meshy GLB (site/solitaire_meshy2.glb = reference/meshy/solitaire_5.glb, loaded by index.html): only the inner diameter is adjustable; no parametric geometry
  solitaire2: { ID: 17 }, // Solitaire 2 = Solitaire with the head (stone + prongs) lowered (index.html SOLS.solitaire2.lower)
};
export const LABELS = { band1: 'Wide band', band2: 'Band', solitaire: 'Solitaire', solitaire2: 'Solitaire 2' };
export const CONTROLS = [
  ['ID', 'Inner diameter', 14, 24, 0.1, ['band1', 'band2', 'solitaire', 'solitaire2']],
  ['w', 'Width', 1.5, 8, 0.1],
  ['t', 'Thickness', 0.8, 3, 0.05],
  ['relief', 'Relief depth', 0, 0.8, 0.05, ['band1', 'band2']],
];

const TAU = Math.PI * 2;
const mod = (a, b) => ((a % b) + b) % b;

// ---------- mesh helpers ----------
function torus(P, N, M) {
  const idx = new Uint32Array(N * M * 6); let k = 0;
  for (let i = 0; i < N; i++) for (let j = 0; j < M; j++) {
    const a = i * M + j, b = ((i + 1) % N) * M + j, c = ((i + 1) % N) * M + (j + 1) % M, d = i * M + (j + 1) % M;
    // D31: split each quad along its SHORTER 3D diagonal (= the one following the iso-line on a steep wall); a fixed a-c split gives a regular sawtooth on walls running along the b-d diagonal
    const ac = (P[a*3]-P[c*3])**2 + (P[a*3+1]-P[c*3+1])**2 + (P[a*3+2]-P[c*3+2])**2, bd = (P[b*3]-P[d*3])**2 + (P[b*3+1]-P[d*3+1])**2 + (P[b*3+2]-P[d*3+2])**2;
    if (ac <= bd) { idx[k++] = a; idx[k++] = b; idx[k++] = c; idx[k++] = a; idx[k++] = c; idx[k++] = d; }
    else { idx[k++] = a; idx[k++] = b; idx[k++] = d; idx[k++] = b; idx[k++] = c; idx[k++] = d; }
  }
  return { pos: P, idx, grid: [N, M] };
}
const DOME = 0.26;

// ---------- relief map sampling (mip pyramid, bilinear, periodic in u) ----------
const GROUND_COL = [0.02, 0.017, 0.013], GROUND_LO = 0.08, GROUND_HI = 0.55; // viewer tint of the recessed ground (x gold) and the relief-height range it fades over
let ULTRA_STEP = 0.02; // mesh step (mm) of the 'ultra' quality for relief bands (D52: 0.03 on touch devices, see setUltraStep)
export function setUltraStep(s) { ULTRA_STEP = s; }
let _nmTex = null;
export function reliefTex() { // D54 (b2): mip 0 of the band map as bytes (R8 texture for the shader normal map)
  if (!_nmTex) { const bin = atob(RELIEF_BAND.b64), d = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) d[i] = bin.charCodeAt(i); _nmTex = { W: RELIEF_BAND.W, H: RELIEF_BAND.H, data: d }; }
  return _nmTex;
}
const REPEATS = 4, FADE_B = 0.2; // FADE_B = fade length of the relief at the band edge // pattern repeats around the ring; relief fades to 0 over the last FADE mm before the rounded edge
const mipCache = new Map();
function reliefMips(R = RELIEF_BAND) {
  if (mipCache.has(R)) return mipCache.get(R);
  const bin = atob(R.b64), a = new Float32Array(bin.length);
  for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i) / 255;
  const mips = [{ W: R.W, H: R.H, a }];
  for (;;) {
    const m = mips[mips.length - 1], W = m.W >> 1, H = m.H >> 1;
    if (W < 8 || H < 4) break;
    const b = new Float32Array(W * H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++)
      b[y * W + x] = (m.a[2 * y * m.W + 2 * x] + m.a[2 * y * m.W + 2 * x + 1] + m.a[(2 * y + 1) * m.W + 2 * x] + m.a[(2 * y + 1) * m.W + 2 * x + 1]) / 4;
    mips.push({ W, H, a: b });
  }
  mipCache.set(R, mips); return mips;
}
function bsw(t) { // uniform cubic B-spline weights for taps -1..2 (C2: no slope kinks where one map px spans several mesh cells)
  const t2 = t * t, t3 = t2 * t, m = 1 - t;
  return [m * m * m / 6, (3 * t3 - 6 * t2 + 4) / 6, (-3 * t3 + 3 * t2 + 3 * t + 1) / 6, t3 / 6];
}
function sampleRelief(L, u, v) { // u periodic in [0,1), v in [0,1]; bicubic B-spline
  const x = u * L.W - 0.5, y = Math.min(Math.max(v * L.H - 0.5, 0), L.H - 1);
  const x0 = Math.floor(x), y0 = Math.floor(y), wx = bsw(x - x0), wy = bsw(y - y0);
  let acc = 0;
  for (let b = 0; b < 4; b++) {
    const r = Math.min(Math.max(y0 - 1 + b, 0), L.H - 1) * L.W; let rs = 0;
    for (let a = 0; a < 4; a++) { let xi = x0 - 1 + a; xi = mod(xi, L.W); rs += wx[a] * L.a[r + xi]; }
    acc += wy[b] * rs;
  }
  return acc;
}
function band(p, quality) {
  const rel = p.relief > 0 ? p.relief : 0, RS = RELIEF_BAND;
  const step = quality === 'draft' ? 0.12 : rel ? (quality === 'ultra' ? ULTRA_STEP : 0.04) : 0.055; // 'ultra' = relief walls need >= ~6 cells (D26: .04 step leaves them 3 cells -> sawtooth hatching)
  const Ri = p.ID / 2, Ro = Ri + p.t;
  const NT = Math.max(240, Math.ceil(TAU * Ro / step));
  const rf = 0.32, SV = !WD ? 1 : (p.w - 2 * rf) / Math.max(0.5, p.w - WD - 2 * rf), Kf = quality === 'draft' ? 4 : 8, Wn = 5, Mi = 10;
  const Mo = Math.max(24, Math.ceil((p.w - 2 * rf) / step));
  const S = 2 * Kf + Wn, Mt = Mo + Mi + 2 * S;
  let lv = null;
  if (rel) { // pick the mip level whose pixel size matches the mesh spacing (box prefilter, no aliasing)
    const ms = reliefMips(RS), pxU = (TAU * Ro / REPEATS) / RS.W, pxV = (p.w / SV) / RS.H;
    lv = ms[Math.min(ms.length - 1, Math.max(0, Math.floor(Math.log2(Math.max(TAU * Ro / NT / pxU, (2 * (p.w / 2 - rf)) / (Mo - 1) / pxV)))))];
  }
  const P = new Float32Array(NT * Mt * 3);
  const C = lv ? new Float32Array(NT * Mt * 3).fill(1) : null; // viewer-only vertex colour: dark bronze ground, full gold on the raised relief
  const UVF = lv ? new Float32Array(NT * Mt * 3) : null; // D53 (b1): per-vertex map u, v and edge fade of the outer face (0 elsewhere); unused until the shader normal map (b2)
  for (let i = 0; i < NT; i++) {
    const th = (i / NT) * TAU;
    const hwid = p.w / 2;
    const ct = Math.cos(th), st = Math.sin(th);
    let o = i * Mt * 3;
    const put = (R, z) => { P[o] = R * ct; P[o + 1] = R * st; P[o + 2] = z; o += 3; };
    const zt = (hwid - rf) / hwid, Rt = Ro + DOME * (1 - zt * zt), Rie = Ri - 0.08 * (1 - zt * zt);
    // outer face (domed)
    for (let j = 0; j < Mo; j++) {
      const zn = (-1 + (2 * j) / (Mo - 1)) * zt;
      let R = Ro + DOME * (1 - zn * zn);
      if (lv) { // engraved relief: peaks keep the nominal radius, recesses cut down by `rel` mm, fading out at the rounded edges
        const zf = Math.min(1, (hwid - rf - Math.abs(zn * hwid)) / FADE_B), fade = zf * zf * (3 - 2 * zf);
        const mu = mod((i / NT) * REPEATS, 1), mv = Math.min(1, Math.max(0, 0.5 + (zn / zt) * SV / 2));
        const hv = sampleRelief(lv, mu, mv); { const uo = (i * Mt + j) * 3; UVF[uo] = mu; UVF[uo + 1] = mv; UVF[uo + 2] = fade; }
        R -= rel * fade * (1 - hv);
        const s = Math.min(1, Math.max(0, (hv - GROUND_LO) / (GROUND_HI - GROUND_LO))), k = s * s * (3 - 2 * s), c = (i * Mt + j) * 3;
        const sg = 0.35 + 1.5 * Math.pow(h2(i, j), 2.2); // D77: stippled ground like the ref (per-vertex grain, viewer colour only)
        for (let q = 0; q < 3; q++) C[c + q] = GROUND_COL[q] * sg + (1 - GROUND_COL[q]) * (1 - fade + fade * k);
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
  const shell = torus(P, NT, Mt); if (C) shell.col = C; if (UVF) shell.uvf = UVF;
  if (UVF) shell.nm = { rel, su: TAU * Ro / REPEATS, sv: 2 * (p.w / 2 - rf) / SV, step }; // D54 (b2): mm per map-u unit, mm per map-v unit, mesh step (mm) for the shader normal map (band only)
  return { shell, top: Ro + DOME };
}
const h2 = (i, j) => { const n = Math.sin(i * 127.1 + j * 311.7) * 43758.5453; return n - Math.floor(n); }; // hash noise for the stippled ground of the old relief band
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

export const GLB_KINDS = ['solitaire', 'solitaire2']; // tabs whose model is a GLB loaded by the viewer
// returns [{pos, idx, kind:'metal', col?}]; quality 'fine' (export) or 'draft' (live dragging)
export function buildRing(kind, p, quality = 'fine') {
  if (GLB_KINDS.includes(kind)) throw new Error(`${kind} is a Meshy GLB model (see index.html), it has no parametric geometry`);
  const shells = [];
  shells.push({ ...band(p, quality).shell, kind: 'metal' });
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
