# Measure the +x flower of a solitaire GLB (ring axis z, stone +y): exact centre, petal lobes, relief height above the surrounding base.
# usage: python3 -I tools/meshy/measure_flower.py IN.glb      (works on site/solitaire2_sym.glb; the -x flower is its mirror)
import sys, json, struct, numpy as np
b = open(sys.argv[1], 'rb').read(); jl, _ = struct.unpack('<II', b[12:20]); j = json.loads(b[20:20 + jl]); BIN = b[20 + jl + 8:]
a = j['accessors'][0]; v = j['bufferViews'][a['bufferView']]; o = v['byteOffset'] + a.get('byteOffset', 0)
P = np.unique(np.round(np.frombuffer(BIN, np.float32, a['count'] * 3, o).reshape(-1, 3).astype(float), 5), axis=0)
P = P[(P[:, 1] > 0.2) & (P[:, 0] > 0.25) & (P[:, 0] < 0.9)]
rho = np.hypot(P[:, 0], P[:, 1]); th = np.arctan2(P[:, 0], P[:, 1]); s = th * 0.8; z = P[:, 2]
# flower = the high plateau: rho > 0.815 inside the coarse window
PL = 0.825                                                             # plateau threshold: the vine ribbons stay <= ~0.80
w = (rho > PL) & (np.abs(s - 0.53) < 0.16) & (np.abs(z) < 0.13)
# iterate: centroid of high vertices, then keep only those within 0.115 of it (drops vine ribbons touching the window)
c = np.array([s[w].mean(), z[w].mean()])
for _ in range(10):
    d = np.hypot(s - c[0], z - c[1]); k = (rho > PL) & (d < 0.13); c = np.array([s[k].mean(), z[k].mean()])
d = np.hypot(s - c[0], z - c[1]); k = (rho > PL) & (d < 0.13)
thc = c[0] / 0.8; cx, cy = 0.8 * 0 + np.sin(thc), np.cos(thc)          # unit direction of the flower normal in the xy-plane
print('flower centre: arc s %.4f z %.4f  -> angle from +y %.2f deg; ring-surface normal (%.4f, %.4f, 0)' % (c[0], c[1], np.degrees(thc), cx, cy))
rt = rho[(d < 0.02)]; print('bead/centre zone (r<0.02): rho min %.4f mean %.4f max %.4f' % (rt.min(), rt.mean(), rt.max()))
print('flower plateau rho: max %.4f, p95 %.4f; plateau verts %d' % (rho[k].max(), np.percentile(rho[k], 95), k.sum()))
# polar outline of the flower (local frame: u = along arc, v = z), outermost radius with rho>0.80 per 10deg sector
u, vv = s - c[0], z - c[1]; ph = np.degrees(np.arctan2(vv, u)) % 360; rr = np.hypot(u, vv)
hi = (rho > PL) & (rr < 0.16)
print('outline radius per 10deg sector (plateau):')
prof = []
for a0 in range(0, 360, 10):
    m = hi & (ph >= a0) & (ph < a0 + 10); prof.append(np.percentile(rr[m], 97) if m.sum() > 5 else np.nan)
print(' '.join('%3d:%.3f' % (a0, p) for a0, p in zip(range(0, 360, 10), prof)))
pa = np.array(prof); pk = [a0 for i, a0 in enumerate(range(0, 360, 10)) if np.isfinite(pa[i]) and pa[i] >= np.nanmax([pa[i - 1], pa[(i + 1) % 36]]) and pa[i] > np.nanmean(pa)]
print('lobe peak angles (deg):', pk, ' spacing:', np.diff(pk).tolist())
# base level: ring surface around the flower, outside the plateau, within the flower window; mode of rho for 0.2<rr<0.3 and |z-cz|>0.08 (clear of the vine)
ann = (rr > 0.2) & (rr < 0.32) & (np.abs(vv) > 0.09) & (rho < 0.815)
h, e = np.histogram(rho[ann], bins=np.arange(0.6, 0.82, 0.01)); print('rho hist of ground annulus:', [(round(e[i], 2), int(h[i])) for i in range(len(h)) if h[i]])
print('model units; relief height above the plateau threshold: %.4f' % (rho[k].max() - PL))
