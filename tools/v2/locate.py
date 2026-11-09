"""T5 flaw locator. usage: [ANN=red|green|blue|magenta|yellow|white] [JSON=out.json] python3 tools/v2/locate.py shot.png [overlay.png]
A phone screenshot of the site (band seen roughly head-on) with spots circled in ANN colour (default red) -> map coordinates (x mod 1640, y; 1 map px ~ 0.5 ref px).
1 detect annotation strokes by colour (HSV; gold is hue 10-30, so red/green/blue/magenta are safe), group into circles (min enclosing circle per stroke group; overlapping circles merge),
2 inpaint the strokes out, crop to the bright band region,
3 register to the map with LIGHTING-INDEPENDENT edge density (SIFT was tried: fails, shading polarity flips with the light): map side = union of Canny edges over 5 lightings, screenshot side = its own Canny edges,
  multi-scale/rotation template search at 1/4 scale on the map tiled 3x (so a seam spot still matches), top candidates refined by ECC homography at 1/2 scale, best by ECC correlation (top 5, then top 20 if < .3),
4 report each spot: map x,y, radius in map px, what is there (flower/bead/scroll/ground, ref-gold class) and the zoom.py command; overlay image with the spots on the map.
match quality = ECC correlation: >= .33 trusted; below that the numbers are LOW-confidence (send a flatter, closer, less tilted screenshot).
Validated only on synthetic screenshots (tools/v2/test_locate.py): 8/10 registered at median 1.5 px (max 5 px), 2/10 failed and were flagged LOW. Real screenshots of the 3D render (different shading/colour, ring curvature, UI chrome) are untested."""
import os, sys, json, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import *
shot = cv2.imread(sys.argv[1]); out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else '/mnt/user-data/outputs/locate.png'
ann = os.environ.get('ANN', 'red')
def ann_mask(bgr):
    h = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV); H_, S_, V_ = h[..., 0].astype(int), h[..., 1].astype(int), h[..., 2].astype(int)
    rng = dict(red=lambda: (H_ <= 6) | (H_ >= 172), green=lambda: (H_ >= 45) & (H_ <= 80), blue=lambda: (H_ >= 100) & (H_ <= 130), magenta=lambda: (H_ >= 140) & (H_ <= 165),
               yellow=lambda: (H_ >= 28) & (H_ <= 34), white=lambda: np.zeros_like(H_, bool))[ann]()
    m = rng & (S_ > 150) & (V_ > 140) if ann != 'white' else (S_ < 25) & (V_ > 245)
    return m
def circles(m):
    m = cv2.dilate(m.astype(np.uint8) * 255, np.ones((9, 9), np.uint8)); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); res = []
    for c in cs:
        if cv2.contourArea(c) < 150: continue
        (x, y), r = cv2.minEnclosingCircle(c); res.append((x, y, r))
    return res
