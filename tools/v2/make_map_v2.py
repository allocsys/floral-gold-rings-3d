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
FCX, FCY = 407 * TW / P, 116 * TW / P; # s80: MEASURED petal gap angles in the new ref (valley centroid of ref brightness about the flower centre, r80..180 median; deg, 0=+x, y down): the ref flower is NOT 60-deg regular (spacings 56.9..64). Axes = midpoints of neighbouring gaps, FHW = half sector widths.
FGAP = [31.8, 88.7, 146.8, 210.8, 271.0, 329.3]; FAX = [(FGAP[i] + FGAP[(i + 1) % 6] + (360 if i == 5 else 0)) / 2 % 360 for i in range(6)]; FHW = [((FGAP[(i + 1) % 6] + (360 if i == 5 else 0)) - FGAP[i]) / 2 for i in range(6)]; FW = E('FW', 14)
_a = (np.degrees(np.arctan2(np.mgrid[:TH, :TW][0] - FCY, np.mgrid[:TH, :TW][1] - FCX)) % 360); _r = np.hypot(np.mgrid[:TH, :TW][0] - FCY, np.mgrid[:TH, :TW][1] - FCX)
_ax = np.zeros(B.shape, bool)
for _t in FAX: _ax |= (np.abs((_a - _t + 180) % 360 - 180) <= FW)
_zone = _ax & (_r > 62) & (_r < 330)
_cl = ndi.binary_closing(B, structure=np.ones((3, 3)), iterations=int(E('FCI', 9)))
B = B | (_cl & _zone)
# s75 petal bases: per petal, fill the convex hull of its gold (r > RB) inside its own 60 deg sector (inset GAPH px from the gap lines) -> no slit remnants/slivers; clear the ring r < RB around the bead moat; round the base corners (SDF smoothing r < 130)
RB, GAPH = E('RB', 74), E('GAPH', 1.5)
# s83 per-petal base radius (ref petal bases start nearer the bead at the top: measured V rise r~70 top, ~72 left/right, ~74 lower; the dark ring is thin there). RBP env 'a,b,c,d,e,f' in FAX order; default = RB for all reproduces s82.
RBPL = [float(v) for v in os.environ.get('RBP', '74,74,72,69.5,69.5,72').split(',')]
_pi = np.argmin(np.stack([np.abs((_a - t + 180) % 360 - 180) / h for t, h in zip(FAX, FHW)]), axis=0); _rbp = np.array(RBPL)[_pi]
GW0, GS, RF = E('GW0', 3.5), E('GS', .04), E('RF', 150)
_dB = ndi.distance_transform_edt(~B); _sm = np.clip((_r - E('FR0', 110)) / (E('FR1', 210) - E('FR0', 110)), 0, 1); _e = E('FEXP', 14) * (1 - _sm * _sm * (3 - 2 * _sm))   # fill may grow a petal by <= _e px, fading out with r (no hard step)
_gwr = GW0 + GS * (np.clip(_r, RB, RF) - RB)   # s77 gap half-width (px): narrow at the bead, widening outward (ref gaps are thin dark lines, petal sides straight along them)

# s81 per-gap flare near the bead (lower-petal slivers): extra half-width FLA[i] px at r<=FL0, decaying exp(-(r-FL0)/FLT), gone by FLE0..FLE1 -- ref gaps are wide pockets at the bead (full width 20-38 px at r76-84) that taper to the ~16 px line by r~90
FLA = [float(v) for v in os.environ.get('FLA', '13,13,6,1.5,0,4').split(',')]; FL0, FLT, FLE0, FLE1 = E('FL0', 80), E('FLT', 6), E('FLE0', 98), E('FLE1', 112)
_gdi = np.stack([np.abs((_a - g + 180) % 360 - 180) for g in FGAP]); _gi = np.argmin(_gdi, axis=0)
_fs = np.clip((_r - FLE0) / (FLE1 - FLE0), 0, 1); _fp = np.where(_r <= FL0, 1.0, np.exp(-(_r - FL0) / FLT)) * (1 - _fs * _fs * (3 - 2 * _fs))
_gwr = _gwr + np.array(FLA)[_gi] * _fp * (_r > RB)
for _t, _hw in zip(FAX, FHW):
    _d = np.abs((_a - _t + 180) % 360 - 180); _sec = (_d <= _hw) & (_r > _rbp) & (_r < 340) & (_r * np.sin(np.radians(np.clip(_hw - _d, 0, 90))) >= _gwr)
    _m = (B & _sec).astype(np.uint8); _n, _l, _st, _ = cv2.connectedComponentsWithStats(_m, connectivity=8)
    if _n < 2: continue
    _k = 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA])); _pts = cv2.findNonZero((_l == _k).astype(np.uint8))
    _hm = np.zeros(B.shape, np.uint8); cv2.fillConvexPoly(_hm, cv2.convexHull(_pts), 1)
    B = B | ((_hm > 0) & _sec & (_r < E('HR', 1e9))) | (_sec & (_dB <= _e))   # s85 HR: hull fill only for r<HR (the hull overreaches where the ref petal rim is concave)   # hull + wedge fill toward the gap lines (distance-limited, fades with r)
