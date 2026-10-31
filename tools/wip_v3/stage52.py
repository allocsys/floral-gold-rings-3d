"""stage52 (D10): carve the ref's interior dark lines (creases, petal edges, veins) into the stage51 map.
usage: CROPX=7 python3 tools/wip_v3/stage52.py [in.png] -> /tmp/band_v3_out/band_period_v52.png
Line strength = black-tophat of ref Lab-L (kernel K), soft-thresholded, tiny components dropped, smoothed;
H2 = H - DEPTH * strength inside the ref gold (eroded RIM px) where the relief exists. Measure with idiff.py."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'; CROPX = int(os.environ.get('CROPX', 7)); S = 2; PW2 = 2396
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'band_period_v51.png'
K, TL, SPAN, RIM, DEPTH, MINPX = 21, 14, 30, 6, float(os.environ.get('DEPTH', 0.30)), 40
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H = (cv2.imread(inp, -1).astype(np.float32) / 65535)[:520]
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]], np.float32)
g = np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2), [1,3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3,3),np.uint8)), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
reg = (cv2.erode(g, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*RIM+1,)*2)) > 0) & (H > 0.3)
L = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.0), cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
bh = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (K, K)))
line = (bh > TL) & reg
lab_, n = ndi.label(line, np.ones((3, 3)))
sz = ndi.sum(line, lab_, range(1, n + 1)); line &= np.isin(lab_, 1 + np.where(sz >= MINPX)[0])
s = np.clip((bh - TL) / SPAN, 0, 1) * line
s = cv2.GaussianBlur(s.astype(np.float32), (0, 0), 1.2); s = np.clip(s * 1.6, 0, 1)
H2 = np.where(reg, np.maximum(H - DEPTH * s, 0.0), H)
print('line px %d in %d comps (kept >=%d px); carved px %d; mean depth %.3f' % (line.sum(), (sz >= MINPX).sum(), MINPX, int((H2 < H - 1e-4).sum()), float((H - H2)[H2 < H - 1e-4].mean())))
cv2.imwrite(Z + 'band_period_v52.png', np.round(np.clip(H2, 0, 1) * 65535).astype(np.uint16)); print('wrote v52')
