"""Shared loader for v2 tools: ref tile (rc, BGR float), ref-gold mask R, map height H, map footprint M, hillshade HS, all in map space 1640x520.
Same cut as diff_v2.py / make_map_v2.py (ref rows 215..472, cols 70..2115, tile cols C0..C0+814, 40 px seam cross-fade)."""
import os, cv2, numpy as np
from scipy import ndimage as ndi
TW, TH, P, C0, SEAM = 1640, 520, 814, 608, 40
def load(mp='maps/v2/band_period_v2.png', T=.03, HI=150, LO=85, GROW=6):
    ref = cv2.imread('reference/band_face.png')[215:473, 70:2116]
    V = cv2.GaussianBlur(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
    seed = ndi.binary_opening(V > HI, np.ones((3, 3))); cand = V > LO; g = seed.copy()
    for _ in range(GROW): g = ndi.binary_dilation(g, np.ones((3, 3))) & cand | seed
    g = ndi.binary_opening(g, np.ones((3, 3)))
    lab, n = ndi.label(g); ar = np.bincount(lab.ravel(), minlength=n + 1); g = np.isin(lab, [i for i in range(1, n + 1) if ar[i] >= 150])
    hl, hn = ndi.label(~g); ha = np.bincount(hl.ravel(), minlength=hn + 1); g |= np.isin(hl, [i for i in range(1, hn + 1) if ha[i] < 150])
    def periodic(a):
        e = a[:, C0:C0 + P + SEAM].copy(); t = e[:, :P].copy(); al = (np.arange(SEAM) / SEAM)[None, :]
        if a.ndim == 3: al = al[..., None]
        t[:, :SEAM] = (1 - al) * e[:, P:P + SEAM] + al * e[:, :SEAM]; return t
    rs = lambda a: cv2.resize(a, (TW, TH), interpolation=cv2.INTER_CUBIC)
    R = rs(periodic(g.astype(np.float32))) > .5
    rc = rs(periodic(ref.astype(np.float32)))
    H = cv2.imread(mp, -1).astype(np.float32) / 65535
    hp = mp.replace('.png', '_hillshade.png')
    HS = cv2.imread(hp, 0) if os.path.exists(hp) else None
    return dict(rc=rc, R=R, H=H, M=H > T, HS=HS)
def regions():
    """region masks in map space: flower disc (r<340 at 820,233.7), beads (round ~r<=45 blobs by name list in zoom), else scroll/outside."""
    yy, xx = np.mgrid[:TH, :TW]; fl = np.hypot(xx - 820, yy - 233.7) < 340
    return dict(flower=fl, outside=~fl, all=np.ones((TH, TW), bool))
