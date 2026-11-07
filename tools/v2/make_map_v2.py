"""v2 step 3: ONE-period height map (1640x520, 16-bit, x wraps) of the NEW reference, from maps/v2/panel_mask.png (+ the ref colour for hairline grooves).
Tile = 814 ref cols centred on flower 2 (ref bead (1085,331) = panel col 1015, row 116); seam made exactly periodic by a 40 px cross-fade with the next period.
Scale 2.0155 map px per ref px (258 -> 520 rows, 814 -> 1640 cols, isotropic). Heights follow the old map's convention (ground 0, gold plateau ~.58, beads ~.8, flower bead .95, bevel W 10 px).
usage: python3 tools/v2/make_map_v2.py [OUT=maps/v2/band_period_v2.png]    knobs (env): PL .25 W 10 BEAD .8 FBEAD .95 GROOVE 1 GD .12 SIG 2.2
"""
import os, sys, cv2, numpy as np
from scipy import ndimage as ndi
OUT = sys.argv[1] if len(sys.argv) > 1 else 'maps/v2/band_period_v2.png'
E = lambda k, d: float(os.environ.get(k, d))
PL, W, BEAD, FBEAD, GR, GD, SIG = E('PL', .5), E('W', 10), E('BEAD', .8), E('FBEAD', .95), E('GROOVE', 1), E('GD', .12), E('SIG', 2.2)
TW, TH, P, C0, SEAM = 1640, 520, 814, 1015 - 407, 40
mask = cv2.imread('maps/v2/panel_mask.png', 0).astype(np.float32) / 255
ref = cv2.imread('reference/band_face.png')[215:473, 70:2116]
def periodic(a):
    e = a[:, C0:C0 + P + SEAM].copy(); t = e[:, :P].copy()
    al = (np.arange(SEAM) / SEAM)[None, ...] if a.ndim == 2 else None
    t[:, :SEAM] = (1 - al) * e[:, P:P + SEAM] + al * e[:, :SEAM]
    return t
mt = periodic(mask)
V = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32); Vt = periodic(V)
rs = lambda a: cv2.resize(a, (TW, TH), interpolation=cv2.INTER_CUBIC)
sg = lambda a, s: ndi.gaussian_filter(a, s, mode=('nearest', 'wrap'))
def tri(a): return np.tile(a, (1, 3))
def sdf_of(Bm): return (ndi.distance_transform_edt(tri(Bm))[:, TW:2 * TW] - ndi.distance_transform_edt(~tri(Bm))[:, TW:2 * TW]).astype(np.float32)
B = sg(rs(sg(mt, .8)), 1.5) > .5
for ss in (SIG, SIG * .8):                       # D-v2 s73: level-set smoothing = smooth the signed distance, re-threshold at 0 (kills the ref stair-steps, keeps tips)
    B = sg(sdf_of(B), ss) > 0