B = B & ~((_r < _rbp) & (_r > 40))
_B2 = sg(sdf_of(B), E('BSG', 2.5)) > 0
B = np.where((_r > 55) & (_r < 130), _B2, B)
_gd = np.min([np.abs((_a - g + 180) % 360 - 180) for g in FGAP], axis=0)   # re-cut the 6 radial petal gaps (smoothing can close them)
B = B & ~((_r * np.sin(np.radians(np.clip(_gd, 0, 90))) < _gwr) & (_r > _rbp) & (_r < E('GR1', 250)))
# s82 rib slits: the ref's 4 side/lower petals (axes FAX[0,1,2,5]) have a dark rib channel (measured full width px by r, centre offset deg): flare at the bead, ~12-14 px line, pointed end. Cut as tapered slits (SLIT=0 disables). top two petals have none.
SLITS = {0: (-0.4, [(74, 30), (82, 24), (90, 12), (120, 11), (130, 5), (140, 4), (148, 0)]),
         1: (-0.8, [(74, 28), (82, 22), (90, 14), (100, 13), (106, 6), (112, 0)]),
         2: (-1.5, [(74, 16), (90, 14), (110, 14), (120, 12), (130, 10), (142, 10), (152, 0)]),
         5: (0.3, [(74, 16), (90, 12), (130, 12), (142, 10), (152, 10), (162, 0)])}
if E('SLIT', 1):
    for _i, (_off, _pr) in SLITS.items():
        _pr = np.array(_pr, float); _wr = np.interp(_r, _pr[:, 0], _pr[:, 1], right=0) * E('SLW', 1.0)
        _dth = np.abs((_a - (FAX[_i] + _off) + 180) % 360 - 180)
        B = B & ~((_r * np.sin(np.radians(np.clip(_dth, 0, 90))) < _wr / 2) & (_dth < 40) & (_r >= RB - 4))
