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
_grv = np.zeros((TH, TW), np.float32)   # s114 GRO: groove weight for the lower-petal ribs (entries 0,1)
if E('SLIT', 1):
    for _i, (_off, _pr) in SLITS.items():
        _pr = np.array(_pr, float); _wr = np.interp(_r, _pr[:, 0], _pr[:, 1], right=0) * E('SLW', 1.0)
        _dth = np.abs((_a - (FAX[_i] + _off) + 180) % 360 - 180)
        _px = _r * np.sin(np.radians(np.clip(_dth, 0, 90)))
        # s114 GRO: the ref's lower-petal rib (entries 0,1) is black only ~12-16 px next to the collar, then a brown groove with gold ribs on both sides (not a through-cut to ground). Through-cut only for r < SLR0 (tapered to a point), beyond it the footprint stays gold and the rib becomes a shallow groove (H *= 1 - GRD*weight). GRO=0 reverts.
        if E('GRO', 1) and _i in (0, 1):
            _wc = _wr * np.clip((E('SLR0', 96) + 6 - _r) / 12, 0, 1)
            B = B & ~((_px < _wc / 2) & (_dth < 40) & (_r >= RB - 4))
            _gw = np.clip(1 - (_px / np.maximum(_wr * E('GRW', 1.0) / 2, .5)) ** 2, 0, 1) * np.clip((_r - (E('SLR0', 96) - 6)) / 14, 0, 1) * (_dth < 40) * (_wr > 0)
            _grv = np.maximum(_grv, _gw.astype(np.float32))
        else:
            B = B & ~((_px < _wr / 2) & (_dth < 40) & (_r >= RB - 4))
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
    CUTS = [(396, 319, 26), (575, 312, 30), (519, 56, 30)]
    for _cx, _cy, _wr in CUTS:
        B = B & ~(_Dk & (np.hypot(_bx - _cx, _by - _cy) <= _wr))
    # s98 scroll/leaf outline smoothing SCS (extra level-set sigma, px): only the big scroll/leaf components of the silhouette (area >= SCA, not the flower: component must not contain the flower centre (820,234)); flower, beads and the later REFW/GAPL windows are untouched. SCS=0 disables (reproduces prior map).
    if E('SCS', 0) > 0:
        _ls, _ns = ndi.label(B); _as = np.bincount(_ls.ravel(), minlength=_ns + 1); _fl = _ls[234, 820]
        _sc = np.isin(_ls, [i for i in range(1, _ns + 1) if _as[i] >= E('SCA', 5000) and i != _fl])
        _Bsm = sg(sdf_of(B), E('SCS', 0)) > 0
        B = np.where(ndi.binary_dilation(_sc, iterations=6), _Bsm, B)
    # s104 SPX sub-pixel scroll outline (precision mapping, not smoothing): on scroll/leaf components only (same selection as SCS), the edge is re-traced from the ref's own crisp gold rim: cubic-upsampled ref gray (map res) thresholded at SPT (rim is a sharp orange edge; V 50..95 give the same contour). Kept only within SPR px of the current silhouette (rejects ground speckle), no SDF smoothing. SPX=0 disables (reproduces prior map).
    if E('SPX', 1):
        _ls, _ns = ndi.label(B); _as = np.bincount(_ls.ravel(), minlength=_ns + 1); _fl = _ls[234, 820]
        _sc = np.isin(_ls, [i for i in range(1, _ns + 1) if _as[i] >= E('SCA', 5000) and i != _fl])
        _Vs = cv2.GaussianBlur(rs(Vt), (0, 0), E('SPB', .8)); _Rv = _Vs > E('SPT', 70)
        _zn = ndi.binary_dilation(_sc, iterations=int(E('SPR', 5)))
        _Rv = ndi.binary_opening(_Rv, structure=np.ones((3, 3)))
        if E('SPG', 2) > 0:   # grow the crisp V>SPT contour outward by <=SPG px where V>SPL (rim foot; bevel eats ~2 px of footprint): uniform band, so ground speckle cannot scallop the edge
            _Rv = _Rv | (ndi.binary_dilation(_Rv, iterations=int(E('SPG', 2))) & (_Vs > E('SPL', 35)))
        _Bn = (_Rv & _zn) | ndi.binary_erosion(B & _zn, iterations=int(E('SPR', 5)))
        _hl, _hn = ndi.label(~_Bn); _ha = np.bincount(_hl.ravel(), minlength=_hn + 1); _Bn = _Bn | np.isin(_hl, [i for i in range(1, _hn + 1) if _ha[i] < 150])
        _yy, _xx = np.mgrid[:TH, :TW]; _zf = np.hypot(_xx - 820, _yy - 234) > E('SPF', 340)   # SPF>0 leaves the flower disc (r<=SPF around 820,234) untouched
        B = np.where(ndi.binary_dilation(_sc, iterations=6) & _zf, _Bn, B)
    # s105 SPC contour-tangent smoothing (not an image blur): trace the silhouette as a sub-pixel closed curve, resample at 1 px, Gaussian-smooth the point sequence ALONG the curve (sigma SPC px), re-rasterise at 4x with holes. Removes the 1-2 px ripple that the ref's pixel-stepped rim leaves (it scallops the lit bevel); same zone as SPX (scroll comps, flower disc untouched). SPC=0 disables (reproduces prior map).
    if E('SPC', 6) > 0:
        from skimage import measure
        _T3 = tri(B.astype(np.float32)); _T3 = cv2.GaussianBlur(_T3, (0, 0), .8); _cs = measure.find_contours(_T3, .5); _S = 4; _cv = np.zeros((TH * _S, 3 * TW * _S), np.uint8)
        _lst = []
        for _c in _cs:
            if len(_c) < 12: continue
            _d = np.r_[0, np.cumsum(np.hypot(*np.diff(_c, axis=0).T))]; _n = max(int(_d[-1]), 8); _u = np.linspace(0, _d[-1], _n, endpoint=False)
            _q = np.c_[np.interp(_u, _d, _c[:, 0]), np.interp(_u, _d, _c[:, 1])]
            if np.hypot(*(_c[0] - _c[-1])) < 1.5 and _n > 20:
                _sm_ = ndi.gaussian_filter1d(_q, E('SPC', 6), axis=0, mode='wrap')
                if E('SPB2', 12) > E('SPC', 6):   # s106 adaptive: where the long-sigma curve stays within ~SPD px of the short-sigma curve the deviation is ripple -> use the long sigma; at tips/corners/tight bends it deviates more -> keep the short sigma
                    _bg_ = ndi.gaussian_filter1d(_q, E('SPB2', 12), axis=0, mode='wrap'); _dv_ = np.hypot(*(_bg_ - _sm_).T)
                    _w_ = np.clip((_dv_ - E('SPD', 1.2)) / E('SPD2', 2.0), 0, 1); _w_ = ndi.gaussian_filter1d(_w_, 4, mode='wrap')
                    _q = _bg_ + _w_[:, None] * (_sm_ - _bg_)
                else: _q = _sm_
            if E('SPWS', 30) > 0 and len(_q) > 20:   # s107 local strong smoothing windows SPW='x,y,r[,sigma];...' (map coords): inside a window the contour gets sigma (default SPWS; smooth-step weight by distance); SPWS=0 off
                for _wd in os.environ.get('SPW', '577,59,24;200,325,45,20;735,60,75,14,3.5;890,55,75,14,3.5;783,312,40,9,1.5;875,322,40,9,1.5').split(';'):
                    _wv = [float(v) for v in _wd.split(',')]; _wx, _wy, _wr = _wv[:3]; _wsg = _wv[3] if len(_wv) > 3 else E('SPWS', 30)
                    _dd = np.hypot((_q[:, 1] % TW) - _wx, _q[:, 0] - _wy) / _wr; _ww_ = np.clip(1.6 - 1.6 * _dd, 0, 1)
                    if _ww_.max() > 0: _ww_ = ndi.gaussian_filter1d(_ww_, 3, mode='wrap'); _q = _q + _ww_[:, None] * (ndi.gaussian_filter1d(_q, _wsg, axis=0, mode='wrap') - _q)
                    _wgr = _wv[4] if len(_wv) > 4 else 0   # s113 optional 5th window value = outward grow px (weighted like the smoothing) to cancel the shrink of convex rounding; absent = prior behaviour
                    if _wgr > 0 and _ww_.max() > 0:
                        _tt = np.roll(_q, -1, 0) - np.roll(_q, 1, 0); _tt /= np.maximum(np.hypot(*_tt.T), 1e-6)[:, None]; _nn = np.c_[_tt[:, 1], -_tt[:, 0]]
                        _pp = np.round(_q + _nn * 3).astype(int); _pr = np.clip(_pp[:, 0], 0, TH - 1); _pc = np.clip(_pp[:, 1], 0, 3 * TW - 1)
                        if np.tile(B, (1, 3))[_pr, _pc].mean() > .5: _nn = -_nn
                        _q = _q + _wgr * _ww_[:, None] * _nn
            _lst.append(_q)
        _pts = [np.round(np.c_[q[:, 1], q[:, 0]] * _S + _S / 2).astype(np.int32) for q in _lst]
        _ar = [abs(cv2.contourArea(q)) for q in _pts]
        # fill with even-odd via XOR of per-contour fills (holes toggle)
        for q in _pts:
            _t = np.zeros_like(_cv); cv2.fillPoly(_t, [q], 1); _cv ^= _t
        _Bc = cv2.resize(_cv[:, TW * _S:2 * TW * _S].astype(np.float32), (TW, TH), interpolation=cv2.INTER_AREA) > .5
        _yy, _xx = np.mgrid[:TH, :TW]; _zf2 = np.hypot(_xx - 820, _yy - 234) > E('SPF', 340)
        if E('SPWS', 30) > 0:   # s107 smoothing windows also lift the flower-disc exclusion locally (the frond tip near 575,57 is inside r<=340)
            for _wd in os.environ.get('SPW', '577,59,24;200,325,45,20;735,60,75,14,3.5;890,55,75,14,3.5;783,312,40,9,1.5;875,322,40,9,1.5').split(';'):
                _wx, _wy, _wr = [float(v) for v in _wd.split(',')[:3]]; _zf2 |= np.hypot(_xx - _wx, _yy - _wy) <= _wr + 8
        if E('FPC', 0):   # s113 FPC: petal class. Petal gold comps (area>=SCA, not the bead/collar comp) outside radius FPR of 820,234 get the same adaptive contour smoothing as scrolls (SPC/SPB2; tips/corners keep short sigma); collar/slits (r<=FPR) untouched. FPC=0 reverts.
            _zf2 = _zf2 | (np.hypot(_xx - 820, _yy - 234) > E('FPR', 85))
        _ls2, _ns2 = ndi.label(B); _as2 = np.bincount(_ls2.ravel(), minlength=_ns2 + 1); _fl2 = _ls2[234, 820]
        _sc2 = np.isin(_ls2, [i for i in range(1, _ns2 + 1) if _as2[i] >= E('SCA', 5000) and i != _fl2])
        B = np.where(ndi.binary_dilation(_sc2, iterations=6) & _zf2, _Bc, B)
        np.save(os.environ.get('DUMPB','/tmp/Bdump.npy'), B)
    # s86 ref-shape windows (x, y, radius): inside, the map silhouette becomes the ref's own (ref gold union, minus ref-dark recess), level-set smoothed RSG. REFW=0 disables.
    REFW = [(1495, 395, 75), (438, 258, 16), (396, 319, 34), (142, 80, 30)]   # bottom-right pointed leaf recess; curl-head groove pocket; gap beside the curl; s91 scroll slit (142,80)
    if E('REFW', 1):
        _ev = _V[:, C0:C0 + P + SEAM].copy(); _tv = _ev[:, :P].copy(); _tv[:, :SEAM] = (1 - _al) * _ev[:, P:P + SEAM] + _al * _ev[:, :SEAM]
        _Dk2 = ndi.binary_opening(cv2.resize(_tv, (TW, TH), interpolation=cv2.INTER_CUBIC) < E('RDT', 60), np.ones((E('RDO', 1).__int__(),) * 2)); _l3, _n3 = ndi.label(_Dk2); _a3 = np.bincount(_l3.ravel(), minlength=_n3 + 1); _Dk2 = np.isin(_l3, [i for i in range(1, _n3 + 1) if _a3[i] >= 60])
        if E('RCL', 9): _Dk2 = ndi.binary_closing(np.pad(_Dk2, 12), np.ones((int(E('RCL', 9)),) * 2))[12:-12, 12:-12] | _Dk2   # s87: close the ref-dark recess (fills notches where a highlight stripe crosses its rim)
        _Bn = (ndi.binary_dilation(B | _Rg, iterations=E('RGR', 4).__int__()) & ~_Dk2) if E('RFILL', 1) else ((B | _Rg) & ~_Dk2); _Bs = sg(sdf_of(_Bn), E('RSG', 1.5)) > 0
        for _cx, _cy, _wr in REFW:
            B = np.where(np.hypot(_bx - _cx, _by - _cy) <= _wr, _Bs, B)