am = ann_mask(shot); cir = circles(am); print('annotation circles found:', len(cir))
clean = cv2.inpaint(shot, cv2.dilate(am.astype(np.uint8) * 255, np.ones((7, 7), np.uint8)), 5, cv2.INPAINT_TELEA)
g = cv2.cvtColor(clean, cv2.COLOR_BGR2GRAY)
d = load(); H = d['H']; gy, gx = np.gradient(H * 40); nn = np.dstack([-gx, -gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
lam = lambda L: (lambda a: a / a.max())(np.clip(nn @ (np.array(L, float) / np.linalg.norm(L)), 0, 1))
sp = np.clip(nn[..., 2], 0, 1) ** 40; rend = {'spec': np.clip(sp * .9 + lam((-1, -1, 1.2)) * .25, 0, 1)}
# lighting-independent edge density: map side = union of Canny edges over several lights (any relief edge), query side = Canny of the screenshot (subset). Blurred so a few px of shading shift do not matter.
def edges(a8, lo=30, hi=90): return cv2.Canny(cv2.createCLAHE(2, (8, 8)).apply(cv2.GaussianBlur(a8, (0, 0), 1.2)), lo, hi)
u8 = lambda a: (np.clip(a, 0, 1) * 255).astype(np.uint8)
Em = np.zeros((TH, TW), np.uint8)
for L in ((-1, -1, 1.2), (1, -1, 1.2), (-1, 1, 1.2), (1, 1, 1.2), (0, 0, 1)): Em |= edges(u8(lam(L)))
SG = float(os.environ.get('SG', 3)); dens = lambda e: cv2.GaussianBlur(e.astype(np.float32) / 255, (0, 0), SG)
PAD = 80; Dm = dens(Em); Dm3 = cv2.copyMakeBorder(np.hstack([Dm, Dm, Dm]), PAD, PAD, 0, 0, cv2.BORDER_CONSTANT, value=0)
# band region in the screenshot: bright part (V above Otsu of the non-black), largest component; edges near its border are dropped (quad border is not a relief edge)
v = cv2.GaussianBlur(g, (0, 0), 2); thr, _ = cv2.threshold(v[v > 12].reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU); reg = (v > max(12, thr * .35)).astype(np.uint8)
nl, lb, st, _ = cv2.connectedComponentsWithStats(reg); reg = (lb == (1 + np.argmax(st[1:, 4]))).astype(np.uint8) if nl > 1 else reg
reg = cv2.morphologyEx(reg, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)); regin = cv2.erode(reg, np.ones((31, 31), np.uint8))
Eq = edges(g) * regin; Dq = dens(Eq)
bx = cv2.boundingRect(regin); print('band region in screenshot: %dx%d' % (bx[2], bx[3]))
import time; t0 = time.time(); K = .25; cands = []; bxx, byy, bww, bhh = bx; Dqc = Dq[byy:byy + bhh, bxx:bxx + bww]
Dm3s = cv2.resize(Dm3, None, fx=K, fy=K, interpolation=cv2.INTER_AREA); PADs = PAD * K
for f in np.geomspace(.5, 4.0, 30):            # query -> map-pixel scale
    qs = cv2.resize(Dqc, None, fx=f * K, fy=f * K, interpolation=cv2.INTER_AREA)
    if qs.shape[0] < 12 or qs.shape[0] > Dm3s.shape[0] or qs.shape[1] > Dm3s.shape[1]: continue
    for ang in range(-10, 11, 2):
        M0 = cv2.getRotationMatrix2D((qs.shape[1] / 2, qs.shape[0] / 2), ang, 1.0); nw = int(qs.shape[1] * abs(M0[0, 0]) + qs.shape[0] * abs(M0[0, 1])); nh = int(qs.shape[1] * abs(M0[1, 0]) + qs.shape[0] * abs(M0[1, 1]))
        M0[0, 2] += nw / 2 - qs.shape[1] / 2; M0[1, 2] += nh / 2 - qs.shape[0] / 2
        if nh > Dm3s.shape[0] or nw > Dm3s.shape[1]: continue
        qr = cv2.warpAffine(qs, M0, (nw, nh)); res = cv2.matchTemplate(Dm3s, qr, cv2.TM_CCOEFF_NORMED); _, mx, _, loc = cv2.minMaxLoc(res); cands.append((mx, f, ang, (loc[0] / K, loc[1] / K), M0))
cands.sort(key=lambda c: -c[0]); top = []
for c in cands:
    if all(abs(np.log(c[1] / t[1])) > .08 or abs(c[2] - t[2]) > 2 or abs(c[3][0] - t[3][0]) > 40 for t in top): top.append(c)
    if len(top) == 20: break
print('coarse top (%.1fs): ' % (time.time() - t0) + ', '.join('%.3f(f%.2f r%d)' % (c[0], c[1], c[2]) for c in top[:5]))
KE = .5; Sa = np.diag([KE, KE, 1.]); Sb = np.diag([KE, KE, 1.])
Dm3n = cv2.resize(np.hstack([Dm, Dm, Dm]).astype(np.float32), None, fx=KE, fy=KE, interpolation=cv2.INTER_AREA); Dqs = cv2.resize(cv2.GaussianBlur(Dq, (0, 0), 1.5).astype(np.float32), None, fx=KE, fy=KE, interpolation=cv2.INTER_AREA); best = None
for ti, (sc, f, ang, loc, M0) in enumerate(top):
    if ti >= 5 and best is not None and best[0] >= .33: break
    # M0 and f were found at scale K: lift the affine to full tile scale (translation term is in K-scaled px of the rotated crop)
    S3 = np.diag([f, f, 1.]); M3 = np.vstack([M0, [0, 0, 1]]); M3[0, 2] /= K; M3[1, 2] /= K
    T3 = np.array([[1, 0, loc[0]], [0, 1, loc[1] - PAD], [0, 0, 1.]]); W0 = T3 @ M3 @ S3 @ np.array([[1, 0, -bxx], [0, 1, -byy], [0, 0, 1.]])
    Wh = Sb @ W0 @ np.linalg.inv(Sa); cc = -1; Wr = Wh
    try: cc, Wr = cv2.findTransformECC(Dqs, Dm3n, Wh.astype(np.float32), cv2.MOTION_HOMOGRAPHY, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 120, 1e-5), None, 5)
    except cv2.error: pass
    Wf = np.linalg.inv(Sb) @ Wr.astype(np.float64) @ Sa
    if best is None or cc > best[0]: best = (cc, sc, Wf, f, ang)
