# usage: python3 tools/vec/notches.py IN.png OUT.png   (post-step AFTER veins.py, BEFORE ground_dots.py; then wire.py)
# D97: clean the 7 petal-gap notches of the MAIN (centre) flower. centre_fill's carved wedge and the natural V notch between
# two petal lobes do not line up, which leaves stair-step jogs, hooked/pill-shaped loops and stray dots. Per gap:
#  1. measure the natural V notch (width + centre line along the gap ray, r ~140-185) and fit a straight V to it,
#  2. template = thin slit (width NCW) from the bead moat that flares smoothly (corner rounded, sigma NSM) into that V,
#  3. rebuild the corridor: petal plateau (nearest petal height outside the corridor) x crisp wedge profile (NED px edge),
#  4. blend back to the original map by r (template fully applied up to the V fit start, gone ~NBL px later).
# Only the corridor around each gap is touched; veins / petals / bevel elsewhere unchanged.
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, dst = sys.argv[1], sys.argv[2]
E = os.environ.get
CX, CY = [float(v) for v in E('CEN', '1199.5,240').split(',')]
R0 = float(E('R0', 46)); CW = float(E('NCW', 3.5)); SM = float(E('NSM', 6)); ED = float(E('NED', 4)); BL = float(E('NBL', 22))
MG = float(E('NMG', 19)); FIT0 = float(E('NF0', 140)); FIT1 = float(E('NF1', 185))
GAPS = [float(v) for v in E('NGAPS', '28,89,150,213,250,288,325').split(',')]
H = np.array(Image.open(src)).astype(float) / 65535
h, w = H.shape
yy, xx = np.mgrid[0:h, 0:w]; dx, dy = xx - CX, yy - CY
sm = lambda x: x * x * (3 - 2 * x)
out = H.copy()
RR = np.arange(0, 400.0)
slit = np.zeros(H.shape, bool)   # template slit pixels (all gaps), used to tell real gap channels from stray pockets
for k in GAPS:
    th = np.radians(k); ux, uy = np.cos(th), np.sin(th); px, py = -uy, ux
    # 1. measure natural V notch along the ray
    rs, ws, cs = [], [], []
    for r in np.arange(FIT0, FIT1 + .1, 1.0):
        ds = np.arange(-48, 48.5, .5)
        v = ndi.map_coordinates(H, [CY + r * uy + ds * py, CX + r * ux + ds * px], order=1)
        lab, n = ndi.label(v < .3)
        best = None
        for i in range(1, n + 1):
            ii = np.where(lab == i)[0]; c = ds[ii].mean()
            if best is None or abs(c) < abs(best[0]): best = (c, ds[ii[0]], ds[ii[-1]])
        if best is None or best[1] <= -46 or best[2] >= 46: continue
        wd = best[2] - best[1]
        if wd < 16: continue
        rs.append(r); ws.append(wd); cs.append((best[1] + best[2]) / 2)
    if len(rs) < 6:
        print('gap', k, 'not enough V samples', len(rs)); continue
    rs, ws, cs = np.array(rs), np.array(ws), np.array(cs)
    b, a0 = np.polyfit(rs, ws, 1); cN = float(np.median(cs))
    rt = (CW - a0) / b                       # radius where the fitted V closes to the slit width
    rf0 = float(rs[0])
    print('gap %g: V slope %.2f tip r %.0f centre %+.1f  fit r %.0f-%.0f (%d pts)' % (k, b, rt, cN, rs[0], rs[-1], len(rs)))
    # 2. template width / centre as functions of r along the ray
    wt = np.maximum(CW, a0 + b * RR); wt = np.maximum(CW, ndi.gaussian_filter1d(wt, SM, mode='nearest'))
    ct = cN * sm(np.clip((RR - (rt - 12)) / 30, 0, 1))
    alpha = 1 - sm(np.clip((RR - (rf0 - 8)) / BL, 0, 1))
    # 3. corridor geometry per pixel
    t = dx * ux + dy * uy; d = dx * px + dy * py
    tw = np.interp(t, RR, wt); tc = np.interp(t, RR, ct); al = np.interp(t, RR, alpha)
    dd = np.abs(d - tc); hw = tw / 2
    reg = (t >= R0) & (t <= rf0 + BL) & (dd < hw + MG + 8)
    if not reg.any(): continue
    core = reg & (dd < hw + MG)
    # fill = interpolate across the gap at the SAME radius from the petal plateau on both sides (keeps the bead ramp, no facets)
    yc, xc = np.where(core)
    tt, dc, c0, h0 = t[yc, xc], d[yc, xc], tc[yc, xc], hw[yc, xc]
    side = []
    for sg in (-1, 1):
        best = np.zeros(len(tt))
        for o in np.linspace(3, MG, 8):
            dsm = c0 + sg * (h0 + o)
            v = ndi.map_coordinates(H, [CY + tt * uy + dsm * py, CX + tt * ux + dsm * px], order=1, mode='nearest')
            best = np.maximum(best, v)
        side.append(best)
    u = np.clip((dc - (c0 - h0 - 3)) / (2 * h0 + 6), 0, 1)
    Hf = np.zeros(H.shape); Hf[yc, xc] = side[0] * (1 - u) + side[1] * u
    Hf = np.where(core, Hf, H)
    Hf = ndi.gaussian_filter(Hf, 1.2)
    prof = np.clip((dd - hw) / ED + .5, 0, 1); prof = sm(prof)
    Ht = Hf * prof
    slit |= (t >= R0) & (t <= rf0 + 4) & (dd < hw + 1.5)
    M = np.clip((hw + MG + 8 - dd) / 8, 0, 1) * (t >= R0) * (t <= rf0 + BL) * al
    out = out + M * (Ht - out)
# 4. stray dark pockets (old wedge/notch leftovers) inside the flower, not part of any gap slit or outer ground: fill from the petal surface
r_ = np.hypot(dx, dy)
dark = (out < .3) & (r_ > R0 + 8) & (r_ < 300)
lab, nl = ndi.label(dark)
keep = set(np.unique(lab[dark & (r_ >= 175)])) | set(np.unique(lab[slit]))
keep.discard(0)
pk = dark & ~np.isin(lab, list(keep))
pk = ndi.binary_dilation(pk, iterations=3) & (r_ > R0 + 4)
print('stray pockets filled px', int(pk.sum()))
if pk.any():
    valid = (out > .5) & ~pk
    idx = ndi.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    Hp = ndi.gaussian_filter(out[idx[0], idx[1]], 1.5)
    mk = ndi.gaussian_filter(pk.astype(float), 1.0)
    out = out + mk * (Hp - out)
Image.fromarray(np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)).save(dst)
print('changed px', int((np.abs(out - H) > .01).sum()), 'max', float(np.abs(out - H).max()))