# s93 shaded-gold grooves SHADE (x, y, r): ref dark-BROWN creases (V ~40..100, clearly brighter than bare ground V<~25) are recessed gold, not holes to the ground. Inside the window the silhouette hole is closed (disk SHC px), and the filled area gets a groove whose depth follows the ref darkness: plate *= 1 - SD * clip((SHV1 - V)/(SHV1 - SHV0), 0, 1). SHADE=0 disables.
SHADE = [(1390, 463, 55)]; SHS = np.zeros(B.shape, bool); SHD = np.zeros(B.shape, np.float32)
if E('SHADE', 0):
    _ev2 = _V[:, C0:C0 + P + SEAM].copy(); _tv2 = _ev2[:, :P].copy(); _tv2[:, :SEAM] = (1 - _al) * _ev2[:, P:P + SEAM] + _al * _ev2[:, :SEAM]
    _tvr = cv2.GaussianBlur(cv2.resize(_tv2, (TW, TH), interpolation=cv2.INTER_CUBIC), (0, 0), E('SHB', 1.5))
    _k = int(E('SHC', 12)); _dk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * _k + 1, 2 * _k + 1))
    _cl = ndi.binary_closing(np.pad(B, 20), _dk)[20:-20, 20:-20]
    for _cx, _cy, _wr in SHADE:
        _w = np.hypot(_bx - _cx, _by - _cy) <= _wr; SHS |= _cl & ~B & _w
    SHS = sg(SHS.astype(np.float32), E('SHG', 1.5)) > .5
    B = B | SHS
    for _cx, _cy, _wr in SHADE: B = B | (ndi.binary_closing(np.pad(B, 4), np.ones((3, 3)))[4:-4, 4:-4] & (np.hypot(_bx - _cx, _by - _cy) <= _wr + 6))   # close 1-px pinholes at the groove/strip seams
    SHD = np.clip((E('SHV1', 95) - _tvr) / (E('SHV1', 95) - E('SHV0', 28)), 0, 1) * sg(SHS.astype(np.float32), 2.0)