cc, sc, Hg, f, ang = best; print('chosen: ECC correlation %.3f (coarse %.3f, scale %.2f, rot %d)  total %.1fs' % (cc, sc, f, ang, time.time() - t0))
ok = cc >= .33; print('match quality %.3f%s' % (cc, '' if ok else '  (LOW: do not trust the numbers; send a flatter, closer screenshot)'))
R = d['R']; yy, xx = np.mgrid[:TH, :TW]; lab, n = __import__('scipy.ndimage', fromlist=['x']).label(R); ar = np.bincount(lab.ravel())
ov = cv2.cvtColor((np.clip(np.hstack([rend['spec']] * 2), 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR); rows = []
def pm(Hh_, x, y): q = Hh_ @ np.array([x, y, 1.]); return q[:2] / q[2]
for i, (x, y, r) in enumerate(cir, 1):
    mode = 'global'; Hl = Hg
    cx, cy = pm(Hl, x, y); ex = pm(Hl, x + r, y); mr = float(np.hypot(*(ex - [cx, cy]))); mx = cx % TW; yi = int(np.clip(cy, 0, TH - 1)); xi = int(mx)
    c = lab[yi, xi]; cls = 'ground'
    if c: cls = 'flower' if np.hypot(xi - 820, yi - 233.7) < 340 else ('bead' if ar[c] < 9000 else 'scroll')
    elif np.hypot(xi - 820, yi - 233.7) < 340: cls = 'ground/flower-disc'
    rows.append(dict(n=i, x=round(float(mx), 1), y=round(float(cy), 1), r=round(mr, 1), mode=mode, on=cls, seam=bool(abs(mx - 0) < mr or abs(mx - TW) < mr)))
    cv2.circle(ov, (int(cx), int(cy)), int(max(mr, 6)), (0, 0, 255), 2); cv2.putText(ov, str(i), (int(cx) + 4, int(cy) - 6), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 255), 2)
    print('spot %d: map (%.0f,%.0f) r %.0f  on %s  [%s]  ->  WIN=%d,%d,%d Z=4 python3 tools/v2/zoom.py' % (i, mx, cy, mr, cls, mode, round(mx), round(cy), max(60, int(mr * 1.8))))
cv2.imwrite(out, ov); print('overlay', out)
if os.environ.get('JSON'): json.dump(rows, open(os.environ['JSON'], 'w'))
