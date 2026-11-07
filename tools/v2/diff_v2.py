"""v2 diff vs the NEW reference picture (reference/band_face.png), independent of panel_mask.png / the map's own mask.
usage: [WIN=x,y,r extra IoU line inside a circle] [T=.03 map footprint threshold] [HI=150 LO=85] python3 tools/v2/diff_v2.py [map=maps/v2/band_period_v2.png] [out=/mnt/user-data/outputs/v2_diff.png]
Gold in the ref = brightness hysteresis on the ref's own pixels: seeds V>HI 150 (170 missed the duller mid-tone gold of the top petals), grown into V>LO (shaded gold rims) but at most GROW px from a seed
(blocks leaking into ground speckle), then 3x3 open, drop comps <150 px, fill holes <150 px. Tile = same cut as make_map_v2.py (ref panel rows 215..472, cols 70..2115 -> tile cols C0..C0+814,
40 px seam cross-fade), resized to the map's 1640x520. Map footprint = H > T.
Picture on the darkened ref: green = both, red = MISS (ref gold, map has none), blue = EXTRA (map has it, ref does not). Prints IoU and counts (all / flower disc r<340 / outside) and the mask's IoU vs maps/v2/panel_mask.png as a sanity check."""
import os, sys, cv2, numpy as np
from scipy import ndimage as ndi
mp = sys.argv[1] if len(sys.argv) > 1 else 'maps/v2/band_period_v2.png'
out = sys.argv[2] if len(sys.argv) > 2 else '/mnt/user-data/outputs/v2_diff.png'
E = lambda k, d: float(os.environ.get(k, d))
T, HI, LO, GROW = E('T', .03), E('HI', 150), E('LO', 85), int(E('GROW', 6))
TW, TH, P, C0, SEAM = 1640, 520, 814, 608, 40
ref = cv2.imread('reference/band_face.png')[215:473, 70:2116]
V = cv2.GaussianBlur(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
seed = ndi.binary_opening(V > HI, np.ones((3, 3)))
cand = V > LO
g = seed.copy()
for _ in range(GROW): g = ndi.binary_dilation(g, np.ones((3, 3))) & cand | seed
g = ndi.binary_opening(g, np.ones((3, 3)))
lab, n = ndi.label(g); ar = np.bincount(lab.ravel(), minlength=n + 1); g = np.isin(lab, [i for i in range(1, n + 1) if ar[i] >= 150])
hl, hn = ndi.label(~g); ha = np.bincount(hl.ravel(), minlength=hn + 1); g |= np.isin(hl, [i for i in range(1, hn + 1) if ha[i] < 150])
pm = cv2.imread('maps/v2/panel_mask.png', 0) > 127
print('ref-gold mask vs panel_mask: IoU %.3f  (this mask %d px, panel_mask %d px)' % ((g & pm).sum() / (g | pm).sum(), g.sum(), pm.sum()))
def periodic(a):
    e = a[:, C0:C0 + P + SEAM].copy(); t = e[:, :P].copy(); al = (np.arange(SEAM) / SEAM)[None, :]
    if a.ndim == 3: al = al[..., None]
    t[:, :SEAM] = (1 - al) * e[:, P:P + SEAM] + al * e[:, :SEAM]; return t
rs = lambda a: cv2.resize(a, (TW, TH), interpolation=cv2.INTER_CUBIC)
R = rs(periodic(g.astype(np.float32))) > .5
rc = rs(periodic(ref.astype(np.float32)))
H = cv2.imread(mp, -1).astype(np.float32) / 65535; M = H > T
yy, xx = np.mgrid[:TH, :TW]; fl = np.hypot(xx - 820, yy - 233.7) < 340
def st(n, a, b, w):
    i = (a & b & w).sum(); u = ((a | b) & w).sum(); print(f'{n}: IoU {i / u:.4f}  both {i}  MISS {(a & ~b & w).sum()}  EXTRA {(b & ~a & w).sum()}')
_w = os.environ.get('WIN')
if _w: _x, _y, _r = [float(v) for v in _w.split(',')]; st('window ', R, M, np.hypot(xx - _x, yy - _y) <= _r)
st('all    ', R, M, np.ones_like(R)); st('flower ', R, M, fl); st('outside', R, M, ~fl)
img = (rc * .35).astype(np.uint8)
for m, c in ((R & M, (0, 200, 0)), (R & ~M, (0, 0, 255)), (M & ~R, (255, 120, 0))): img[m] = (img[m] * .35 + np.array(c) * .65).astype(np.uint8)
cv2.imwrite(out, img)
