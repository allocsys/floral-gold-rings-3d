"""Cushion-slope metric: is the map's cushion (slope field + edge-to-crown profile) consistent with the reference shading?
usage: CROPX=7 python3 tools/wip_v3/cdiff.py [map.png] [outdir]   (needs T2.png in outdir, default /tmp/band_v3_out)
Region = ref gold mask (as diff.py) eroded RIM px. L = Lab-L of ref, H = map; both gaussian-smoothed (SIG=4) so only cushion-scale counts.
Findings that shaped this tool (v56): ref shading is NOT directional (L ~ a + bx*dHx + by*dHy gives R2 ~0.005); it is ~isotropic:
bright flat tops, dark steep shoulders. So the metrics are:
  slope corr   corr(L, -|grad H|) in region and per distance-to-edge band (higher = steep parts of the map are dark in the ref)
  R2(H,|g|)    variance of L explained by linear fit on H and |grad H|
  profile      width-normalised crown profile: u = d / local max of d (d = px inside ref gold); per local half-width class,
               mean L and mean H vs u (each rescaled 0..1 over u=.2..8); reports RMSE and signed lead (H - L; >0 = map rises earlier than ref)
Writes cdiff_<map>.png: |grad H| agreement map, green = (L above region mean) matches (|g| below region mean), red = mismatch."""
import sys, os, cv2, numpy as np
mp = sys.argv[1] if len(sys.argv) > 1 else 'maps/band_period.png'
Z = (sys.argv[2] if len(sys.argv) > 2 else '/tmp/band_v3_out').rstrip('/') + '/'
CROPX, S, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
RIM, SIG, R = 8, float(os.environ.get('SIG', 4)), 70
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H = (cv2.imread(mp, -1).astype(np.float32) / 65535)[:520]
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]], np.float32)
g = np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2), [1,3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3,3),np.uint8)), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
el = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1,)*2)
reg = cv2.erode(g, el(RIM)) > 0
L = cv2.cvtColor(cv2.GaussianBlur(ref, (0,0), 1.0), cv2.COLOR_BGR2LAB)[:,:,0].astype(np.float32)
Ls = cv2.GaussianBlur(L, (0,0), SIG); Hs = cv2.GaussianBlur(H, (0,0), SIG)
Hx = cv2.Sobel(Hs, cv2.CV_32F, 1, 0, ksize=3) / 8; Hy = cv2.Sobel(Hs, cv2.CV_32F, 0, 1, ksize=3) / 8
mag = np.hypot(Hx, Hy)
d = cv2.distanceTransform(g, cv2.DIST_L2, 5)
lm = cv2.dilate(d, el(R))   # local max of d = local petal half-width
u = d / np.maximum(lm, 1)
cc = lambda a, b, m: np.corrcoef(a[m], b[m])[0, 1]
print('region %d px | slope corr(L,-|gradH|) %.3f | corr(L,H) %.3f' % (reg.sum(), -cc(Ls, mag, reg), cc(Ls, Hs, reg)))
m = reg; A = np.stack([np.ones(m.sum()), Hs[m], mag[m]], 1); y = Ls[m]; p = A @ np.linalg.lstsq(A, y, rcond=None)[0]
print('R2(L ~ H, |gradH|) %.3f' % (1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()))
print('slope corr by distance-to-edge band: ' + ' | '.join('%d-%d: %.3f' % (lo, hi, -cc(Ls, mag, reg & (d >= lo) & (d < hi))) for lo, hi in [(8, 14), (14, 22), (22, 34), (34, 999)] if (reg & (d >= lo) & (d < hi)).sum() > 200))
nrm = lambda a: (a - np.nanmin(a)) / max(np.nanmax(a) - np.nanmin(a), 1e-6)
ub = np.arange(0.2, 0.81, 0.1)
for lo, hi in [(24, 40), (40, 70)]:
    sel = reg & (lm >= lo) & (lm < hi); pl, ph = [], []
    for b in ub:
        mm = sel & (u >= b) & (u < b + 0.1)
        pl.append(L[mm].mean() if mm.sum() > 100 else np.nan); ph.append(H[mm].mean() if mm.sum() > 100 else np.nan)
    nl, nh = nrm(np.array(pl)), nrm(np.array(ph)); df = nh - nl
    print('profile local halfwidth %d-%d px (%d px), u=.2..0.8: RMSE %.3f | lead %+.3f | L %s | H %s' % (lo, hi, sel.sum(), np.sqrt(np.nanmean(df**2)), np.nanmean(df), np.round(nl, 2), np.round(nh, 2)))
sg = reg & ((Ls > Ls[reg].mean()) == (mag < mag[reg].mean()))
vis = (ref * 0.35).astype(np.uint8); vis[~reg] = (vis[~reg] * 0.5).astype(np.uint8)
vis[sg] = (0, 160, 0); vis[reg & ~sg] = (0, 0, 220)
out = Z + 'cdiff_' + os.path.splitext(os.path.basename(mp))[0] + '.png'
cv2.imwrite(out, cv2.resize(vis, (1198, 260), interpolation=cv2.INTER_AREA)); print('wrote', out)
