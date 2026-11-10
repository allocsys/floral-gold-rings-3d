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
GR0, GR1 = float(os.environ.get('GR0', 160)), float(os.environ.get('GR1', 200))   # D94: detect the gaps beyond the fill (r 160-200) = all 7 real petal gaps; r 92-128 found a false groove through the odd top petal and missed its two gaps
m = (r >= GR0) & (r < GR1)
g = np.array([(H[m & (a >= k) & (a < k + 1)] < .35).mean() for k in range(360)])
gs = np.convolve(np.r_[g[-3:], g, g[:3]], np.ones(5) / 5, 'same')[3:-3]
pk, _ = find_peaks(np.r_[gs, gs[:30]], height=.12, distance=15)
gaps = sorted({(int(p % 360), float(gs[p % 360])) for p in pk})
print('grooves at', [(k, round(s, 2)) for k, s in gaps])
# D95: per-gap natural notch tip radius along the gap ray (first dark px beyond r100); tip > RF+4 = odd-top-petal gaps (petals merged inside the tip)
tips = {}
for k, s in gaps:
    th = np.radians(k); rr = np.arange(R0 + 8, 270.0)
    v = ndi.map_coordinates(H, [CY + rr * np.sin(th), CX + rr * np.cos(th)], order=1, mode='wrap')
    ii = np.where((v < .3) & (rr > 100))[0]
    tips[k] = float(rr[ii[0]]) if len(ii) else RF
RM = float(os.environ.get('RM', 160)); LI = float(os.environ.get('LI', .68)); CW = float(os.environ.get('CW', 3.5))
# perpendicular distance to nearest groove line (px)
wmul = np.ones(H.shape)
for k, s in gaps:
    th = np.radians(k); d = np.abs(-dx * np.sin(th) + dy * np.cos(th)); d = np.where(dx * np.cos(th) + dy * np.sin(th) > 0, d, 1e9)
    if tips[k] > RF + 4: half = np.full(H.shape, CW / 2)         # narrow wedge up to the notch tip
    else: half = (GW0 + (GW1 - GW0) * np.clip((r - R0) / (RF - R0), 0, 1)) / 2   # wedge widens to the rim, then stays (natural notch takes over)
    wmul = np.minimum(wmul, np.clip((d / half - .6) / .8, 0, 1))
# D95: ONE smooth ramp per petal: from LI at the bead moat to the real outer petal height at r=RM (nearest outer petal height, smoothed), lobes domed between the gap lines
valid = (H > .5) & (r >= RM)
idx = ndi.distance_transform_edt(~valid, return_distances=False, return_indices=True)
Hm = np.clip(ndi.gaussian_filter(H[idx[0], idx[1]], 3.0), .55, .9)
t = np.clip((r - R0 - BR) / (RM - R0 - BR), 0, 1); S = t * t * (3 - 2 * t)
Lp = LI + (Hm - LI) * S
sa = np.array(sorted(k for k, sc in gaps if sc > .6), float)
if len(sa) >= 3:
    ext = np.r_[sa[-1] - 360, sa, sa[0] + 360]
    ii = np.clip(np.searchsorted(ext, a, side='right'), 1, len(ext) - 1)
    u = (a - ext[ii - 1]) / (ext[ii] - ext[ii - 1])
    lobe = (1 - LD) + LD * 4 * u * (1 - u)
    Lp = Lp * (1 - (1 - lobe) * (1 - S))
bev = np.clip((r - R0) / BR, 0, 1); bev = bev * bev * (3 - 2 * bev)      # bevel up from the bead moat
gnd = (H < .3) & (r >= 105) & (r < 300)                                    # natural notches beyond the fill stay open; isolated dark pockets (not connected to the outer ground) are filled
lab, nl = ndi.label(gnd); keep = np.unique(lab[gnd & (r >= RM + 40)]); nat = ndi.gaussian_filter(np.isin(lab, keep[keep > 0]).astype(float), 1.0)
# D95: vein hairlines continue inward to the bead: 2 per petal at the petal mid-angle, offset VO at RM converging to the bead
VO, VW, VD = float(os.environ.get('VO', 4.5)), float(os.environ.get('VW', 1.2)), float(os.environ.get('VD', .12))
vf = np.ones(H.shape)
if len(sa) >= 3:
    for i in range(len(ext) - 1):
        a0, a1 = ext[i], ext[i + 1]
        if a1 - a0 > 90 or a1 < -1 or a0 > 361: continue
        th = np.radians((a0 + a1) / 2); d = -dx * np.sin(th) + dy * np.cos(th); fw = dx * np.cos(th) + dy * np.sin(th) > 0
        tt = np.clip((r - R0 - 8) / (RM - R0 - 8), 0, 1); off = 1.2 + (VO - 1.2) * tt
        dep = VD * np.clip((r - R0 - 6) / 14, 0, 1) * (1 - .5 * tt)
        for sg in (-1, 1): vf = np.minimum(vf, 1 - np.where(fw, dep * np.exp(-((d - sg * off) / VW) ** 2), 0))
add = np.where((r >= R0) & (r < RM + 25), Lp * wmul * bev * (1 - nat) * vf, 0)
wr = np.clip((RM + 20 - r) / 20, 0, 1); wr = wr * wr * (3 - 2 * wr)
add = ndi.gaussian_filter(add, .8)
out = np.maximum(H, add * wr * (r >= R0 - 1))
# D94: gaps whose notch tip lies beyond RF (odd top petal): petals are merged inside the tip, so carve the thin dark wedge into H too
for k, s in gaps:
    tip = tips[k]
    if tip <= RF + 4: continue
    print('carve gap', k, 'tip r', tip); th = np.radians(k)
    d = np.abs(-dx * np.sin(th) + dy * np.cos(th)); d = np.where(dx * np.cos(th) + dy * np.sin(th) > 0, d, 1e9)
    wm = np.clip((d / (CW / 2) - .6) / .8, 0, 1)
    fr = np.clip((tip + 5 - r) / 8, 0, 1) * (r >= R0)
    out = out * (1 - fr * (1 - wm))
out = np.where((r > 38) & (r < R0 - 1) & (H > .02), np.minimum(out, H * np.clip((R0 - 1 - r) / 4, 0, 1)), out)   # D93 clean thin moat ring round the bead (r 40..R0)
Image.fromarray(np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)).save(dst)
print('changed px', int((np.abs(out - H) > .01).sum()), 'max', float(np.abs(out - H).max()))
