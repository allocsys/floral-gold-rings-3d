"""stage58 (D25): remove ghost bumps = relief on pixels that are ground in the reference.
usage: python3 tools/wip_v3/stage58.py [in.png] -> /tmp/band_v3_out/band_period_v58x.png ; env DIST (6 px: protected band around ref gold, keeps rim shoulders), HMIN (.03: ghost threshold), FEATH (2 px), MINA (6 px: min patch area).
Ghost = pixel with H>HMIN that lies farther than DIST px from the ref gold mask (diff.py definition: Lab k-means clusters 1,3, 3x3 open+close) and is not part of the silhouette (H<=.3 only; H>.3 untouched).
Replaced by 0.0013 (map ground median), feathered. Everything inside the protected band or H>.3 is untouched.
Chain (v60): ... -> stage57 (c57) -> stage58 = chain_final.png.
"""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'
DIST = float(os.environ.get('DIST', 6)); HMIN = float(os.environ.get('HMIN', .03)); FEATH = float(os.environ.get('FEATH', 2)); MINA = int(os.environ.get('MINA', 6))
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'band_period_v57.png'
raw = cv2.imread(inp, -1); H = (raw.astype(np.float32) / 65535)[:520]
CROPX = int(os.environ.get('CROPX', 7)); T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX * 2:CROPX * 2 + 520, 2396:2 * 2396]
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69, 143, 159], [211, 132, 175], [13, 134, 135], [147, 143, 178]], np.float32)
g = np.isin(((lab[:, :, None, :] - C[None, None]) ** 2).sum(3).argmin(2), [1, 3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
dist = ndi.distance_transform_edt(~g)
m = (H > HMIN) & (H <= .3) & (dist > DIST)
lb, n = ndi.label(ndi.binary_dilation(m, iterations=1)); ar = ndi.sum(m, lb, range(1, n + 1))
patch = np.isin(lb, [i for i, a in enumerate(ar, 1) if a >= MINA]) & m
print('ghost px %d (patches %d), H mean %.3f max %.3f' % (patch.sum(), int((ar >= MINA).sum()), H[patch].mean() if patch.any() else 0, H[patch].max() if patch.any() else 0))
w = np.clip(cv2.GaussianBlur(ndi.binary_dilation(patch, iterations=2).astype(np.float32), (0, 0), FEATH) * 1.6, 0, 1)
w = np.where(H > .3, 0, w) * (dist > DIST)
H2 = np.where(w > 0, H * (1 - w) + .0013 * w, H)
out = np.vstack([np.round(H2 * 65535).astype(np.uint16), raw[520:]]) if raw.shape[0] > 520 else np.round(H2 * 65535).astype(np.uint16)
print('px changed %d' % int((np.abs(H2 - H) > 1e-4).sum()))
cv2.imwrite(Z + 'band_period_v58x.png', out); print('wrote v58x (stage58)')
