"""stage61 (D35): close the bites on bead silhouettes (ground notches open to the outside) with the bead dome, via the convex hull of the bead core.
usage: python3 tools/wip_v3/stage61.py [in.png] -> /tmp/band_v3_out/c61.png ; env SG (.12 hull rounding sigma / r), HR (1.02 hull core radius / bead r), LIM (1.06 only inside LIM*r), BPW (.5 dome power), DCL (.97 dome d clamp / r), FW (2 px feather).
Per bead: gold mask (H>.3) inside LIM*r core (d<=HR*r, component through the centre) is replaced by its convex hull; only the NEW pixels (ground notches) get H = dome(d) (d clamped to DCL*r so the rim is continuous), feathered. Gold and the rest of the map untouched."""
import sys, os, pickle, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'; PW2 = 2396
HR = float(os.environ.get('HR', 1.02)); LIM = float(os.environ.get('LIM', 1.06)); BPW = float(os.environ.get('BPW', .5)); DCL = float(os.environ.get('DCL', .97)); FW = float(os.environ.get('FW', 2)); SG = float(os.environ.get('SG', .12))
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'chain_final.png'
raw = cv2.imread(inp, -1); H = (raw.astype(np.float32) / 65535)[:520]
beads = [(x - PW2, y, r) for x, y, r in pickle.load(open(Z + 'beads.pkl', 'rb'))] + [(491, 49, 32), (1905, 49, 32)]
yy, xx = np.mgrid[:520, :PW2]; out = H.copy(); tot = 0
for cx, cy, r in beads:
    d = np.hypot(xx - cx, yy - cy); disk = d < LIM * r
    gold = (H > .3) & disk
    core = gold & (d <= HR * r); lb, nl = ndi.label(core); c = lb[int(cy), int(cx)]
    if c == 0: continue
    pts = cv2.findNonZero((lb == c).astype(np.uint8)); hull = cv2.convexHull(pts)
    hm = np.zeros(H.shape, np.uint8); cv2.fillConvexPoly(hm, hull, 1)
    hs = ndi.gaussian_filter(hm.astype(np.float32), SG * r) > .5   # round the polygon corners of the hull
    cl = (hs | gold) & (d <= HR * r)
    new = cl & ~gold
    if not new.any(): continue
    dome = .3 + .7 * np.sqrt(np.clip(1 - (np.minimum(d, DCL * r) / r) ** 2, 0, 1)) ** (2 * BPW)
    w = np.clip(ndi.gaussian_filter(new.astype(np.float32), FW / 2) * 2, 0, 1) * disk   # soft edge, still inside the disk
    w = np.where(new, 1.0, w * (H < .3))
    w = np.maximum(w, (ndi.binary_dilation(new, iterations=3) & cl).astype(np.float32))   # lift the old gold rim next to the fill (kills the dark seam)
    out = out + w * (np.maximum(out, dome) - out); tot += int(new.sum())
print('beads', len(beads), 'new px', tot, 'px changed', int((np.abs(out - H) > 1e-4).sum()), 'max raise %.2f' % (out - H).max())
res = raw.copy(); res[:520] = np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)
cv2.imwrite(Z + 'c61.png', res)