# s94 gap channels GAPL ([(x,y),...], full width px): empty space between two petals that the ref shows as a thin brown channel (V ~60-90, too bright for the dark-recess detector) -> carved out of the silhouette along the polyline. User-confirmed: brown here = empty space, not recessed gold. GAPL=0 disables.
GAPL = [([(1463, 433), (1440, 443), (1423, 455), (1403, 463), (1390, 472), (1373, 480), (1350, 488)], E('GAPW', 4))]   # s95 one continuous gap A->D (user-confirmed empty space)
if E('GAPL', 1):
    for _pts, _gw in GAPL:
        _gm = np.zeros(B.shape, np.uint8); cv2.polylines(_gm, [np.round(np.array(_pts) * 1.0).astype(np.int32).reshape(-1, 1, 2)], False, 1, int(round(_gw)), cv2.LINE_AA)
        B = B & ~(_gm > 0)
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
        _FS = ((_r * np.sin(np.radians(np.clip(_gd, 0, 90))) < (E('CGW', 3) + E('CGX', 9) * np.clip((d - R) / (Rc - R), 0, 1) ** E('CGP', 1.2))) & (d > R) & (d <= Rc)); _FD = np.clip((R + 2.5 - d) / 5, 0, 1)   # s79: slit mask + soft dome weight (1 inside r<=R-2.5, 0 beyond R+2.5)
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
if SHS.any(): plate = plate * (1 - E('SD', .45) * SHD)   # s93 shaded-gold groove depth (follows ref darkness)
if GR > 0:   # thin dark hairlines inside gold (black-hat of ref luminance); wide dark bands are reflections, not grooves -> thin + elongated comps only
    Vb = cv2.GaussianBlur(Vt, (0, 0), 1.0); bh = cv2.morphologyEx(Vb, cv2.MORPH_CLOSE, np.ones((int(E('GK', 11)),) * 2, np.uint8)) - Vb   # s105 GK kernel (5 = thin hairlines only, prior behaviour; 11 default s105, GCgold scroll .309->.328; ~11-15 also catches broad creases between leaf bands)
    g = rs(((bh > E('GT', 30))).astype(np.float32)) > .5
    g &= ndi.binary_erosion(B & ~isbead, iterations=14)
    g &= ~(_r < 335)   # flower petals get procedural veins instead (s74)
    gl, gn = ndi.label(g, structure=np.ones((3, 3))); keep = np.zeros_like(g)
    for k, sl in enumerate(ndi.find_objects(gl), 1):
        h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if max(h_, w_) >= 40: keep |= gl == k
    if E('GSOFT', 1):   # s100 the binary groove mask (threshold, resample, >.5) leaves 1-px stair-steps along the thin scroll creases (dashed look in the hillshade, ridged in 3D). GSOFT=1: same components (keep), but the weight inside them is the ref's own soft black-hat response (graded, not thresholded), blurred GSS px. GSOFT=0 = prior behaviour.
        _soft = rs(np.clip((bh - E('GT', 30) * .7) / (E('GT', 30) * .6), 0, 1).astype(np.float32)) * ndi.binary_dilation(keep, iterations=2)
        _sk = sg(_soft.astype(np.float32), E('GSS', 2.0)); plate = plate * (1 - GD * _sk / max(_sk.max(), 1e-3))
    else:
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
# s107 RID crest ridges: thin bright lines inside scroll gold (white-hot highlight lines = rolled leaf edges / ridge crests; top-hat of ref luminance, width < 5 ref px, elongated >= RIL ref px) raise the plate by RID along the line (soft, blurred RIS map px). Scroll class only (flower disc r<335, beads, 8 px of the rim excluded). RID=0 disables (reproduces prior map).
if E('RID', .12) > 0:
    _Vr = cv2.GaussianBlur(Vt, (0, 0), 1.0); _th = _Vr - cv2.morphologyEx(_Vr, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    _rg = rs(np.clip((_th - E('RIT', 12)) / E('RIT2', 25), 0, 1).astype(np.float32))
    _rb = (_rg > .3) & ndi.binary_erosion(B & ~isbead, iterations=int(E('RIE', 8))) & ~(_r < 335)
    _rl, _rn = ndi.label(_rb, structure=np.ones((3, 3))); _rk = np.zeros_like(_rb)
    for _k, _sl in enumerate(ndi.find_objects(_rl), 1):
        if max(_sl[0].stop - _sl[0].start, _sl[1].stop - _sl[1].start) >= 2 * E('RIL', 14): _rk |= _rl == _k
    _rm = (_rg * ndi.binary_dilation(_rk, iterations=2)).astype(np.float32)
    if E('LS', 15) > 0:   # s108 oriented line smoothing: average the ridge map along each of LSN directions with a line kernel (length LS px, 0.8 px wide), keep the per-pixel max -> fills the gaps/dashes in a continuous line, dims isolated specks; LS=0 off
        _L = int(E('LS', 15)) | 1; _o = np.zeros_like(_rm)
        for _a in range(int(E('LSN', 16))):
            _t = np.pi * _a / int(E('LSN', 16)); _kk = np.zeros((_L, _L), np.float32); _c0 = _L // 2
            cv2.line(_kk, (int(round(_c0 - _c0 * np.cos(_t))), int(round(_c0 - _c0 * np.sin(_t)))), (int(round(_c0 + _c0 * np.cos(_t))), int(round(_c0 + _c0 * np.sin(_t)))), 1, 1)
            _kk = cv2.GaussianBlur(_kk, (0, 0), .8); _kk /= _kk.sum(); _o = np.maximum(_o, cv2.filter2D(_rm, -1, _kk))
        _rm = _o
    _rs = sg(_rm, E('RIS', 2.0))
    plate = plate + E('RID', .12) * _rs / max(_rs.max(), 1e-3)
_LUM = E('LUM', 0)
if _LUM > 0:   # s76 faint shape-from-shading: ref luminance (blurred) relative to its local gold mean -> +-LUM height; flower disc excluded (procedural veins)
    _Vl = sg(rs(Vt), E('LSIG', 5)); _w = (B & ~isbead).astype(np.float32)
    _mu = sg(_Vl * _w, 30) / np.maximum(sg(_w, 30), 1e-3)
    plate = plate + _LUM * np.clip((_Vl - _mu) / 60, -1, 1) * np.clip((_r - 300) / 60, 0, 1) * sg(_w, 2)
plate = plate - VG
if E('NOCURL', 1) and E('CB', .25) > 0:   # s86: gentle rounded swell on the scroll's curl head (ref head is a lit round end), smooth falloff so no circle edge
    _dc = np.hypot(Xg - 228 * sc, Yg - 145 * sc) / (E('CBR', 1.15) * 21 * sc); plate = plate + E('CB', .25) * (1 - np.clip(_dc, 0, 1) ** 2) ** 2
level = np.where(big, plate, level)
_sb = sg(sdf, E('SBS', 2.0)) if E('SBS', 2.0) > 0 else sdf   # s79 rim faceting: bevel ramp from a smoother SDF (binary-mask staircase made stripes on the rims)
# s99 SBC: rim scalloping on the big scroll/leaf shapes only (silhouette wiggles wider than SBS survive into the bevel foot): bevel ramp from a smoother SDF (sigma SBC) there. Class = silhouette components of area >= 5000 not containing the flower centre, dilated 8 px, soft edge. Flower, beads, collar and gap lips keep SBS. SBC=0 disables (reproduces prior map).
if E('SBC', 3) > 0:
    _lc, _nc = ndi.label(B); _ac = np.bincount(_lc.ravel(), minlength=_nc + 1)
    _cc = ndi.center_of_mass(B, _lc, range(1, _nc + 1))   # petals are separate components too: keep only shapes centred > 300 px from the flower centre
    _scm = np.isin(_lc, [i for i in range(1, _nc + 1) if _ac[i] >= 5000 and np.hypot(_cc[i - 1][1] - 820, _cc[i - 1][0] - 234) > 300]).astype(np.float32)
    _scm = np.clip(sg(ndi.binary_dilation(_scm > 0, iterations=8).astype(np.float32), 2.0), 0, 1)
    _sb = _scm * sg(sdf, E('SBC', 3)) + (1 - _scm) * _sb
bev = np.clip(_sb / W, 0, 1); bev = bev * bev * (3 - 2 * bev)
# s79 collar slit pockets: the bevel of the flower dome ignores the 6 collar slits (distance to the moat only), so slit ends no longer scoop round pockets out of the dome edge
_sf = sg(sdf_of(B | _FS), 1.0); _bf = np.clip(_sf / W, 0, 1); _bf = _bf * _bf * (3 - 2 * _bf)
bev = _FD * _bf + (1 - _FD) * bev
H = np.clip(level * bev, 0, 1) * np.clip(B + (sdf > -.3), 0, 1)
if E('GRO', 1): H = H * (1 - E('GRD', .7) * np.clip(sg(_grv, 1.2), 0, 1))   # s114 shallow rib grooves (see SLITS)
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
# s97 ground texture GAMP: the ref ground is stippled (crackle, ~6-12 px features); the map ground was perfectly flat (H=0). Raised micro-relief taken straight from the ref's own ground brightness (high-pass of V, bright = raised, positive only so the base level stays 0), only where the ground is >= GCLR px from any gold (full strength after +GRAMP px) and inside the panel rows GY0..GY1. Gold pixels are never touched. GAMP=0 disables (reproduces prior map).
_gamp = E('GAMP', .015)
if _gamp > 0:
    _ev3 = _V[:, C0:C0 + P + SEAM].copy(); _tv3 = _ev3[:, :P].copy(); _tv3[:, :SEAM] = (1 - _al) * _ev3[:, P:P + SEAM] + _al * _ev3[:, :SEAM]
    _g = cv2.resize(_tv3, (TW, TH), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    _hp = cv2.GaussianBlur(_g, (0, 0), E('GSG', .9)) - cv2.GaussianBlur(_g, (0, 0), E('GLP', 7))
    _tex = np.clip(_hp / E('GSC', 25), 0, 1)
    _gd = cv2.distanceTransform((H <= .01).astype(np.uint8), cv2.DIST_L2, 5)
    _gw = np.clip((_gd - E('GCLR', 12)) / E('GRAMP', 6), 0, 1) * np.clip(np.minimum(np.arange(TH) - E('GY0', 12), E('GY1', 496) - np.arange(TH)) / 6, 0, 1)[:, None]
    _gw = _gw * (H <= .01)
    H = np.clip(H + _gamp * _tex * _gw, 0, 1)
# s106 BSS bulb interior smoothing: the bulb (~460,280) is a smooth dome in the ref but the RID ridge / GK groove terms put lumps and a step into its interior. Inside windows BSW 'x,y,r;..' replace H by a normalized-convolution gaussian (sigma BSS, gold only so the moat does not pull it down), blended in only where the pixel is >= BSD px inside the footprint (ramp BSR) so the rim/bevel is untouched. BSS=0 disables (reproduces prior map).
_bss = E('BSS', 5); _bwin = np.zeros((TH, TW), np.float32)
if _bss > 0:
    _yy5, _xx5 = np.mgrid[:TH, :TW]; _w5 = np.zeros((TH, TW), np.float32)
    for _q in os.environ.get('BSW', '460,280,45').split(';'):
        _a5 = [float(v) for v in _q.split(',')]; _w5 = np.maximum(_w5, np.clip((_a5[2] - np.hypot(_xx5 - _a5[0], _yy5 - _a5[1])) / 6, 0, 1))
    _mk5 = (H > .03).astype(np.float32)
    _hs5 = cv2.GaussianBlur(H * _mk5, (0, 0), _bss) / np.maximum(cv2.GaussianBlur(_mk5, (0, 0), _bss), 1e-4)
    _de5 = cv2.distanceTransform(_mk5.astype(np.uint8), cv2.DIST_L2, 5)
    _bwin = np.clip(_w5 * 1.0, 0, 1)
    _w5 = _w5 * np.clip((_de5 - E('BSD', 4)) / E('BSR', 14), 0, 1)
    H = H * (1 - _w5) + _hs5 * _w5
# s107 FRA procedural frond ridges (user-approved creative step): the ref scroll bodies carry parallel leaf bands with thin bright highlight lines; the map plateaus were comparatively smooth. Adds FRK narrow ridges (gaussian cross-section sigma FRW, height FRA) running parallel to the outline at inner distances FR0 + k*FRP px from the footprint edge (d from distanceTransform of H>.03, slightly warped by low-frequency noise FRJ px so the spacing is not mechanical). Faded out near the medial axis of each band (hw = local max inscribed distance; ridge weight ramps to 0 within FRM px of it) so ridges never cross, only on big scroll bodies (components > FRB px, outside the flower disc r<FRD, outside the bulb smoothing window). Footprint and rim untouched. FRA=0 disables (reproduces prior map).
_fra = E('FRA', .025)
if _fra > 0:
    _mk6 = (H > .03).astype(np.uint8); _d6 = cv2.distanceTransform(_mk6, cv2.DIST_L2, 5)
    _hw6 = cv2.dilate(_d6, np.ones((E('FRH', 41).__int__(), E('FRH', 41).__int__()), np.uint8))
    _rs6 = np.random.RandomState(7); _nz6 = cv2.GaussianBlur(_rs6.randn(TH, TW).astype(np.float32), (0, 0), 25); _nz6 = _nz6 / max(np.abs(_nz6).max(), 1e-6)
    _dj6 = _d6 + E('FRJ', 2.0) * _nz6
    _rg6 = np.zeros((TH, TW), np.float32)
    for _k6 in range(int(E('FRK', 2))):
        _rg6 += np.exp(-0.5 * ((_dj6 - (E('FR0', 9) + _k6 * E('FRP', 10))) / E('FRW', 2.2)) ** 2)
    _wm6 = np.clip((_hw6 - _d6 - E('FRM', 5)) / 6, 0, 1)
    _l6, _n6 = ndi.label(_mk6); _a6 = np.bincount(_l6.ravel(), minlength=_n6 + 1)
    _big6 = np.isin(_l6, [i for i in range(1, _n6 + 1) if _a6[i] >= E('FRB', 14000)]).astype(np.float32)
    _yy6, _xx6 = np.mgrid[:TH, :TW]; _fd6 = np.clip((np.hypot(_xx6 - 820, _yy6 - 233.7) - E('FRD', 345)) / 8, 0, 1)
    _nm6 = cv2.GaussianBlur(np.random.RandomState(11).randn(TH, TW).astype(np.float32), (0, 0), E('FRL', 40)); _nm6 = _nm6 / max(np.abs(_nm6).max(), 1e-6)
    _am6 = np.clip(E('FRB0', .6) + E('FRB1', 1.4) * _nm6, E('FRMN', .15), 1)
    _rw6 = cv2.GaussianBlur(_big6, (0, 0), 2) * _fd6 * (1 - _bwin) * _am6
    H = np.clip(H + _fra * _rg6 * _wm6 * _rw6, 0, 1)
# s106 KNB bright gold knobs in the ground (~1057,450 / 1080,447): ref shows two raised bright gold shapes (V>KNT) that the map had as faint bumps. Inside windows KNW 'x,y,r;..' take ref V>KNT (map space), drop specks < KNA px, soften the edge by KNS px sigma and raise H to at least KNB*mask (plateau level). Everything outside the windows untouched. KNB=0 disables (reproduces prior map).
_knb = E('KNB', 0)
if _knb > 0:
    _ev4 = _V[:, C0:C0 + P + SEAM].copy(); _tv4 = _ev4[:, :P].copy(); _tv4[:, :SEAM] = (1 - _al) * _ev4[:, P:P + SEAM] + _al * _ev4[:, :SEAM]
    _g4 = cv2.GaussianBlur(cv2.resize(_tv4, (TW, TH), interpolation=cv2.INTER_CUBIC).astype(np.float32), (0, 0), 1.0)
    _yy4, _xx4 = np.mgrid[:TH, :TW]; _win = np.zeros((TH, TW), bool)
    for _w4 in os.environ.get('KNW', '1074,447,34').split(';'):
        _a4 = [float(v) for v in _w4.split(',')]; _win |= np.hypot(_xx4 - _a4[0], _yy4 - _a4[1]) < _a4[2]
    _m4 = (_g4 > E('KNT', 130)) & _win
    _l4, _n4 = ndi.label(_m4); _ar4 = np.bincount(_l4.ravel(), minlength=_n4 + 1)
    _m4 = np.isin(_l4, [i for i in range(1, _n4 + 1) if _ar4[i] >= E('KNA', 30)])
    _m4 = ndi.binary_closing(_m4, np.ones((3, 3))); _m4 = ndi.binary_fill_holes(_m4)
    _s4 = np.clip(cv2.GaussianBlur(_m4.astype(np.float32), (0, 0), E('KNS', 1.5)) * 1.0, 0, 1) * _win
    H = np.maximum(H, _knb * _s4)
# s110 FSH: shift the whole flower (petals+bead, gold comps within r<=FSR of 820,234, area>5000) along u by FSH map px (+ = screen down on the ring view; 20 balances top/bottom clearance 42/45 px, was 23/60). Old footprint (halo FSM px) is ground-filled from nearest outside ground; the small bead below-left stays. FSH=0 reverts.
_fsh = int(E('FSH', 4))
if _fsh:
    _l5, _n5 = ndi.label(H > .03); _yy5, _xx5 = np.mgrid[:TH, :TW]; _F5 = np.zeros((TH, TW), bool)
    for _i5 in range(1, _n5 + 1):
        _c5 = _l5 == _i5
        if _c5.sum() > 5000:
            _cy5, _cx5 = ndi.center_of_mass(_c5)
            if np.hypot(_cx5 - 820, _cy5 - 234) <= E('FSR', 250): _F5 |= _c5
    _Rg = ndi.binary_dilation(_F5, structure=np.ones((3, 3)), iterations=int(E('FSM', 10)))
    _ix = ndi.distance_transform_edt(_Rg, return_distances=False, return_indices=True)
    _Hf = H[_ix[0], _ix[1]]; _Hn = H.copy(); _Hn[_Rg] = _Hf[_Rg]
    _Rs = np.roll(_Rg, _fsh, axis=1); _Hn[_Rs] = np.roll(H, _fsh, axis=1)[_Rs]; H = _Hn
# s111 FSV/FSS: centre the flower across the band (rows = v). Bead row -> map middle (FSV rows shift, + = toward larger row), flower scaled by FSS about the bead so the longer petal side keeps a rim margin. FSV=0 FSS=1 reverts.
_fsv = int(E('FSV', 26)); _fss = E('FSS', .88)
if _fsv or _fss != 1:
    _l6, _n6 = ndi.label(H > .03); _F6 = np.zeros((TH, TW), bool)
    for _i6 in range(1, _n6 + 1):
        _c6 = _l6 == _i6
        if _c6.sum() > 5000:
            _cy6, _cx6 = ndi.center_of_mass(_c6)
            if np.hypot(_cx6 - 840, _cy6 - 234) <= E('FSR', 250): _F6 |= _c6
    _R6 = ndi.binary_dilation(_F6, structure=np.ones((3, 3)), iterations=int(E('FSM', 10)))
    _ix6 = ndi.distance_transform_edt(_R6, return_distances=False, return_indices=True)
    _Hb = H.copy(); _Hb[_R6] = H[_ix6[0], _ix6[1]][_R6]
    _cx0, _cy0 = E('FSX', 820. + _fsh), E('FSY', 233.5)
    _M6 = np.float32([[_fss, 0, _cx0 - _fss * _cx0], [0, _fss, _cy0 + _fsv - _fss * _cy0]])
    _Hw = cv2.warpAffine((H * _R6).astype(np.float32), _M6, (TW, TH), flags=cv2.INTER_CUBIC)
    _Wm = cv2.warpAffine(_R6.astype(np.float32), _M6, (TW, TH), flags=cv2.INTER_LINEAR) > .5
    _g0 = ndi.distance_transform_edt(~(H > .03)) > E('FSD0', 14)
    _H0 = H.copy()
    H = np.where(_Wm, _Hw, _Hb)
    # s112 FSQ: moved/scaled flower leaves a stipple-free ring (old footprint + 12 px margin) = dotted seam. Refill with block-copied real ground stipple wherever now >= FSQD px from gold (design margin was 12).
    if int(E('FSQ', 1)):
        _dn = ndi.distance_transform_edt(~(H > .03))
        _T = (_R6 | _Wm) & (_dn > E('FSQD', 12)) & (H < .03)
        _ok = ndi.binary_erosion(_g0 & (_H0 < .016), structure=np.ones((8, 8)))
        _src = np.argwhere(_ok); _rg = np.random.RandomState(7)
        _ys, _xs = np.where(_R6 | _Wm)
        for _by in range(_ys.min(), _ys.max() + 1, 8):
            for _bx in range(_xs.min(), _xs.max() + 1, 8):
                _t = _T[_by:_by + 8, _bx:_bx + 8]
                if not _t.any(): continue
                _sy, _sx = _src[_rg.randint(len(_src))] - 4
                _blk = _H0[_sy:_sy + 8, _sx:_sx + 8]
                _hh, _ww = _t.shape
                _cur = H[_by:_by + 8, _bx:_bx + 8]
                _cur[_t] = _blk[:_hh, :_ww][_t]
    _f6 = np.where(_Wm & (H > .03))
    print('flower rows', _f6[0].min(), _f6[0].max(), 'bead row target', _cy0 + _fsv)
# s113 CLP: cubic warp (FSS) undershoots <0 at the gold edge; uint16 cast wrapped it to 1.0 = 1-px wall = dotted outline. Clip H to [0,1] before writing. CLP=0 reverts.
if int(E('CLP', 1)): H = np.clip(H, 0, 1)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
cv2.imwrite(OUT, (H * 65535).astype(np.uint16))
m_ = H; gy, gx = np.gradient(m_ * 40); nn = np.dstack([-gx, -gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
hs = np.clip(nn @ np.array([-1, -1, 1.2]) / np.linalg.norm([-1, -1, 1.2]), 0, 1); hs = hs / hs.max()
cv2.imwrite(OUT.replace('.png', '_hillshade.png'), (hs * 255).astype(np.uint8))
print('wrote', OUT, H.shape, 'beads:', len(BEADS), 'coverage %.3f' % B.mean())
