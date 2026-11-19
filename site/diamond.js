// Round brilliant diamond (flat facets), pure geometry. Axis y, culet down. Units = model units.
// 57 facets: table, 8 star, 8 bezel (2 tris each), 16 upper girdle, girdle band (16 quads), 16 lower girdle, 8 pavilion mains (2 tris each).
import * as THREE from 'three';
export const DIA = { Rg: 0.137, culetY: 0.8818, crown: 0.16, pav: 0.43, table: 0.56, girdle: 0.018, rhK: 0.78, rsK: 0.52 };
export function diamondData(o = {}) {
  const P = { ...DIA, ...o }, D = 2 * P.Rg, tg = P.girdle * D, ch = P.crown * D, pd = P.pav * D;
  const yb = P.culetY + pd, yg = yb + tg, yt = yg + ch, rt = P.table * P.Rg, Rg = P.Rg, A = Math.PI / 4, c22 = Math.cos(A / 2);
  const V = (r, a, y) => [r * Math.cos(a), y, r * Math.sin(a)];
  const T = [], Gm = [], Gi = [], Bm = [], Bi = [], S = [], H = [], C = [0, P.culetY, 0];
  const rs = rt + P.rsK * (Rg - rt), ys = yt - (ch / (Rg - rt)) * (rs * c22 - rt), rh = P.rhK * Rg, yh = P.culetY + rh * c22 * pd / Rg;
  for (let k = 0; k < 8; k++) {
    T.push(V(rt, k * A, yt)); Gm.push(V(Rg, k * A, yg)); Gi.push(V(Rg, (k + .5) * A, yg));
    Bm.push(V(Rg, k * A, yb)); Bi.push(V(Rg, (k + .5) * A, yb)); S.push(V(rs, (k + .5) * A, ys)); H.push(V(rh, (k + .5) * A, yh));
  }
  const tris = [], n = i => (i + 1) % 8, p = i => (i + 7) % 8;
  for (let k = 1; k < 7; k++) tris.push([T[0], T[k], T[k + 1]]);
  for (let k = 0; k < 8; k++) {
    tris.push([T[k], T[n(k)], S[k]]);
    tris.push([T[k], S[p(k)], Gm[k]], [T[k], Gm[k], S[k]]);
    tris.push([S[k], Gm[k], Gi[k]], [S[k], Gi[k], Gm[n(k)]]);
    tris.push([Gm[k], Bm[k], Bi[k]], [Gm[k], Bi[k], Gi[k]], [Gi[k], Bi[k], Bm[n(k)]], [Gi[k], Bm[n(k)], Gm[n(k)]]);
    tris.push([H[k], Bm[k], Bi[k]], [H[k], Bi[k], Bm[n(k)]]);
    tris.push([C, H[p(k)], Bm[k]], [C, Bm[k], H[k]]);
  }
  const cen = [0, (yt + P.culetY) / 2, 0], out = tris.map(([a, b, c]) => {
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]], nn = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const m = [(a[0] + b[0] + c[0]) / 3 - cen[0], (a[1] + b[1] + c[1]) / 3 - cen[1], (a[2] + b[2] + c[2]) / 3 - cen[2]];
    return nn[0] * m[0] + nn[1] * m[1] + nn[2] * m[2] < 0 ? [a, c, b] : [a, b, c];
  });
  return { tris: out, yt, yg, yb, rt, Rg, culetY: P.culetY };
}
export function diamondGeo(o) {
  const { tris } = diamondData(o), pos = new Float32Array(tris.length * 9);
  tris.forEach((t, i) => t.forEach((v, j) => pos.set(v, i * 9 + j * 3)));
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.computeVertexNormals(); return g;
}
