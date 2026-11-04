"""Vector rebuild PILOT step 1 (outlines): trace the gold mask of ONE flower window with potrace (smooth Bezier outlines),
re-rasterise, rebuild the edge profile from the new SDF, and compare silhouette roughness with the current map.
usage: python3 tools/vec/pilot_outline.py [x0 x1] -> /tmp/vec/pilot_{cur,new}.png (hillshade), prints jag metrics (same definition as wip_v3/jag.py)"""
import sys, os, cv2, numpy as np, potrace
from scipy import ndimage as ndi
X0, X1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1000, 1400)
PAD, UP, SM, W = 30, 4, 1.6, 4.0       # window pad, trace upsample, mask blur before trace (map px), bevel width (map px)
os.makedirs('/tmp/vec', exist_ok=True)
H = cv2.imread('maps/band_period.png', -1).astype(np.float32)[:520] / 65535
Hw = np.pad(H[:, X0 - PAD:X1 + PAD], ((PAD, PAD), (0, 0)), mode='edge')
m0 = Hw > .3
# smooth, upsample, threshold -> clean high-res mask, then potrace
big = cv2.resize(ndi.gaussian_filter(m0.astype(np.float32), SM), None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC) > .5
bm = potrace.Bitmap(big)
pl = bm.trace(turdsize=int(12 * UP * UP), turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0, opticurve=True, opttolerance=0.5)
def bez(p0, c1, c2, p1, n=14):
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p1
acc = np.zeros(big.shape, np.uint8); nc = 0; nseg = 0
for cv in pl:
    p0 = np.array([cv.start_point.x, cv.start_point.y]); pts = []
    for s in cv.segments:
        e = np.array([s.end_point.x, s.end_point.y])
        if s.is_corner:
            c = np.array([s.c.x, s.c.y]); pts += [p0, c]
        else:
            pts += list(bez(p0, np.array([s.c1.x, s.c1.y]), np.array([s.c2.x, s.c2.y]), e))
        p0 = e; nseg += 1
    layer = np.zeros(big.shape, np.uint8)
    cv2.fillPoly(layer, [np.round(np.array(pts) * 16).astype(np.int32)], 1, lineType=cv2.LINE_8, shift=4)
    acc ^= layer; nc += 1           # XOR handles holes (even-odd)
vec = cv2.resize(acc.astype(np.float32), (Hw.shape[1], Hw.shape[0]), interpolation=cv2.INTER_AREA)   # anti-aliased vector mask
iou = lambda a, b: (a & b).sum() / max((a | b).sum(), 1)
if iou(vec > .5, m0) < iou(vec <= .5, m0): vec = 1 - vec; acc = 1 - acc     # potrace outer frame flips even-odd parity
print('mask IoU vector vs current: %.4f' % iou(vec > .5, m0))
# relief: interior height from the current map (normalised-convolution fill inside old mask), edge bevel from the NEW sdf
ab = acc > 0                                                  # sub-pixel SDF: EDT on the 4x vector raster, /UP, area-downsampled (no pixel staircase)
sdf_b = (ndi.distance_transform_edt(ab) - ndi.distance_transform_edt(~ab)) / UP
sdf = cv2.resize(sdf_b.astype(np.float32), (Hw.shape[1], Hw.shape[0]), interpolation=cv2.INTER_AREA)   # >0 inside
sm = lambda a, s: ndi.gaussian_filter(a, s)
core = ndi.binary_erosion(Hw > .3, iterations=4)            # interior only: old edge slopes excluded
wgt = core.astype(np.float32)
fill = sm(Hw * wgt, 4) / np.maximum(sm(wgt, 4), 1e-3)       # extrapolated interior level up to the new outline
inner_w = ndi.gaussian_filter(core.astype(np.float32), 1.0)
base = Hw * inner_w + fill * (1 - inner_w)
bev = np.clip(sdf / W, 0, 1); bev = bev * bev * (3 - 2 * bev)
new = np.clip(np.maximum(base, .35) * bev, 0, 1) * np.clip(vec * 1.0 + (sdf > -0.3), 0, 1)
def jag(Hm, SIG=3):
    m = Hm > .3
    s = ndi.distance_transform_edt(~m) - ndi.distance_transform_edt(m)
    g = ndi.gaussian_filter(s, SIG, mode='nearest'); b = np.abs(s) <= 1.0
    inner = np.zeros(Hm.shape, bool); inner[PAD + 20:-PAD - 20, PAD + 20:-PAD - 20] = True
    d = np.abs(s - g)[b & inner]
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE); cor = 0
    for c in cs:
        c = c[:, 0, :].astype(float)
        if len(c) < 8: continue
        a = np.roll(c, -3, 0) - c; b2 = c - np.roll(c, 3, 0)
        cosv = (a * b2).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b2, axis=1) + 1e-9)
        cor += int((cosv < .5).sum())
    return d.mean(), np.percentile(d, 95), int(b.sum()), cor
def shade(Hm):
    gy, gx = np.gradient(ndi.gaussian_filter(Hm * 14, .8)); s = np.clip(.5 + (-gx - gy) * .9, 0, 1)
    return cv2.resize((s * 255).astype(np.uint8), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
for n, Hm in (('cur', Hw), ('new', new)):
    print('%-3s jag mean %.3f p95 %.3f  boundary px %d  corners %d' % ((n,) + jag(Hm)))
    cv2.imwrite('/tmp/vec/pilot_%s.png' % n, shade(Hm))
print('curves', nc, 'segments', nseg)
cv2.imwrite('/tmp/vec/pilot_pair.png', np.hstack([shade(Hw), shade(new)]))