_l2, _n2 = ndi.label(B); _a2 = np.bincount(_l2.ravel(), minlength=_n2 + 1); B = np.isin(_l2, [i for i in range(1, _n2 + 1) if _a2[i] >= 150])   # drop slivers left by the gap cut
# s79 local corner round: the top-right petal's rim meets its gap line in a tiny hook at map (820,72); SDF-smooth B in a soft window (NCX,NCY,NCR) so only that corner rounds
_nx, _ny = np.meshgrid(np.arange(TW), np.arange(TH)); _nd = np.hypot(_nx - E('NCX', 821), _ny - E('NCY', 72)); _nw = 1 - np.clip((_nd - E('NCR', 14)) / 8, 0, 1)
B = np.where(_nw > .5, sg(sdf_of(B), E('NSG', 3)) > 0, B)
# s84 bay fills: where a dark crease next to a leaf edge was cut out of the mask it opened a bite / left a shaded tail out (diff MISS blobs, x y window radius). Inside these soft windows the map takes the union with the ref's own gold (brightness hysteresis, same detector as diff_v2.py: seeds V>HI 150 grown <=6 px into V>85, opened 3x3, comps/holes <150 dropped), opened 5x5 to drop rim noise. BAY=0 disables.
BAYS = [(146, 74, 34), (1377, 492, 44), (612, 108, 26), (525, 40, 36)]   # s85 + right petal tip (612,108) and scroll top strip (525,40)
if E('BAY', 1):
    _ref = cv2.imread('reference/band_face.png')[215:473, 70:2116]
    _V = cv2.GaussianBlur(cv2.cvtColor(_ref, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
    _sd = ndi.binary_opening(_V > 150, np.ones((3, 3))); _cd = _V > 85; _g = _sd.copy()
    for _ in range(6): _g = ndi.binary_dilation(_g, np.ones((3, 3))) & _cd | _sd
    _g = ndi.binary_opening(_g, np.ones((3, 3))); _l, _n = ndi.label(_g); _ar = np.bincount(_l.ravel(), minlength=_n + 1); _g = np.isin(_l, [i for i in range(1, _n + 1) if _ar[i] >= 150])
    _e = _g[:, C0:C0 + P + SEAM].astype(np.float32).copy(); _t = _e[:, :P].copy(); _al = (np.arange(SEAM) / SEAM)[None, :]
    _t[:, :SEAM] = (1 - _al) * _e[:, P:P + SEAM] + _al * _e[:, :SEAM]
    _Rg = ndi.binary_opening(cv2.resize(_t, (TW, TH), interpolation=cv2.INTER_CUBIC) > .5, np.ones((5, 5)))
    _bx, _by = np.meshgrid(np.arange(TW), np.arange(TH))
    _Dk = ndi.binary_opening(cv2.resize(_t, (TW, TH), interpolation=cv2.INTER_CUBIC) <= .5, np.ones((5, 5)))   # ref NON-gold (dark crease / ground), opened 5x5
    for _cx, _cy, _wr in BAYS:
        B = B | (_Rg & (np.hypot(_bx - _cx, _by - _cy) <= _wr))
    # s85 cuts: window (x, y, radius) where the map has gold but the ref has a dark crease / dark rim band: remove the ref-dark part. 'a' windows above add ref gold.
    CUTS = [(396, 319, 26), (575, 312, 30)]
    for _cx, _cy, _wr in CUTS:
        B = B & ~(_Dk & (np.hypot(_bx - _cx, _by - _cy) <= _wr))
    # s86 ref-shape windows (x, y, radius): inside, the map silhouette becomes the ref's own (ref gold union, minus ref-dark recess), level-set smoothed RSG. REFW=0 disables.
    REFW = [(1495, 395, 75), (438, 258, 16), (396, 319, 34)]   # bottom-right pointed leaf recess; curl-head groove pocket; gap beside the curl
    if E('REFW', 1):
        _ev = _V[:, C0:C0 + P + SEAM].copy(); _tv = _ev[:, :P].copy(); _tv[:, :SEAM] = (1 - _al) * _ev[:, P:P + SEAM] + _al * _ev[:, :SEAM]
        _Dk2 = ndi.binary_opening(cv2.resize(_tv, (TW, TH), interpolation=cv2.INTER_CUBIC) < E('RDT', 60), np.ones((E('RDO', 1).__int__(),) * 2)); _l3, _n3 = ndi.label(_Dk2); _a3 = np.bincount(_l3.ravel(), minlength=_n3 + 1); _Dk2 = np.isin(_l3, [i for i in range(1, _n3 + 1) if _a3[i] >= 60])
        if E('RCL', 9): _Dk2 = ndi.binary_closing(np.pad(_Dk2, 12), np.ones((int(E('RCL', 9)),) * 2))[12:-12, 12:-12] | _Dk2   # s87: close the ref-dark recess (fills notches where a highlight stripe crosses its rim)
        _Bn = (ndi.binary_dilation(B | _Rg, iterations=E('RGR', 4).__int__()) & ~_Dk2) if E('RFILL', 1) else ((B | _Rg) & ~_Dk2); _Bs = sg(sdf_of(_Bn), E('RSG', 1.5)) > 0
        for _cx, _cy, _wr in REFW:
            B = np.where(np.hypot(_bx - _cx, _by - _cy) <= _wr, _Bs, B)
# beads (ring-template matched on the ref, tile px x,y,r, moat?, top): carve moat ring, stamp disc
sc = TW / P; Yg, Xg = np.mgrid[:TH, :TW]
BEADS = [(407, 116, 29, 1, FBEAD), (593, 151, 22, 1, BEAD), (80, 214, 27, 1, BEAD), (530, 33, 10, 1, BEAD), (302, 224, 9, 1, BEAD), (593, 36, 18, 0, BEAD), (228, 145, 21, 0, .78)]
if E('BFIT', 1):   # s85 circles refitted (robust LSQ) to the ref gold outline, edge px with ground outside; only beads with >=33/36 angular bins covered (the (302,224) and curl-ball (228,145) fits were contaminated, kept)
    BEADS[1] = (592.7, 151.9, 22.29, 1, BEAD); BEADS[2] = (81.0, 214.1, 27.2, 1, BEAD); BEADS[3] = (530.9, 34.0, 9.93, 1, BEAD); BEADS[5] = (592.8, 36.4, 18.31, 0, BEAD)
if E('NOCURL', 1): BEADS = [_b for _b in BEADS if _b[0] != 228]   # s86: the curl-head 'ball' (228,145) is the scroll's own rounded end in the ref (no sphere, no circle edge): let the scroll plateau carry it
dist_b = np.full(B.shape, 1e9, np.float32)
for bx, by, br, moat, top in BEADS:
    d = np.hypot(Xg - bx * sc, Yg - by * sc); R = br * sc
    if bx == 407 and by == 116:   # s78 flower bead: ref has a gold COLLAR out to r~66 (cut by the 6 petal gap lines), dark moat r 66..73, petals from ~74 (measured radial profile)
        Rc = R + E('COL', 8); B = B & ~((d > Rc) & (d <= np.minimum(Rc + E('FMOAT', 7), _rbp))); B = B | (d <= Rc)
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
if E('NOCURL', 1) and E('CB', .25) > 0:   # s86: gentle rounded swell on the scroll's curl head (ref head is a lit round end), smooth falloff so no circle edge
    _dc = np.hypot(Xg - 228 * sc, Yg - 145 * sc) / (E('CBR', 1.15) * 21 * sc); plate = plate + E('CB', .25) * (1 - np.clip(_dc, 0, 1) ** 2) ** 2
level = np.where(big, plate, level)
_sb = sg(sdf, E('SBS', 2.0)) if E('SBS', 2.0) > 0 else sdf   # s79 rim faceting: bevel ramp from a smoother SDF (binary-mask staircase made stripes on the rims)
bev = np.clip(_sb / W, 0, 1); bev = bev * bev * (3 - 2 * bev)
# s79 collar slit pockets: the bevel of the flower dome ignores the 6 collar slits (distance to the moat only), so slit ends no longer scoop round pockets out of the dome edge
_sf = sg(sdf_of(B | _FS), 1.0); _bf = np.clip(_sf / W, 0, 1); _bf = _bf * _bf * (3 - 2 * _bf)
bev = _FD * _bf + (1 - _FD) * bev
H = np.clip(level * bev, 0, 1) * np.clip(B + (sdf > -.3), 0, 1)
# s79 collar slit ends: light Gaussian of H in a soft window around the 6 collar slits (r 53..69, within SLW px of the gap line) removes the stair-stepped teeth where the slits meet the dome edge
_slw = E('SLW', 9); _wr = np.clip(np.minimum(_r - (29 * sc - 5), (29 * sc + E('COL', 8) + 2.5) - _r) / 3, 0, 1)
_wa = np.clip((_slw - _r * np.sin(np.radians(np.clip(_gd, 0, 90)))) / 3, 0, 1); _ws = _wr * _wa
H = np.clip(_ws * sg(H, E('SLG', 1.3)) + (1 - _ws) * H, 0, 1)
# s88 collar ring ripple: tangential (along-angle) Gaussian of H in the collar band r CR0..CR1 around the flower centre, skipped within CRG deg of the 6 petal gap lines (slits keep their shape). CRS = sigma in px along the ring (0 = off, reproduces prior map)
_crs = E('CRS', 3.0)
if _crs > 0:
    _CR0, _CR1, _CRG = E('CR0', 52), E('CR1', 66), E('CRG', 9)
    _NA = 2880; _rr = np.arange(40, 80, .5)
    _th = np.linspace(0, 2 * np.pi, _NA, endpoint=False)
    _mx = (820.2 + _rr[:, None] * np.cos(_th)[None]).astype(np.float32); _my = (233.7 + _rr[:, None] * np.sin(_th)[None]).astype(np.float32)
    _pol = cv2.remap(H.astype(np.float32), _mx, _my, cv2.INTER_CUBIC)
    _sp = ndi.gaussian_filter1d(_pol, _crs / 66 * _NA / (2 * np.pi), axis=1, mode='wrap')
    _dg = np.min(np.abs((np.degrees(_th)[None] - np.array(FGAP)[:, None] + 180) % 360 - 180), axis=0)
    _wa = np.clip((_dg - _CRG) / 3, 0, 1)[None]; _wr = np.clip(np.minimum(_rr - _CR0, _CR1 - _rr) / 2, 0, 1)[:, None]
    _wgt = _wa * _wr; _d = (_sp - _pol) * _wgt
    _dH = np.zeros(H.shape, np.float32); _cnt = np.zeros(H.shape, np.float32)
    _xi = np.clip(np.round(_mx).astype(int), 0, TW - 1); _yi = np.clip(np.round(_my).astype(int), 0, TH - 1)
    np.add.at(_dH, (_yi, _xi), _d); np.add.at(_cnt, (_yi, _xi), 1)
    _ok = _cnt > 0; H = np.clip(H + np.where(_ok, _dH / np.maximum(_cnt, 1), 0), 0, 1)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
cv2.imwrite(OUT, (H * 65535).astype(np.uint16))
m_ = H; gy, gx = np.gradient(m_ * 40); nn = np.dstack([-gx, -gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
hs = np.clip(nn @ np.array([-1, -1, 1.2]) / np.linalg.norm([-1, -1, 1.2]), 0, 1); hs = hs / hs.max()
cv2.imwrite(OUT.replace('.png', '_hillshade.png'), (hs * 255).astype(np.uint8))
print('wrote', OUT, H.shape, 'beads:', len(BEADS), 'coverage %.3f' % B.mean())