lab, n = ndi.label(B); ar = np.bincount(lab.ravel(), minlength=n + 1)
B = np.isin(lab, [i for i in range(1, n + 1) if ar[i] >= 150])
hl, hn = ndi.label(~B); ha = np.bincount(hl.ravel(), minlength=hn + 1)
B = B | np.isin(hl, [i for i in range(1, hn + 1) if ha[i] < 150])   # fill small holes
# thin-gap narrowing: background strips < 12 map px wide (petal gaps, slits) are wider than the ref's hairlines -> grow gold GN px into them from both sides
rr = 6; yy_, xx_ = np.mgrid[-rr:rr + 1, -rr:rr + 1]; disc = (yy_ ** 2 + xx_ ** 2) <= rr * rr
opn = ndi.binary_opening(tri(~B), structure=disc)[:, TW:2 * TW]
thin = ~B & ~opn
B = B | (thin & (ndi.distance_transform_edt(~tri(B))[:, TW:2 * TW] <= E('GN', 2.5)))
# D-v2 s74 petal slit fill: the mask subtracted dark ref slits that are really petal ribs (not petal gaps). Inside the flower disc, close B within +-FW deg of each petal axis (gaps lie midway between axes, untouched).
FCX, FCY = 407 * TW / P, 116 * TW / P; FAX = [357, 57, 117, 177, 237, 297]; FW = E('FW', 14)
_a = (np.degrees(np.arctan2(np.mgrid[:TH, :TW][0] - FCY, np.mgrid[:TH, :TW][1] - FCX)) % 360); _r = np.hypot(np.mgrid[:TH, :TW][0] - FCY, np.mgrid[:TH, :TW][1] - FCX)
_ax = np.zeros(B.shape, bool)
for _t in FAX: _ax |= (np.abs((_a - _t + 180) % 360 - 180) <= FW)
_zone = _ax & (_r > 62) & (_r < 330)
_cl = ndi.binary_closing(B, structure=np.ones((3, 3)), iterations=int(E('FCI', 9)))
B = B | (_cl & _zone)
# s75 petal bases: per petal, fill the convex hull of its gold (r > RB) inside its own 60 deg sector (inset GAPH px from the gap lines) -> no slit remnants/slivers; clear the ring r < RB around the bead moat; round the base corners (SDF smoothing r < 130)
RB, GAPH = E('RB', 74), E('GAPH', 1.5)
GW0, GS, RF = E('GW0', 3.5), E('GS', .04), E('RF', 150)
_dB = ndi.distance_transform_edt(~B); _sm = np.clip((_r - E('FR0', 110)) / (E('FR1', 210) - E('FR0', 110)), 0, 1); _e = E('FEXP', 14) * (1 - _sm * _sm * (3 - 2 * _sm))   # fill may grow a petal by <= _e px, fading out with r (no hard step)
_gwr = GW0 + GS * (np.clip(_r, RB, RF) - RB)   # s77 gap half-width (px): narrow at the bead, widening outward (ref gaps are thin dark lines, petal sides straight along them)
for _t in FAX:
    _d = np.abs((_a - _t + 180) % 360 - 180); _sec = (_d <= 30) & (_r > RB) & (_r < 340) & (_r * np.sin(np.radians(np.clip(30 - _d, 0, 90))) >= _gwr)
    _m = (B & _sec).astype(np.uint8); _n, _l, _st, _ = cv2.connectedComponentsWithStats(_m, connectivity=8)
    if _n < 2: continue
    _k = 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA])); _pts = cv2.findNonZero((_l == _k).astype(np.uint8))
    _hm = np.zeros(B.shape, np.uint8); cv2.fillConvexPoly(_hm, cv2.convexHull(_pts), 1)
    B = B | ((_hm > 0) & _sec) | (_sec & (_dB <= _e))   # hull + wedge fill toward the gap lines (distance-limited, fades with r)
B = B & ~((_r < RB) & (_r > 40))
_B2 = sg(sdf_of(B), E('BSG', 2.5)) > 0
B = np.where((_r > 55) & (_r < 130), _B2, B)
_gd = np.min([np.abs((_a - g + 180) % 360 - 180) for g in (27, 87, 147, 207, 267, 327)], axis=0)   # re-cut the 6 radial petal gaps (smoothing can close them)
B = B & ~((_r * np.sin(np.radians(np.clip(_gd, 0, 90))) < _gwr) & (_r > RB) & (_r < E('GR1', 300)))
_l2, _n2 = ndi.label(B); _a2 = np.bincount(_l2.ravel(), minlength=_n2 + 1); B = np.isin(_l2, [i for i in range(1, _n2 + 1) if _a2[i] >= 150])   # drop slivers left by the gap cut
# s79 local corner round: the top-right petal's rim meets its gap line in a tiny hook at map (820,72); SDF-smooth B in a soft window (NCX,NCY,NCR) so only that corner rounds
_nx, _ny = np.meshgrid(np.arange(TW), np.arange(TH)); _nd = np.hypot(_nx - E('NCX', 821), _ny - E('NCY', 72)); _nw = 1 - np.clip((_nd - E('NCR', 14)) / 8, 0, 1)
B = np.where(_nw > .5, sg(sdf_of(B), E('NSG', 3)) > 0, B)
# beads (ring-template matched on the ref, tile px x,y,r, moat?, top): carve moat ring, stamp disc
sc = TW / P; Yg, Xg = np.mgrid[:TH, :TW]
BEADS = [(407, 116, 29, 1, FBEAD), (593, 151, 22, 1, BEAD), (80, 214, 27, 1, BEAD), (530, 33, 10, 1, BEAD), (302, 224, 9, 1, BEAD), (593, 36, 18, 0, BEAD), (228, 145, 21, 0, .78)]
dist_b = np.full(B.shape, 1e9, np.float32)
for bx, by, br, moat, top in BEADS:
    d = np.hypot(Xg - bx * sc, Yg - by * sc); R = br * sc
    if bx == 407 and by == 116:   # s78 flower bead: ref has a gold COLLAR out to r~66 (cut by the 6 petal gap lines), dark moat r 66..73, petals from ~74 (measured radial profile)
        Rc = R + E('COL', 8); B = B & ~((d > Rc) & (d <= Rc + E('FMOAT', 7))); B = B | (d <= Rc)
        _FS = ((_r * np.sin(np.radians(np.clip(_gd, 0, 90))) < E('CGW', 3)) & (d > R) & (d <= Rc)); _FD = np.clip((R + 2.5 - d) / 5, 0, 1)   # s79: slit mask + soft dome weight (1 inside r<=R-2.5, 0 beyond R+2.5)
        B = B & ~_FS
        B = B | (d <= R)
        continue
    if moat: B = B & ~((d > R) & (d <= R + E('MOAT', 8)))
    B = B | (d <= R)
