#!/usr/bin/env python3
"""D87 (S-3): raised micro-dots on the bare ground (ref ground is stippled with dozens of tiny dots; map ground was perfectly flat).
usage: python3 tools/vec/ground_dots.py IN.png OUT.png   (LAST step, after centre_fill.py; then wire.py)
Dots are placed (seeded, poisson-ish) only where the ground is >= CLR px from any gold and inside the band rows YM..h-YM, in the left
half [0,w/2] and mirrored x -> w-x (the map is a mirrored period: axis at 0 and w/2... centre flower at w/2).
env SEED 7, RMIN 3, RMAX 6.5, HMIN .12, HMAX .26, CLR 20, SP 24 (min centre spacing), YM 46, NMAX 400
"""
import os, sys
import numpy as np
import scipy.ndimage as ndi
from PIL import Image
E = lambda k, d: float(os.environ.get(k, d))
SEED = int(E('SEED', 7)); RMIN, RMAX = E('RMIN', 3), E('RMAX', 6.5); HMIN, HMAX = E('HMIN', .12), E('HMAX', .26)
CLR, SP, YM, NMAX = E('CLR', 20), E('SP', 24), int(E('YM', 46)), int(E('NMAX', 400))
H = np.array(Image.open(sys.argv[1])).astype(np.float64) / 65535
h, w = H.shape
gold = H > .05
ok = ndi.distance_transform_edt(~gold) >= CLR
ok[:YM] = False; ok[h - YM:] = False
sh = w // 2
# wrap-aware clearance: roll so the seam is inside the array
ok = np.roll(ndi.distance_transform_edt(~np.roll(gold, sh, axis=1)) >= CLR, -sh, axis=1)
ok[:YM] = False; ok[h - YM:] = False
ok[:, sh + 1:] = False                      # left half only, mirrored afterwards
ys, xs = np.nonzero(ok)
rng = np.random.default_rng(SEED)
order = rng.permutation(len(ys))
pts = []
for i in order:
    x, y = xs[i], ys[i]
    # also keep clear of the mirror image
    if any(np.hypot(x - px, y - py) < SP for px, py in pts): continue
    if np.hypot(x - (w - x), 0) < SP and x > w / 2 - SP: continue
    pts.append((x, y))
    if len(pts) >= NMAX: break
out = H.copy()
yy, xx = np.mgrid[0:h, 0:w]
for (x, y) in pts:
    r = rng.uniform(RMIN, RMAX); hh = rng.uniform(HMIN, HMAX)
    for cx in {x % w, (w - x) % w}:
        dxw = np.abs(xx - cx); dxw = np.minimum(dxw, w - dxw); rr = np.hypot(dxw, yy - y)
        dome = hh * np.sqrt(np.clip(1 - (rr / r) ** 2, 0, 1)) * np.clip((r - rr) / 1.2, 0, 1)
        out = np.maximum(out, dome)
Image.fromarray(np.clip(np.round(out * 65535), 0, 65535).astype(np.uint16)).save(sys.argv[2])
print('ground dots', len(pts), 'x2 mirrored; changed px', int((out > H + 1e-4).sum()))
