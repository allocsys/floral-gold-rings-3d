"""stage63 (D37): replace the blobby ghost pair near map x941-1000,y318-374 by the 3 small pearls the reference has there (T2 peaks (956,357) r8, (985,378) r7, (944,381) r5 (radii from the visible blob extents); same dome as stage62).
usage: python3 tools/wip_v3/stage63.py [in.png] -> /tmp/band_v3_out/c63.png ; env WIN (940,316,1002,370 window of the ghost), HM (.72 dome max)."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'
HM = float(os.environ.get('HM', .72)); x0, y0, x1, y1 = [int(v) for v in os.environ.get('WIN', '940,316,1002,370').split(',')]
DOTS = [(956, 357, 8), (985, 378, 7), (944, 381, 5)]
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'chain_final.png'
raw = cv2.imread(inp, -1); H = (raw.astype(np.float32) / 65535)[:520]
win = np.zeros(H.shape, bool); win[y0:y1, x0:x1] = True
lb, n = ndi.label(H > .15); ids = np.unique(lb[win]); ids = ids[ids > 0]; ghost = np.isin(lb, ids)
assert ghost.sum() < 4000, 'ghost too big: %d px' % ghost.sum()
ring = ndi.binary_dilation(ghost, iterations=12) & ~ndi.binary_dilation(ghost, iterations=3) & (H < .15)
gl = float(np.median(H[ring])) if ring.any() else .03
m = ndi.gaussian_filter(ndi.binary_dilation(ghost, iterations=2).astype(np.float32), 1.0)
out = H * (1 - m) + gl * m
yy, xx = np.mgrid[:520, :H.shape[1]]
for cx, cy, rd in DOTS:
    d = np.hypot(xx - cx, yy - cy); dome = np.where(d < rd, .3 + (HM - .3) * np.sqrt(np.clip(1 - (d / rd) ** 2, 0, 1)), 0)
    wd = np.clip((rd + .5 - d) / 1.5, 0, 1); out = out + wd * (np.maximum(out, dome) - out)
print('ghost px', int(ghost.sum()), 'ground %.3f' % gl, 'px changed', int((np.abs(out - H) > 1e-4).sum()))
res = raw.copy(); res[:520] = np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)
cv2.imwrite(Z + 'c63.png', res)