sdf = sg(sdf_of(B), 1.0)
level = np.zeros(B.shape, np.float32); isbead = np.zeros(B.shape, bool)
for bx, by, br, moat, top in BEADS:
    d = np.hypot(Xg - bx * sc, Yg - by * sc); R = br * sc; r_ = d <= R
    if bx == 407 and by == 116:   # flower bead: dome rises from a flat collar (height COLH) out to Rc (already carved by the gap lines / moat in B)
        _Rc = R + E('COL', 8); _col = (d > R) & (d <= _Rc) & B; level[_col] = E('COLH', .5); isbead |= _col
        level[r_] = (E('COLH', .5) + (top - E('COLH', .5)) * np.sqrt(np.clip(1 - (d / R) ** 2, 0, 1)))[r_]; isbead |= r_; continue
    _b0 = .3 if moat else .55   # moat-less balls sit on the leaf: dome starts at plate height, no cliff (s76)
    level[r_] = (_b0 + (top - _b0) * np.sqrt(np.clip(1 - (d / R) ** 2, 0, 1)))[r_]; isbead |= r_
big = B & ~isbead
yy, xx = np.mgrid[-30:31, -30:31]; fp = (yy ** 2 + xx ** 2) <= 900
Rloc = sg(ndi.maximum_filter(tri(np.maximum(sdf, 0)), footprint=fp, mode='nearest')[:, TW:2 * TW], 14)   # tiled x3 so the round footprint wraps
dn = sg(np.clip(sdf / np.maximum(Rloc, 8), 0, 1), 4)
plate = .58 * (1 - PL * (1 - dn) ** 2)
if GR > 0:   # thin dark hairlines inside gold (black-hat of ref luminance); wide dark bands are reflections, not grooves -> thin + elongated comps only
    Vb = cv2.GaussianBlur(Vt, (0, 0), 1.0); bh = cv2.morphologyEx(Vb, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) - Vb
    g = rs(((bh > E('GT', 30))).astype(np.float32)) > .5
    g &= ndi.binary_erosion(B & ~isbead, iterations=14)
    g &= ~(_r < 335)   # flower petals get procedural veins instead (s74)
    gl, gn = ndi.label(g, structure=np.ones((3, 3))); keep = np.zeros_like(g)
    for k, sl in enumerate(ndi.find_objects(gl), 1):
        h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if max(h_, w_) >= 40: keep |= gl == k
    plate = plate * (1 - GD * sg(keep.astype(np.float32), 1.3) / max(sg(keep.astype(np.float32), 1.3).max(), 1e-3))
