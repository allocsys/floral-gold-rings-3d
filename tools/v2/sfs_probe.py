"""T6 shape-from-shading viability probe (no map change). usage: python3 tools/v2/sfs_probe.py [out.png]
1 SANITY: directional-derivative correlation on a KNOWN Lambertian render of the map (must be ~.95, proves the measurement works).
2 REAL: same measurement on the reference's gold luminance (rim 1-6 px inside the footprint, rim 1-12, interior >12 px) and best azimuth.
3 REGRESSION: held-out R^2 of ref luminance from 12 local geometry features of the map (slopes, |grad|, height, Laplacian, 2nd derivs, products, distance to edge).
Last run (s103): sanity .950; real rim best az 120 corr .124 (interior .041); held-out R^2 rim .238 / interior .155 / all gold .178 => the reference's gold shading is NOT a (Lambertian) function of
the map's geometry, so single-image shape-from-shading / luminance inversion cannot give a trustworthy interior height target. Pretrained photo depth nets: HF + PyTorch CPU index blocked here, MiDaS weights reachable on github but torch is ~900 MB and the domain (chrome-like gold illustration) is a poor fit: not attempted.
Figure: ref V | prediction from map geometry (fit on all gold) | |residual| = ref shading structure the map's geometry does not explain (candidate missing detail OR specular/environment shading: cannot tell which)."""
import os, sys, cv2, numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__)); from common import *
out = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/sfs_probe.png'
d = load(); H, M = d['H'], d['M']; g8 = lambda a: cv2.cvtColor(np.clip(a, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
rv = cv2.GaussianBlur(g8(d['rc']), (0, 0), 1.5); Hs = cv2.GaussianBlur(H, (0, 0), 1.5); gy, gx = np.gradient(Hs); dist = ndi.distance_transform_edt(M)
def cc(a, b, w): a, b = a[w], b[w]; a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-9))
gy0, gx0 = np.gradient(H * 40); nn = np.dstack([-gx0, -gy0, np.ones_like(gx0)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
L = np.array([-1, -1, 1.2]); L /= np.linalg.norm(L); lamb = cv2.GaussianBlur(np.clip(nn @ L, 0, 1), (0, 0), 1.5)
dirs = lambda im, w: max(((az, cc(im, gx * np.cos(np.deg2rad(az)) + gy * np.sin(np.deg2rad(az)), w)) for az in range(0, 360, 15)), key=lambda t: abs(t[1]))
rim6, rim12, inter = (dist >= 1) & (dist <= 6), (dist >= 1) & (dist <= 12), dist > 12
print('SANITY known Lambertian: rim best az %d corr %+.3f' % dirs(lamb, rim6))
for n, w in (('rim 1-6px', rim6), ('rim 1-12px', rim12), ('interior >12px', inter)): print('REAL %-15s best az %d corr %+.3f' % ((n,) + dirs(rv, w)))
gyy, gyx = np.gradient(gy); gxy, gxx = np.gradient(gx)
F = lambda w: np.stack([gx[w], gy[w], np.hypot(gx, gy)[w], Hs[w], (gxx + gyy)[w], gxx[w], gyy[w], gxy[w], gx[w] ** 2, gy[w] ** 2, gx[w] * gy[w], dist[w]], 1)
for n, w in (('rim 1-6px', rim6), ('interior >12px', inter), ('all gold', M & (dist >= 1))):
    X = F(w); X = (X - X.mean(0)) / (X.std(0) + 1e-9); X = np.c_[X, np.ones(len(X))]; y = (rv[w] - rv[w].mean()) / rv[w].std(); idx = np.random.default_rng(0).permutation(len(y)); tr, te = idx[:len(y) // 2], idx[len(y) // 2:]
    wt = np.linalg.lstsq(X[tr], y[tr], rcond=None)[0]; p = X[te] @ wt; print('REGR %-15s n %6d held-out R^2 %.3f' % (n, len(y), 1 - ((y[te] - p) ** 2).sum() / ((y[te] - y[te].mean()) ** 2).sum()))
w = M & (dist >= 1); X = F(w); mu, sd = X.mean(0), X.std(0) + 1e-9; X = np.c_[(X - mu) / sd, np.ones(len(X))]; yv = rv[w]; ym, ys = yv.mean(), yv.std(); wt = np.linalg.lstsq(X, (yv - ym) / ys, rcond=None)[0]
pred = np.zeros_like(rv); pred[w] = (X @ wt) * ys + ym; res = np.zeros_like(rv); res[w] = np.abs(rv[w] - pred[w])
t = lambda a, n: cv2.putText(cv2.cvtColor(np.clip(a, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR), n, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2)
sheet = np.vstack([t(rv * M, 'ref V (gold footprint)'), t(pred, 'predicted from map geometry'), t(np.clip(res * 2.5, 0, 255), '|residual| x2.5 (ref structure NOT explained)')])
cv2.imwrite(out, cv2.resize(sheet, None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA)); print('wrote', out)
