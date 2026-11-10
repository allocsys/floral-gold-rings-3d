"""stage59 (D29): fill skull-like recesses in beads (pin hole 'eye socket' + side notches) with a clean dome.
usage: python3 tools/wip_v3/stage59.py [in.png] -> /tmp/band_v3_out/c59.png ; env KF (.82 fill radius / bead r), FW (.1 feather / r), BPW (.5 dome power as stage50).
Beads = beads.pkl (T2 coords, middle tile -> x-2396) + the 2 top beads (491,49,32),(1905,49,32). Inside KF*r: H = max(H, dome) feathered; outside untouched (silhouette rim unchanged)."""
import sys, os, pickle, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'; PW2 = 2396
KF = float(os.environ.get('KF', .82)); FW = float(os.environ.get('FW', .1)); BPW = float(os.environ.get('BPW', .5)); SIL = int(os.environ.get('SIL', 1))   # SIL=1 keep silhouette (default)
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'chain_final.png'
raw = cv2.imread(inp, -1); H = (raw.astype(np.float32) / 65535)[:520]
beads = [(x - PW2, y, r) for x, y, r in pickle.load(open(Z + 'beads.pkl', 'rb'))] + [(491, 49, 32), (1905, 49, 32)]
yy, xx = np.mgrid[:520, :PW2]; out = H.copy(); n = 0
for cx, cy, r in beads:
    d = np.hypot(xx - cx, yy - cy)
    dome = .3 + .7 * np.sqrt(np.clip(1 - (d / r) ** 2, 0, 1)) ** (2 * BPW)
    w = np.clip((KF * r - d) / (FW * r), 0, 1)
    if SIL:   # keep the silhouette: raise gold dents (H>.3) and ENCLOSED holes only; ground bites open to the outside stay
        lb, nl = ndi.label((out < .3) & (d < r * 1.3))
        edge = set(np.unique(lb[(d >= r * 1.25) & (d < r * 1.3)])) - {0}
        enc = (out < .3) & (d < KF * r) & ~np.isin(lb, list(edge)) & (lb > 0)
        enc = ndi.binary_dilation(enc, iterations=2)
        w = w * ((out >= .3) | enc)
    out = out + w * (np.maximum(out, dome) - out)
print('beads', len(beads), 'px changed', int((np.abs(out - H) > 1e-4).sum()), 'max raise %.2f' % (out - H).max())
res = raw.copy(); res[:520] = np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)
cv2.imwrite(Z + 'c59.png', res)
