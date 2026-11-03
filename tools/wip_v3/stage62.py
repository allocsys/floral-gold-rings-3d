"""stage62 (D36): replace the star-shaped speck ghost (map ~x342-391,y272-321, between the beads) by the single small pearl the reference really has there.
usage: python3 tools/wip_v3/stage62.py [in.png] -> /tmp/band_v3_out/c62.png ; env CX CY (358,300 ref dot peak, T2 x-2396), RD (7 dome radius px), HM (.72 dome max, like the other small pearl at x960), WIN (342,272,391,321 window of the ghost).
Gold component(s) inside WIN are flattened to the local ground level (median of H<.15 around), then a dome (sqrt profile like stage50/59, .3 -> HM) is drawn at the ref peak."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'
CX = float(os.environ.get('CX', 358)); CY = float(os.environ.get('CY', 300)); RD = float(os.environ.get('RD', 7)); HM = float(os.environ.get('HM', .72))
x0, y0, x1, y1 = [int(v) for v in os.environ.get('WIN', '338,268,396,326').split(',')]
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'chain_final.png'
raw = cv2.imread(inp, -1); H = (raw.astype(np.float32) / 65535)[:520]
win = np.zeros(H.shape, bool); win[y0:y1, x0:x1] = True
lb, n = ndi.label(H > .15); ids = np.unique(lb[win]); ids = ids[ids > 0]
ghost = np.isin(lb, ids) & ~(np.hypot(*np.mgrid[:520, :H.shape[1]][::-1] - np.array([[[CX]], [[CY]]]) * 0) < 0)   # components touching the window
assert ghost.sum() < 4000, 'ghost component too big (touches other structure): %d px' % ghost.sum()
ring = ndi.binary_dilation(ghost, iterations=12) & ~ndi.binary_dilation(ghost, iterations=3) & (H < .15)
gl = float(np.median(H[ring])) if ring.any() else .03
m = ndi.gaussian_filter(ndi.binary_dilation(ghost, iterations=2).astype(np.float32), 1.0)
out = H * (1 - m) + gl * m
yy, xx = np.mgrid[:520, :H.shape[1]]; d = np.hypot(xx - CX, yy - CY)
dome = .3 + (HM - .3) * np.sqrt(np.clip(1 - (d / RD) ** 2, 0, 1)); dome = np.where(d < RD, dome, 0)
wd = np.clip((RD + .5 - d) / 1.5, 0, 1); out = out + wd * (np.maximum(out, dome) - out)
print('ghost px', int(ghost.sum()), 'ground level %.3f' % gl, 'px changed', int((np.abs(out - H) > 1e-4).sum()))
res = raw.copy(); res[:520] = np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)
cv2.imwrite(Z + 'c62.png', res)
