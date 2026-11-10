"""Slit-rim raggedness: dark slits/holes inside the gold, ref vs map (python3 tools/wip_v3/rdiff.py [map.png] [outdir]).

Slit = non-gold connected component that is NOT the big background (area < MAXA, default 6000 px at 2x scale).
Per mask (ref gold mask as in diff.py, map = H>0.3) it reports, over all slits:
  rag   = raw rim length / rim length of the same slit after gaussian smoothing the mask (sigma SM px); 1.00 = smooth
  jit   = mean |signed-distance(raw) - signed-distance(smoothed)| on the rim (px)
  n, area. Plus matching: slits matched by centroid (<12 px): area ratio and rim distance (mean |SDF_map - SDF_ref| on the ref rim).
Writes rdiff_<map>.png (ref rim white, map rim red, on grey gold).
"""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
mp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/band_v3_out/chain_final.png'
Z = (sys.argv[2] if len(sys.argv) > 2 else '/tmp/band_v3_out').rstrip('/') + '/'
CROPX, S, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
MAXA, SM = int(os.environ.get('MAXA', 6000)), float(os.environ.get('SM', 2.5))
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX * S:CROPX * S + 520, PW2:2 * PW2]
H = cv2.imread(mp, -1).astype(np.float32)[:520] / 65535
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69, 143, 159], [211, 132, 175], [13, 134, 135], [147, 143, 178]], np.float32)
g = np.isin(((lab[:, :, None, :] - C[None, None]) ** 2).sum(3).argmin(2), [1, 3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
h = H > 0.3

def sdf(m):  # signed distance, + inside gold
    return ndi.distance_transform_edt(m) - ndi.distance_transform_edt(~m)

def slits(m):
    lb, n = ndi.label(~m)
    ar = ndi.sum(np.ones_like(lb), lb, range(1, n + 1))
    keep = [i + 1 for i, a in enumerate(ar) if 30 <= a < MAXA]
    return lb, keep

def rag(m):
    lb, keep = slits(m)
    out = []
    for i in keep:
        s = lb == i
        ys, xs = np.where(s); y0, y1, x0, x1 = max(ys.min() - 8, 0), ys.max() + 9, max(xs.min() - 8, 0), xs.max() + 9
        s = s[y0:y1, x0:x1]
        sm = cv2.GaussianBlur(s.astype(np.float32), (0, 0), SM) > 0.5
        per = lambda a: (a & ~ndi.binary_erosion(a)).sum()
        d_raw, d_sm = sdf(~s), sdf(~sm)  # + inside gold
        rim = s ^ ndi.binary_erosion(s)
        out.append((s.sum(), per(s) / max(per(sm), 1), np.abs(d_raw - d_sm)[rim].mean(), ndi.center_of_mass(lb == i)))
    return out

def summ(name, r):
    a = np.array([x[0] for x in r]); rg = np.array([x[1] for x in r]); jt = np.array([x[2] for x in r])
    print('%-4s slits %3d | area %7d | rag mean %.3f (area-wtd %.3f) max %.2f | jit mean %.2f px (area-wtd %.2f)' %
          (name, len(r), a.sum(), rg.mean(), (rg * a).sum() / a.sum(), rg.max(), jt.mean(), (jt * a).sum() / a.sum()))
rr, rm = rag(g), rag(h)
summ('ref', rr); summ('map', rm)
sg, sh = sdf(g), sdf(h)
lg, kg = slits(g); lh, kh = slits(h)
cm = np.array([x[3] for x in rm]) if rm else np.zeros((0, 2))
dist, ratio = [], []
for (a, _, _, c) in rr:
    if not len(cm): break
    d = np.hypot(cm[:, 0] - c[0], cm[:, 1] - c[1]); j = d.argmin()
    if d[j] < 12: ratio.append(rm[j][0] / a)
rim_ref = (lg > 0) & np.isin(lg, kg)
rim_ref = rim_ref ^ ndi.binary_erosion(rim_ref)
print('matched slits %d/%d | map/ref area ratio median %.2f | mean |SDF_map-SDF_ref| on ref slit rim %.2f px' %
      (len(ratio), len(rr), np.median(ratio) if ratio else 0, np.abs(sh - sg)[rim_ref].mean()))
vis = np.zeros(g.shape + (3,), np.uint8); vis[g] = (70, 70, 70)
for m, col in ((g, (255, 255, 255)), (h, (0, 0, 255))):
    l, k = slits(m); s = np.isin(l, k); vis[s ^ ndi.binary_erosion(s)] = col
out = Z + 'rdiff_' + os.path.splitext(os.path.basename(mp))[0] + '.png'
cv2.imwrite(out, vis); print('wrote', out)