# D-v2 s74 petal veins: per petal ONE rib + 2 diverging hairlines (clean, evenly tapered), straight along the petal axis; replaces the ref's reflection-dependent dark lines
VR, VH, VW, VO, VS, VE = E('VR', .05), E('VH', .035), E('VW', 1.4), E('VO', 9), E('VS', 80), E('VE', .86)
VG = np.zeros(B.shape, np.float32)
def seg_field(p0, p1, t0, t1, w):
    """gaussian groove around segment p0->p1 with sin-taper along length (t0,t1 = taper fractions)"""
    d = p1 - p0; L = np.hypot(*d); u = d / L
    px, py = Xg - p0[0], Yg - p0[1]; s_ = (px * u[0] + py * u[1]) / L; q = np.abs(px * -u[1] + py * u[0])
    tap = np.clip(np.minimum(s_ / t0, (1 - s_) / t1), 0, 1); tap = np.sin(tap * np.pi / 2) * ((s_ >= 0) & (s_ <= 1))
    return (np.exp(-.5 * (q / w) ** 2) * tap).astype(np.float32)
for t in FAX:
    sel = B & _zone & (np.abs((_a - t + 180) % 360 - 180) <= 5)
    tipR = _r[sel].max() if sel.any() else 250; L1 = VE * (tipR - VS)
    u = np.array([np.cos(np.radians(t)), np.sin(np.radians(t))]); n_ = np.array([-u[1], u[0]]); c = np.array([FCX, FCY])
    VG = np.maximum(VG, VR * seg_field(c + u * VS, c + u * (VS + L1), .12, .35, VW * 1.1))
    for sgn in (-1, 1):   # hairlines start at 0.15 L with offset 2, diverge to +-VO at the end, run to .8 L
        a0 = c + u * (VS + .15 * L1) + n_ * sgn * 2; a1 = c + u * (VS + .8 * L1) + n_ * sgn * VO
        VG = np.maximum(VG, VH * seg_field(a0, a1, .25, .4, VW))
_LUM = E('LUM', .05)
if _LUM > 0:   # s76 faint shape-from-shading: ref luminance (blurred) relative to its local gold mean -> +-LUM height; flower disc excluded (procedural veins)
    _Vl = sg(rs(Vt), E('LSIG', 5)); _w = (B & ~isbead).astype(np.float32)
    _mu = sg(_Vl * _w, 30) / np.maximum(sg(_w, 30), 1e-3)
    plate = plate + _LUM * np.clip((_Vl - _mu) / 60, -1, 1) * np.clip((_r - 300) / 60, 0, 1) * sg(_w, 2)
plate = plate - VG
level = np.where(big, plate, level)
bev = np.clip(sdf / W, 0, 1); bev = bev * bev * (3 - 2 * bev)
# s79 collar slit pockets: the bevel of the flower dome ignores the 6 collar slits (distance to the moat only), so slit ends no longer scoop round pockets out of the dome edge
_sf = sg(sdf_of(B | _FS), 1.0); _bf = np.clip(_sf / W, 0, 1); _bf = _bf * _bf * (3 - 2 * _bf)
bev = _FD * _bf + (1 - _FD) * bev
H = np.clip(level * bev, 0, 1) * np.clip(B + (sdf > -.3), 0, 1)
# s79 collar slit ends: light Gaussian of H in a soft window around the 6 collar slits (r 53..69, within SLW px of the gap line) removes the stair-stepped teeth where the slits meet the dome edge
_slw = E('SLW', 9); _wr = np.clip(np.minimum(_r - (29 * sc - 5), (29 * sc + E('COL', 8) + 2.5) - _r) / 3, 0, 1)
_wa = np.clip((_slw - _r * np.sin(np.radians(np.clip(_gd, 0, 90)))) / 3, 0, 1); _ws = _wr * _wa
H = np.clip(_ws * sg(H, E('SLG', 1.3)) + (1 - _ws) * H, 0, 1)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
cv2.imwrite(OUT, (H * 65535).astype(np.uint16))
m_ = H; gy, gx = np.gradient(m_ * 40); nn = np.dstack([-gx, -gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
hs = np.clip(nn @ np.array([-1, -1, 1.2]) / np.linalg.norm([-1, -1, 1.2]), 0, 1); hs = hs / hs.max()
cv2.imwrite(OUT.replace('.png', '_hillshade.png'), (hs * 255).astype(np.uint8))
print('wrote', OUT, H.shape, 'beads:', len(BEADS), 'coverage %.3f' % B.mean())
