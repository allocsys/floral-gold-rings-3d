"""Outline roughness metric robust to near-straight segments: total variation of curvature per 100 px of contour, with tips excluded (|k|>KT clipped).
Lower = calmer outline. usage: python3 tools/vec/curvtv.py MAP.png [...]"""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
MINL = float(os.environ.get('MINL', 0))
for p in sys.argv[1:]:
    H = cv2.imread(p, -1).astype(np.float32) / 65535; H = np.pad(H, ((8, 8), (0, 0)), mode='edge')
    B = cv2.resize(ndi.gaussian_filter(H, .6), None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    cs, _ = cv2.findContours((B > .3).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE); tv = L = 0
    for c in cs:
        c = c[:, 0, :].astype(float) / 4
        if len(c) < 80 or c[:, 1].min() < 3 or c[:, 1].max() > 523: continue
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]; n = int(d[-1] / .5)
        if n < 40 or (MINL and d[-1] < MINL): continue
        t = np.linspace(0, d[-1], n, endpoint=False); x = np.interp(t, d, c[:, 0]); y = np.interp(t, d, c[:, 1])
        xs = ndi.gaussian_filter1d(x, 3, mode='wrap'); ys = ndi.gaussian_filter1d(y, 3, mode='wrap')
        dx, dy = np.gradient(xs), np.gradient(ys); k = (dx * np.gradient(dy) - dy * np.gradient(dx)) / 0.125 ** 0 / np.maximum(np.hypot(dx, dy), 1e-6) ** 3 / 1.0
        k = np.clip(k * 1.0, -.25 * .25, .25 * .25) if False else np.clip(k, -.5, .5)
        tv += np.abs(np.diff(k, append=k[:1])).sum(); L += d[-1]
    print('%-20s curvature TV per 100px %.3f' % (p.split('/')[-1], 100 * tv / max(L, 1)))
