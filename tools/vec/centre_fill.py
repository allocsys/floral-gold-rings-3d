# usage: python3 tools/vec/centre_fill.py IN.png OUT.png   (post-step AFTER zonal.py; then wire.py)
# Petals reach the centre bead: fills the dark moat/ring around the main flower's centre bead with a petal-level plateau
# and keeps thin radial grooves along the petal gaps / central veins (angles auto-detected). Not idempotent-safe? It is (max with old).
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import find_peaks
src, dst = sys.argv[1], sys.argv[2]
CX, CY = [float(v) for v in os.environ.get('CEN', '1199.5,240').split(',')]
R0 = float(os.environ.get('R0', 46)); RF = float(os.environ.get('RF', 125)); RFE = float(os.environ.get('RFE', 10))
PL0, PL1 = float(os.environ.get('PL0', .74)), float(os.environ.get('PL1', .72)); G0 = float(os.environ.get('G0', 1.3)); GK = float(os.environ.get('GK', .02)); GD = float(os.environ.get('GD', .5))
GW0 = float(os.environ.get('GW0', 3)); GW1 = float(os.environ.get('GW1', 13)); BR = float(os.environ.get('BR', 7)); LD = float(os.environ.get('LD', .14)); RD = float(os.environ.get('RD', .10))   # D93: petal-gap wedge total width at R0 / at RF (px), bevel ramp off the bead moat
H = np.array(Image.open(src)).astype(float) / 65535
h, w = H.shape
yy, xx = np.mgrid[0:h, 0:w]
dx, dy = xx - CX, yy - CY
r = np.hypot(dx, dy); a = np.degrees(np.arctan2(dy, dx)) % 360
m = (r >= 92) & (r < 128)
g = np.array([(H[m & (a >= k) & (a < k + 1)] < .35).mean() for k in range(360)])
gs = np.convolve(np.r_[g[-3:], g, g[:3]], np.ones(5) / 5, 'same')[3:-3]
pk, _ = find_peaks(np.r_[gs, gs[:30]], height=.12, distance=15)
gaps = sorted({(int(p % 360), float(gs[p % 360])) for p in pk})
print('grooves at', [(k, round(s, 2)) for k, s in gaps])
# perpendicular distance to nearest groove line (px)
dmin = np.full(H.shape, 1e9); wmul = np.ones(H.shape)
for k, s in gaps:
    th = np.radians(k); d = np.abs(-dx * np.sin(th) + dy * np.cos(th)); d = np.where(dx * np.cos(th) + dy * np.sin(th) > 0, d, 1e9)
    if s > .6:     # D93: real petal gap = narrow dark wedge to ground, widening outward (petals run in to the bead moat)
        half = (GW0 + (GW1 - GW0) * np.clip((r - R0) / (RF - R0), 0, 1)) / 2; fl = 0.0
    else:          # central vein: hairline, shallow
        half = (G0 + GK * np.clip(r - R0, 0, None)) * .6 / 2; fl = GD
    q = d / half
    wmul = np.minimum(wmul, fl + (1 - fl) * np.clip((q - .6) / .8, 0, 1))
Lp = PL0 + (PL1 - PL0) * np.clip((r - R0) / (RF - R0), 0, 1)
# continue the neighbouring petal surface inward (nearest petal height, smoothed), blend to the plateau near the bead
NB = float(os.environ.get('NB', 1.0))   # D93 plateau (no nearest-petal facets); petal lobes are domed below
valid = (H > .3) & (r > RF + 6)
idx = ndi.distance_transform_edt(~valid, return_distances=False, return_indices=True)
pv = ndi.gaussian_filter(H[idx[0], idx[1]], 4.0)
t = NB * np.clip((RF - r) / (RF - R0), 0, 1)
Lp = np.where(r < RF + 20, (1 - t) * np.clip(pv, .55, .85) + t * Lp, Lp)
# D93: each petal lobe = smooth dome between its two gap lines (u 0..1 across the sector), rising outward
sa = np.array(sorted(k for k, sc in gaps if sc > .6), float)
if len(sa) >= 3:
    ext = np.r_[sa[-1] - 360, sa, sa[0] + 360]
    ii = np.clip(np.searchsorted(ext, a, side='right'), 1, len(ext) - 1)
    u = (a - ext[ii - 1]) / (ext[ii] - ext[ii - 1])
    lobe = (1 - LD) + LD * 4 * u * (1 - u)
    Lp = Lp * lobe * (1 - RD + RD * np.clip((r - R0) / (RF - R0), 0, 1))
wr = np.clip((RF + RFE - r) / (2 * RFE), 0, 1); wr = wr * wr * (3 - 2 * wr)   # smoothstep taper at the rim
wr = np.where(r < RF - RFE, 1.0, wr)
bev = np.clip((r - R0) / BR, 0, 1); bev = bev * bev * (3 - 2 * bev)      # D93 bevel up from the bead moat
add = np.where(r >= R0, Lp * wr * wmul * bev, 0)
add = ndi.gaussian_filter(add, .8)
out = np.maximum(H, add * (r >= R0 - 1))
out = np.where((r > 38) & (r < R0 - 1) & (H > .02), np.minimum(out, H * np.clip((R0 - 1 - r) / 4, 0, 1)), out)   # D93 clean thin moat ring round the bead (r 40..R0)
Image.fromarray(np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)).save(dst)
print('changed px', int((np.abs(out - H) > .01).sum()), 'max', float(np.abs(out - H).max()))
