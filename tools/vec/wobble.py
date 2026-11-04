"""Outline waviness metric: iso-contour (level .3) of a 16-bit band map, 4x cubic upsample, resampled at 0.5 map px, coords smoothed sigma 1 px.
Reports inflections (curvature sign changes) per 100 map px of contour and sharp corners (turn >60 deg within 4 px) -> lower inflections = calmer outline, corners ~ constant = tips kept.
usage: python3 tools/vec/wobble.py MAP.png [...]"""
import sys, cv2, numpy as np
from scipy import ndimage as ndi
for p in sys.argv[1:]:
    H = cv2.imread(p, -1).astype(np.float32) / 65535
    H = np.pad(H, ((8, 8), (0, 0)), mode='edge')
    B = cv2.resize(ndi.gaussian_filter(H, .6), None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    cs, _ = cv2.findContours((B > .3).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    infl = L = corners = 0
    for c in cs:
        c = c[:, 0, :].astype(float) / 4
        if len(c) < 80 or c[:, 1].min() < 3 or c[:, 1].max() > 523: continue   # skip tiny specks and strip-edge contours
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
        n = int(d[-1] / .5)
        if n < 40: continue
        t = np.linspace(0, d[-1], n, endpoint=False)
        x = np.interp(t, d, c[:, 0]); y = np.interp(t, d, c[:, 1])
        xs = ndi.gaussian_filter1d(x, 2, mode='wrap'); ys = ndi.gaussian_filter1d(y, 2, mode='wrap')   # sigma 2 samples = 1 px
        dx, dy = np.gradient(xs), np.gradient(ys); ddx, ddy = np.gradient(dx), np.gradient(dy)
        k = dx * ddy - dy * ddx
        k = ndi.gaussian_filter1d(k, 1.5, mode='wrap'); sg = np.sign(k[np.abs(k) > 1e-3])
        infl += int((np.diff(sg) != 0).sum()); L += d[-1]
        a = np.arctan2(dy, dx); da = np.abs(np.angle(np.exp(1j * (np.roll(a, -4) - np.roll(a, 4))))); corners += int((da > 1.05).sum() > 0) * int(((da > 1.05) & (np.r_[0, da[:-1]] <= 1.05)).sum())
    print('%-28s contour %6.0f px  inflections/100px %.2f  corners %d' % (p.split('/')[-1], L, 100 * infl / max(L, 1), corners))
