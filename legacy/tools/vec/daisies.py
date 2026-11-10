#!/usr/bin/env python3
"""D82 (S-1): proper 8-petal daisies for the band map.
The ref has two full side daisies (~13% / 87% of the band) and a full flower at the seam; the vector map had none at the sides
and a mirrored partial edge flower at the seam (jagged bow petals). This post-step stamps broad, rounded, near-touching petals
(hairline gaps), a round centre bead and a mesh-ready bevel; wrap-aware in x.
usage: python3 tools/vec/daisies.py IN.png OUT.png   (run AFTER build_map.py, BEFORE add_berries.py)
env DAISY 'x,y,L;x,y,L;..' (default '0,258,195' = seam daisy only), DELETE 'x,y,L;..' (default '236,258,190;2162,258,190': old flower cleared, nothing stamped; D90), N 8, RB 34 (bead radius), GAP 2.4, BW 12 (bevel), WMAX 42,
    SEAMCLEAR 215 (seam: clear old flower inside this radius, sloped 12 px), MOAT 4
"""
import os, sys
import numpy as np
import scipy.ndimage as ndi
from PIL import Image

E = lambda k, d: float(os.environ.get(k, d))
N = int(E('N', 8)); RB = E('RB', 34); GAP = E('GAP', 2.4); BW = E('BW', 12); WMAX = E('WMAX', 42); MOAT = E('MOAT', 4); DVO = E('DVO', 9); DVHW = E('DVHW', 1.3); DVD = E('DVD', .07); DVR = E('DVR', .03)
SEAMCLEAR = E('SEAMCLEAR', 215); SS = 3; SEAMFAR = E('SEAMFAR', 360); SEAMAREA = E('SEAMAREA', 12000); SLA = E('SLA', 2500); SLC = E('SLC', .35)
DAISY = [tuple(float(v) for v in s.split(',')) for s in os.environ.get('DAISY', '0,258,195').split(';')]
# DELETE: places where the old flower is cleared (small comps within L+25) but NO daisy is stamped (D90: side daisies removed)
# D91: blunt leaf tails next to the seam daisy: polygon (map x,y; left end) cut out of the big stem comp, mirrored x->w-x for the right end;
# stem side of the cut slopes up over CUTSL px (only for x>=CUTX; the hook top edge left of that stays crisp)
CUT = [[(100, 270), (466, 270), (466, 400), (450, 418), (430, 432), (400, 441), (100, 441)]] if os.environ.get('CUT', '1') == '1' else []
CUTSL = E('CUTSL', 14); CUTX = E('CUTX', 400)
# D92: beads fused to a leaf: (x,y,R) = old blob centre/size (left end, mirrored x->w-x). Everything within R+DETG is replaced by a clean
# hemisphere bead (peak DETH, like the other berries) with a ground moat DETG px wide around it (ramps back to the leaf over 6 px)
DETACH = [(356, 72, 52)] if os.environ.get('DETACH', '1') == '1' else []
DETG = E('DETG', 10); DETH = E('DETH', .75)
DELAREA = E('DELAREA', 30000)   # D90: bigger cutoff in delete mode so the old wing (~16.6k px) goes too
DELETE = [tuple(float(v) for v in s.split(',')) for s in os.environ.get('DELETE', '236,258,190;2162,258,190').split(';') if s]


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def stamp(A, cx, cy, L):
    """A: float height map (h,w) with the centre at column cx (int). Returns modified copy."""
    h, w = A.shape
    R = int(L + 40)
    y0, y1 = max(0, int(cy) - R), min(h, int(cy) + R + 1)
    x0, x1 = cx - R, cx + R + 1
    ys = (np.arange(y0 * SS, y1 * SS) + .5) / SS - .5
    xs = (np.arange(x0 * SS, x1 * SS) + .5) / SS - .5
    dx, dy = xs[None, :] - cx, ys[:, None] - cy
    r = np.hypot(dx, dy)
    U0 = RB + 2
    foot = np.zeros(r.shape, bool); q = np.zeros(r.shape); rib = np.zeros(r.shape); hair = np.zeros(r.shape)
    for k in range(N):
        a = np.pi * 2 * k / N + np.pi / 2          # petal at top first; symmetric for N=8 about both axes
        u = dx * np.cos(a) + dy * np.sin(a); t = -dx * np.sin(a) + dy * np.cos(a)
        s = (u - U0) / (L - U0)
        c = .55
        z = (s - c) / np.where(s < c, c, 1 - c)
        e = np.sqrt(np.clip(1 - z ** 2, 0, 1))
        hw = WMAX * np.where(s < c, .35 + .65 * e, e)        # elliptical rounded tip (no kite point)
        hwlim = (u * np.sin(np.pi / N) - GAP / 2) / np.cos(np.pi / N)
        aa = .3; hw = -np.log(np.exp(-aa * hw) + np.exp(-aa * np.maximum(hwlim, -50))) / aa
        m = (s > 0) & (s < 1) & (np.abs(t) < hw)
        foot |= m
        tp = np.sin(np.pi * np.clip((s - .10) / .78, 0, 1)) ** 1.3 * (s > .12) * (s < .88)       # D86: rib + 2 hairlines per petal, tapered along the axis
        rib = np.where(m, np.maximum(rib, np.exp(-(t / DVO) ** 2) * tp), rib)
        hair = np.where(m, np.maximum(hair, np.exp(-((np.abs(t) - DVO) / DVHW) ** 2) * tp), hair)
        q = np.where(m, np.abs(t) / np.maximum(hw, 1e-3), q)
    bead = r < RB
    d_in = ndi.distance_transform_edt(foot) / SS                       # px (map units) to petal edge
    lvl = .70 + .10 * (1 - q ** 2)
    tb = np.clip(d_in / BW, 0, 1); rb = np.sqrt(1 - (1 - tb) ** 2)     # quarter-round wall
    hp = np.where(foot, lvl * rb * (1 - DVD * hair) + DVR * rib * (1 - hair), 0.0)
    hb = np.where(bead, .80 + .15 * np.sqrt(np.clip(1 - (r / RB) ** 2, 0, 1)), 0.0)
    new = np.maximum(hp, hb)
    clr = ndi.distance_transform_edt(~(foot | (r < RB + 2))) / SS < MOAT
    # downsample to map pixels (area mean)
    def ds(z): return z.reshape(z.shape[0] // SS, SS, z.shape[1] // SS, SS).mean((1, 3))
    new_d, clr_d = ds(new), ds(clr.astype(float))
    sub = A[y0:y1, x0:x1].copy()
    out = np.where(clr_d > .5, new_d, sub)
    A = A.copy(); A[y0:y1, x0:x1] = out
    return A


def remove_small(A, cx, cy, rad, amax=12000):
    lab, n = ndi.label(A > .05)
    yy, xx = np.mgrid[0:A.shape[0], 0:A.shape[1]]
    for i in range(1, n + 1):
        m = lab == i; area = m.sum()
        if area < amax:
            c = ndi.center_of_mass(m)
            if np.hypot(c[1] - cx, c[0] - cy) < rad:
                A[ndi.binary_dilation(m, iterations=6)] = 0
    return A


def remove_far(A, stamped, cx, cy, rout):
    # old-flower leftovers: small comps within rout of the seam centre that contain NO stamped (new daisy) pixel
    lab, n = ndi.label(A > .05)
    yy, xx = np.mgrid[0:A.shape[0], 0:A.shape[1]]
    rr = np.hypot(xx - cx, yy - cy)
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() < SEAMAREA and rr[m].min() < rout and not stamped[m].any():
            A[ndi.binary_dilation(m, iterations=6)] = 0
    return A


def remove_slivers(H):
    """thin leftover slivers (old wing edges cut by the daisy moat) + stray 1-px specks next to the daisies"""
    import cv2
    h, w = H.shape; sh = w // 2
    R = np.roll(H, sh, axis=1)
    lab, n = ndi.label(R > .02)
    yy, xx = np.mgrid[0:h, 0:w]
    near = np.zeros(R.shape, bool)
    for (x, y, L) in DAISY + DELETE:
        cx = (int(round(x)) + sh) % w
        dxw = np.minimum(np.abs(xx - cx), w - np.abs(xx - cx))
        near |= np.hypot(dxw, yy - y) < L + 140
    cnt = 0
    for i in range(1, n + 1):
        mk = lab == i; A = int(mk.sum())
        if A > SLA or not near[mk].any(): continue
        if A < 12: circ = 0
        else:
            c, _ = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            P = cv2.arcLength(c[0], True); circ = 4 * np.pi * A / max(P, 1) ** 2
        if circ < SLC:
            R[ndi.binary_dilation(mk, iterations=4)] = 0; cnt += 1
    print('slivers removed', cnt)
    return np.roll(R, -sh, axis=1)


def cut_leaves(H):
    import cv2
    h, w = H.shape
    lab, n = ndi.label(H > .05)
    big = np.zeros(H.shape, bool)
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() > 60000: big |= m
    yy, xx = np.mgrid[0:h, 0:w]
    for poly in CUT:
        for mir in (0, 1):
            P = np.array([((w - x) if mir else x, y) for x, y in poly], np.int32)
            pm = np.zeros(H.shape, np.uint8); cv2.fillPoly(pm, [P], 1); pm = pm.astype(bool)
            kill = pm & big
            ux = (w - xx) if mir else xx
            dist = ndi.distance_transform_edt(~kill)
            near = big & ~kill & (dist < CUTSL) & (ux >= CUTX)      # stem side slopes up from the cut
            H = np.where(kill, 0, H)
            H = np.where(near, H * sstep(0, CUTSL, dist), H)
    return H


def detach_beads(H):
    h, w = H.shape
    yy, xx = np.mgrid[0:h, 0:w]
    for (x, y, R) in DETACH:
        for cx in (x, w - x):
            d = np.hypot(xx - cx, yy - y)
            H = np.where(d < R + DETG + 6, H * sstep(R + DETG, R + DETG + 6, d), H)    # clear blob + neck, moat ramps out
            H = np.where(d <= R, DETH * np.sqrt(np.clip(1 - (d / R) ** 2, 0, 1)), H)   # clean dome
    return H


def main(src, dst):
    H = np.array(Image.open(src)).astype(np.float64) / 65535.0
    h, w = H.shape; H_in = H.copy()
    for (x, y, L) in DAISY:
        sh = w // 2 - int(round(x))
        A = np.roll(H, sh, axis=1); cx = w // 2
        yy, xx = np.mgrid[0:h, 0:w]
        if x == 0 or x >= w - 1:                      # seam flower: clear the mirrored partial flower, sloped edge
            rr = np.hypot(xx - cx, yy - y)
            A = A * sstep(SEAMCLEAR - 12, SEAMCLEAR, rr)
        else:
            A = remove_small(A, cx, y, L + 25)
        A = stamp(A, cx, y, L)
        if x == 0 or x >= w - 1: A = remove_far(A, (A - np.roll(H_in, sh, axis=1)) > .02, cx, y, SEAMFAR)
        H = np.roll(A, -sh, axis=1)
    stamped = (H - H_in) > .02                       # new daisy px: never delete comps that contain them
    for (x, y, L) in DELETE:                         # after the seam clear: the old wing is cut off from the stem there
        sh = w // 2 - int(round(x))
        A = np.roll(H, sh, axis=1); P = np.roll(stamped, sh, axis=1)
        lab, n = ndi.label(A > .05)
        for i in range(1, n + 1):
            m = lab == i
            if m.sum() < DELAREA and not P[m].any():
                c = ndi.center_of_mass(m)
                if np.hypot(c[1] - w // 2, c[0] - y) < L + 25: A[ndi.binary_dilation(m, iterations=6)] = 0
        H = np.roll(A, -sh, axis=1)
    H = cut_leaves(H)
    H = detach_beads(H)
    H = remove_slivers(H)
    Image.fromarray(np.clip(np.round(H * 65535), 0, 65535).astype(np.uint16)).save(dst)
    print('daisies', DAISY, 'changed px', int((np.abs(H - np.array(Image.open(src)).astype(float) / 65535) > .02).sum()))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
