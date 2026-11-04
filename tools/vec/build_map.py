"""Vector rebuild of the whole band map (periodic): potrace outlines + sub-pixel SDF bevel + per-shape interior denoise.
Same method as pilot_outline.py + pilot_interior.py, windowless: x wraps (period 2396), y edge-padded.
usage: python3 tools/vec/build_map.py [maps/band_raster_src.png = the old raster map, the build INPUT] [OUT=/tmp/vec/band_vec.png]  -> 16-bit 520x2396; then tools/wip_v3/wire.py OUT"""
import sys, os, time, cv2, numpy as np, potrace
from scipy import ndimage as ndi
SRC = sys.argv[1] if len(sys.argv) > 1 else 'maps/band_raster_src.png'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/vec/band_vec.png'
PAD, UP, LP, MED = 40, 4, 1.0, 5
W = float(os.environ.get('W', 10.0))   # bevel width (map px). Mesh needs walls >= ~7 site px = 14 map px (see meshmap.py) when the cone step is skipped (MESH=0)
SM = float(os.environ.get('SM', 1.6)); OPTT = float(os.environ.get('OPTT', 0.5))   # SM = mask blur before trace (map px); OPTT = potrace opttolerance
ER = int(os.environ.get('ER', 3))
TAU, LOWS = float(os.environ.get('TAU', 0)), float(os.environ.get('LOWS', 4))   # TAU>0: soft-threshold interior detail (Hm - lowpass LOWS) = kills weak lumps, keeps strong veins/grooves
os.makedirs(os.path.dirname(OUT), exist_ok=True); t0 = time.time()
H0 = cv2.imread(SRC, -1).astype(np.float32)[:520] / 65535
Hw = np.pad(np.pad(H0, ((0, 0), (PAD, PAD)), mode='wrap'), ((PAD, PAD), (0, 0)), mode='edge')
m0 = Hw > .3
big = cv2.resize(ndi.gaussian_filter(m0.astype(np.float32), SM), None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC) > .5
pl = potrace.Bitmap(big).trace(turdsize=int(12 * UP * UP), turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0, opticurve=True, opttolerance=OPTT)
print('traced %d curves %.0fs' % (len(pl), time.time() - t0), flush=True)
def bez(p0, c1, c2, p1, n=14):
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p1
OSM = float(os.environ.get('OSM', 3)); OCORN = float(os.environ.get('OCORN', 70))   # OSM = outline smoothing sigma (map px) along arclength; points near corners (turn > OCORN deg over +-1.5 map px) keep their position
def smooth_outline(p):
    """closed polyline (4x px): uniform arclength resample (0.5 px), gaussian smooth sigma OSM map px, corner-protected blend."""
    q = np.vstack([p, p[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
    if d[-1] < 40: return p
    n = int(d[-1] / 2); t = np.linspace(0, d[-1], n, endpoint=False)
    x = np.interp(t, d, q[:, 0]); y = np.interp(t, d, q[:, 1])
    sg = OSM * UP / 2     # sigma in samples (sample = 2 px of 4x grid = .5 map px)
    xs = ndi.gaussian_filter1d(x, sg, mode='wrap'); ys = ndi.gaussian_filter1d(y, sg, mode='wrap')
    k = int(round(1.5 * UP / 2)) + 1                      # +-1.5 map px in samples
    a = np.arctan2(np.roll(y, -k) - y, np.roll(x, -k) - x); b = np.arctan2(y - np.roll(y, k), x - np.roll(x, k))
    turn = np.degrees(np.abs(np.angle(np.exp(1j * (a - b)))))
    cm = (turn > OCORN).astype(np.float32)
    w = np.clip(ndi.gaussian_filter1d(ndi.maximum_filter1d(cm, 2 * k + 1, mode='wrap'), k, mode='wrap') * 1.5, 0, 1)   # 1 at corners, tapers out
    return np.c_[x * w + xs * (1 - w), y * w + ys * (1 - w)]
acc = np.zeros(big.shape, np.uint8)
for cv in pl:
    p0 = np.array([cv.start_point.x, cv.start_point.y]); pts = []
    for s in cv.segments:
        e = np.array([s.end_point.x, s.end_point.y])
        if s.is_corner: pts += [p0, np.array([s.c.x, s.c.y])]
        else: pts += list(bez(p0, np.array([s.c1.x, s.c1.y]), np.array([s.c2.x, s.c2.y]), e))
        p0 = e
    if OSM > 0: pts = smooth_outline(np.array(pts))
    layer = np.zeros(big.shape, np.uint8)
    cv2.fillPoly(layer, [np.round(np.array(pts) * 16).astype(np.int32)], 1, lineType=cv2.LINE_8, shift=4)
    acc ^= layer
vec = cv2.resize(acc.astype(np.float32), (Hw.shape[1], Hw.shape[0]), interpolation=cv2.INTER_AREA)
iou = lambda a, b: (a & b).sum() / max((a | b).sum(), 1)
if iou(vec > .5, m0) < iou(vec <= .5, m0): vec = 1 - vec; acc = 1 - acc
print('mask IoU %.4f  %.0fs' % (iou(vec > .5, m0), time.time() - t0), flush=True)
ab = acc > 0
sdf = cv2.resize(((ndi.distance_transform_edt(ab) - ndi.distance_transform_edt(~ab)) / UP).astype(np.float32), (Hw.shape[1], Hw.shape[0]), interpolation=cv2.INTER_AREA)
sm = ndi.gaussian_filter
sdf = sm(sdf, float(os.environ.get('SDFS', 1.6)))   # kills the 1/UP px staircase of the EDT on diagonal edges (shading showed it as dotted lines)
Hm = cv2.medianBlur((np.clip(Hw, 0, 1) * 65535).astype(np.uint16), MED).astype(np.float32) / 65535
lab, n = ndi.label(vec > .5); objs = ndi.find_objects(lab)
level = np.zeros_like(Hw); M = 14
for i, sl in enumerate(objs, 1):
    if sl is None: continue
    y0, y1 = max(sl[0].start - M, 0), min(sl[0].stop + M, Hw.shape[0]); x0, x1 = max(sl[1].start - M, 0), min(sl[1].stop + M, Hw.shape[1])
    reg = lab[y0:y1, x0:x1] == i
    if reg.sum() < 30: continue
    mo = m0[y0:y1, x0:x1]
    core = ndi.binary_erosion(reg & mo, iterations=ER)
    if core.sum() < 10: core = ndi.binary_erosion(reg & mo, iterations=2)
    if core.sum() < 5: core = reg & mo
    w = core.astype(np.float32)
    if w.sum() < 5: continue
    f = sm(Hm[y0:y1, x0:x1] * w, LP) / np.maximum(sm(w, LP), 1e-3)
    if TAU > 0:
        low = sm(Hm[y0:y1, x0:x1] * w, LOWS) / np.maximum(sm(w, LOWS), 1e-3)
        d = (Hm[y0:y1, x0:x1] - low) * sm(w, 1.5)          # detail only inside the core, fades to 0 at the edge zone
        f = low + np.sign(d) * np.maximum(np.abs(d) - TAU, 0)
    rd = ndi.binary_dilation(reg, iterations=2)
    sub = level[y0:y1, x0:x1]; sub[rd] = f[rd]
level = np.maximum(level, .35)
bev = np.clip(sdf / W, 0, 1); bev = bev * bev * (3 - 2 * bev)
new = np.clip(level * bev, 0, 1) * np.clip(vec + (sdf > -.3), 0, 1)
new = new[PAD:-PAD, PAD:-PAD]
assert new.shape == (520, 2396)
DSP = int(os.environ.get('DESPECKLE', 120))   # remove isolated raised comps (H>.05) smaller than DSP px (floating specks on the ground); wrap-aware
if DSP > 0:
    sh = new.shape[1] // 2; r = np.roll(new, sh, axis=1)
    lb, nb = ndi.label(r > .05); ar = np.bincount(lb.ravel(), minlength=nb + 1)
    kill = (ar < DSP) & (np.arange(nb + 1) > 0)
    print('despeckle: removed %d comps (areas %s)' % (kill.sum(), sorted(ar[kill].tolist())))
    r[kill[lb]] = 0; new = np.roll(r, -sh, axis=1)
BEAD = int(os.environ.get('BEAD', 1))   # smooth free berries: fitted ellipse + their own radial height profile (pooled over all angles, monotone, smoothed) => perfect round domes, no lumps / polygon outline
if BEAD:
    sh = new.shape[1] // 2; r = np.roll(new, sh, axis=1); lb, nb = ndi.label(r > .3); Y, X = np.mgrid[:r.shape[0], :r.shape[1]]; nbd = 0
    for i in range(1, nb + 1):
        m = lb == i; a = int(m.sum())
        if a < 2500 or a > 9000: continue
        ys = np.nonzero(m.any(axis=1))[0]
        if ys.min() < 3 or ys.max() > r.shape[0] - 4: continue
        cn, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cn, key=len)
        circ = 4 * np.pi * a / cv2.arcLength(c, True) ** 2
        (cx, cy), (MA, ma), ang = cv2.fitEllipse(c); el = np.zeros(m.shape, np.uint8); cv2.ellipse(el, ((cx, cy), (MA, ma), ang), 1, -1)
        eiou = (m & (el > 0)).sum() / (m | (el > 0)).sum()
        if circ < .85 or eiou < .91 or ndi.label(ndi.binary_fill_holes(m) & ~m)[1] > 0: continue
        t = np.radians(ang); dx, dy = X - cx, Y - cy
        rho = np.hypot((dx * np.cos(t) + dy * np.sin(t)) / (MA / 2), (-dx * np.sin(t) + dy * np.cos(t)) / (ma / 2))
        other = ndi.binary_dilation((lb > 0) & ~m, iterations=3)
        use = (rho < 1.4) & ~other
        bi = np.minimum((rho[use] / 1.4 * 140).astype(int), 139)
        prof = np.array([r[use][bi == k].mean() if (bi == k).any() else 0 for k in range(140)])
        prof = ndi.gaussian_filter1d(prof, 1.5, mode='nearest'); prof = np.minimum.accumulate(prof)   # monotone non-increasing
        rc = (np.arange(140) + .5) / 140 * 1.4; R0 = float(os.environ.get('BR0', .85)); pe = float(np.interp(R0, rc, prof)); pc = min(1.0, pe + float(os.environ.get('BRISE', .2)))
        prof = np.where(rc < R0, pe + (pc - pe) * (1 - (rc / R0) ** 2), prof)   # true cap inside rho<R0, data edge fall-off outside (continuous at R0)
        val = np.interp(rho, rc, prof, right=0)
        r[use] = val[use]; nbd += 1
    print('beads smoothed: %d' % nbd); new = np.roll(r, -sh, axis=1)
cv2.imwrite(OUT, np.round(np.clip(new, 0, 1) * 65535).astype(np.uint16))
print('shapes %d  wrote %s  seam jump |col0-col2395| mean %.4f (cur %.4f)  %.0fs' % (n, OUT, np.abs(new[:, 0] - new[:, -1]).mean(), np.abs(H0[:, 0] - H0[:, -1]).mean(), time.time() - t0))
