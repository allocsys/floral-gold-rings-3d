"""v2 silhouette diff: map (H>T) vs the ref gold mask for the same tile, drawn on the darkened ref colour tile.
usage: [T=.03 map threshold] python3 tools/v2/diff_v2.py [map=maps/v2/band_period_v2.png] [out=/mnt/user-data/outputs/v2_diff.png]
green = both, red = MISS (gold in ref, not in map), blue = EXTRA (map has it, ref does not). Ref tile = same cut as make_map_v2.py (cols C0..C0+814, 40 px seam cross-fade), resized to 1640x520.
Prints IoU and pixel counts, overall and for the flower disc (r<340 about (820,233.7)) and outside it."""
import sys, cv2, numpy as np
mp = sys.argv[1] if len(sys.argv) > 1 else 'maps/v2/band_period_v2.png'
out = sys.argv[2] if len(sys.argv) > 2 else '/mnt/user-data/outputs/v2_diff.png'
import os; T = float(os.environ.get('T', .03)); TW, TH, P, C0, SEAM = 1640, 520, 814, 608, 40
def periodic(a):
    e = a[:, C0:C0 + P + SEAM].copy(); t = e[:, :P].copy(); al = (np.arange(SEAM) / SEAM)[None, :]
    if a.ndim == 3: al = al[..., None]
    t[:, :SEAM] = (1 - al) * e[:, P:P + SEAM] + al * e[:, :SEAM]; return t
mask = cv2.imread('maps/v2/panel_mask.png', 0).astype(np.float32) / 255
ref = cv2.imread('reference/band_face.png')[215:473, 70:2116].astype(np.float32)
R = cv2.resize(periodic(mask), (TW, TH), interpolation=cv2.INTER_CUBIC) > .5
rc = cv2.resize(periodic(ref), (TW, TH), interpolation=cv2.INTER_CUBIC)
H = cv2.imread(mp, -1).astype(np.float32) / 65535; M = H > T
yy, xx = np.mgrid[:TH, :TW]; fl = np.hypot(xx - 820, yy - 233.7) < 340
def st(n, a, b, w):
    i = (a & b & w).sum(); u = ((a | b) & w).sum(); print(f'{n}: IoU {i / u:.4f}  both {i}  MISS {(a & ~b & w).sum()}  EXTRA {(b & ~a & w).sum()}')
st('all   ', R, M, np.ones_like(R)); st('flower', R, M, fl); st('outside', R, M, ~fl)
img = (rc * .35).astype(np.uint8)
for m, c in ((R & M, (0, 200, 0)), (R & ~M, (0, 0, 255)), (M & ~R, (255, 120, 0))): img[m] = (img[m] * .35 + np.array(c) * .65).astype(np.uint8)
cv2.imwrite(out, img)
