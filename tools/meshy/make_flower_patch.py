# Solitaire 2: take the band's flower (whole one from the Meshy strip reference/meshy/model.glb) and place it, in solitaire model coordinates, on both flowers of site/solitaire_meshy2.glb.
# Output site/flower_patch.glb = one mesh (both flowers), the band's UVs/normals, a dummy material (the viewer swaps in the band's real material: same textures as band_meshy_tile.glb).
# The viewer removes the solitaire's own flower triangles inside the cut circles (CUTS json printed here -> index.html SOLS.solitaire2.cuts).
# usage: [S=0.8 SZ=1.25 RP=0.14 ROT=0 ROT2=180] python3 tools/meshy/make_flower_patch.py reference/meshy/model.glb site/solitaire_meshy2.glb site/flower_patch.glb
import sys, os, json, struct, numpy as np
strip, sol, out = sys.argv[1:4]
S = float(os.environ.get('S', 0.87)); SZ = float(os.environ.get('SZ', 1.4)); RP = float(os.environ.get('RP', 0.145)); RMAX = float(os.environ.get('RMAX', 0.125)); DIL = float(os.environ.get('DIL', 0.005)); RVINE = float(os.environ.get('RVINE', 0.104)); DH = float(os.environ.get('DH', -0.02)); DSINK = float(os.environ.get('DSINK', 0.001))   # DH: the cut also removes the solitaire's own floor triangles in the footprint (their texture is the old flower's gold = pale plate), down to 0.02 under the window floor plane (the bore is 0.075 lower, stays); the flat disc replaces that floor at DSINK under the plane;   # xy scale, height scale, patch radius in band units
ROT = [float(os.environ.get('ROT', 0)), float(os.environ.get('ROT2', 180))]                                          # in-plane rotation (deg) of the band flower on the +x / -x flower
SINK = float(os.environ.get('SINK', 0.004)); R0 = 0.82; CX, CY = -0.0001, -0.1190                     # patch = band relief (z > floor+0.003, band UVs) + a flat floor disc (constant solitaire UV) sunk SINK under the solitaire's floor; the viewer removes the solitaire's own flower relief inside a mask = the solitaire flower's footprint (star-shaped, walked out from the bead until the height drops to the floor, capped at RMAX, dilated DIL), packed as a bit raster in CUTS
FLOWERS = [(1, float(os.environ.get('U1', 0.6099)), float(os.environ.get('Z1', 0.0151))), (-1, float(os.environ.get('U2', 0.644)), float(os.environ.get('Z2', -0.006)))]   # (side, arc u at R0, z) start guesses for the bead centre

GAP = int(os.environ.get('GAP', 12))                  # petal creases are short: the outline ends at the first run of GAP consecutive low samples (0.0008 apart), not at the first low one
def first_run(low, n=None):
    n = n or GAP; c = np.convolve(low.astype(int), np.ones(n, int), 'valid'); i = np.where(c == n)[0]; return i[0] if len(i) else None

def glb(path):
    b = open(path, 'rb').read(); jl, _ = struct.unpack('<II', b[12:20]); j = json.loads(b[20:20 + jl]); BIN = b[20 + jl + 8:]
    pr = j['meshes'][0]['primitives'][0]
    def acc(i, dt, n):
        a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]; o = v['byteOffset'] + a.get('byteOffset', 0)
        return np.frombuffer(BIN, dt, a['count'] * n, o).reshape(-1, n)
    A = pr['attributes']
    return acc(A['POSITION'], np.float32, 3).astype(float), acc(A['NORMAL'], np.float32, 3).astype(float), acc(A['TEXCOORD_0'], np.float32, 2), acc(pr['indices'], np.uint32, 1).reshape(-1, 3)

# ---- band flower in the strip: bead = top vertices near the centre
P, N, UV, F = glb(strip)
xc, yc = -0.730, 0.0132
for _ in range(4):
    r = np.hypot(P[:, 0] - xc, P[:, 1] - yc); s = r < 0.03; hi = s & (P[:, 2] > np.percentile(P[s, 2], 85)); xc, yc = P[hi, 0].mean(), P[hi, 1].mean()
r = np.hypot(P[:, 0] - xc, P[:, 1] - yc); ann = (r > 0.10) & (r < 0.14) & (P[:, 2] > -0.03); ZF = np.percentile(P[ann, 2], 15)   # window floor height of the band
cen = P[F].mean(axis=1)
# only the flower (bead + petals), not the neighbouring beads / vines: raster of the strip height, connected plateau component of the bead, bead centre = plateau centroid
from scipy import ndimage as ndi
RB = 0.0004; NB = 700; selb = np.hypot(P[:, 0] - xc, P[:, 1] - yc) < 0.20
HB = np.full((NB, NB), ZF - 0.01); ixb = ((P[selb, 0] - xc + NB * RB / 2) / RB).astype(int).clip(0, NB - 1); iyb = ((P[selb, 1] - yc + NB * RB / 2) / RB).astype(int).clip(0, NB - 1)
np.maximum.at(HB, (iyb, ixb), P[selb, 2])
for _ in range(4): HB = np.where(HB > ZF - 0.0099, HB, ndi.maximum_filter(HB, 3))
gb = (np.arange(NB) + .5) * RB - NB * RB / 2; GBU, GBZ = np.meshgrid(gb, gb); cu = cz = 0.0
for R_ in [0.13] * 3 + [0.12] * 6:
    m_ = (np.hypot(GBU - cu, GBZ - cz) < R_) & (HB > ZF + 0.03); lab, _n = ndi.label(m_); l_ = lab[int(NB / 2 + cz / RB), int(NB / 2 + cu / RB)]; mm = lab == l_ if l_ else m_; cu, cz = GBU[mm].mean(), GBZ[mm].mean()
xc += cu; yc += cz
HBm = ndi.binary_closing(HB > ZF + 0.012, iterations=3); _h, _hn = ndi.label(ndi.binary_fill_holes(HBm) & ~HBm); _sz = ndi.sum(np.ones_like(_h), _h, range(1, _hn + 1)); HBm |= np.isin(_h, 1 + np.where(_sz < 1500)[0])   # fill the small holes only (raster gaps inside the petals), not the gaps between petal tips and the rails      # petal mask (holes of the raster closed, gaps to the rails / beads NOT bridged)
NAB = 180; RPb = np.zeros(NAB)                      # petal outline: walk out from the bead until the mask ends; no end before the cap (touching a rail / bead / vine) -> fixed radius RBV; polar median + +-10 deg max filter
RBC = float(os.environ.get('RBC', 0.135)); RBV = float(os.environ.get('RBV', 0.11))
for k in range(NAB):
    a_ = 2 * np.pi * k / NAB; rs = np.arange(0.03, RBC + 1e-9, 0.0008); hb_ = HBm[((cz + rs * np.sin(a_) + NB * RB / 2) / RB).astype(int).clip(0, NB - 1), ((cu + rs * np.cos(a_) + NB * RB / 2) / RB).astype(int).clip(0, NB - 1)]
    i_ = first_run(~hb_); RPb[k] = rs[i_] if i_ is not None else RBV
RPb = ndi.maximum_filter(ndi.median_filter(RPb, size=3, mode='wrap'), size=11, mode='wrap') + 0.010; RPET = RPb.max()
print('  band petal outline radius per 30 deg:', np.round(RPb[::15], 3).tolist())
cxb = (cen[:, 0] - (xc - cu)); cyb = (cen[:, 1] - (yc - cz)); ab = np.arctan2(cyb, cxb) % (2 * np.pi); rb_ = np.hypot(cxb, cyb)
petal = None
keep = (rb_ <= np.interp(ab, 2 * np.pi * np.arange(NAB + 1) / NAB, np.r_[RPb, RPb[0]])) & (np.abs(cyb) <= float(os.environ.get('YMAX', 0.105))) & (P[F][:, :, 2].min(axis=1) > ZF + 0.005)   # |y| clip: the rails of the strip start at y 0.1075, the petal tips end at 0.1025
print('band flower: bead centre shifted by %.4f %.4f, petal component radius %.4f (x S %.2f = %.4f)' % (cu, cz, RPET, S, RPET * S))
f = F[keep]; used, inv = np.unique(f, return_inverse=True); f = inv.reshape(-1, 3)
bp, bn, buv = P[used], N[used], UV[used]
print('band flower centre %.4f %.4f floor z %.4f bead z %.4f; patch tris %d verts %d' % (xc, yc, ZF, P[hi, 2].mean(), len(f), len(bp)))

# ---- solitaire
SP, _, SUV, _ = glb(sol)
import io; from PIL import Image
_b = open(sol, 'rb').read(); _jl, _ = struct.unpack('<II', _b[12:20]); _j = json.loads(_b[20:20 + _jl]); _bv = _j['bufferViews'][_j['images'][_j['textures'][_j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]['bufferView']]
TEX = np.asarray(Image.open(io.BytesIO(_b[20 + _jl + 8:][_bv['byteOffset']:_bv['byteOffset'] + _bv['byteLength']])).convert('RGB'))   # solitaire base colour texture
X = SP[:, 0] - CX; Y = SP[:, 1] - CY; Z = SP[:, 2]; rho = np.hypot(X, Y); th = np.arctan2(X, Y)
V, NN, UU, FF = [], [], [], []; FV, FN, FU, FF2 = [], [], [], []; cuts = []; base = 0; fbase = 0
import base64
for (sg, u0, z0), rot in zip(FLOWERS, ROT):
    t = sg * th
    NC = 480; RC = 0.0006; selc = (np.hypot(R0 * t - u0, Z - z0) < 0.18) & (rho > 0.70)      # flower centre = centroid of the plateau (rho > 0.835) component around the start guess, iterated
    HC = np.zeros((NC, NC)); ixc = ((R0 * t[selc] - u0 + NC * RC / 2) / RC).astype(int).clip(0, NC - 1); izc = ((Z[selc] - z0 + NC * RC / 2) / RC).astype(int).clip(0, NC - 1); np.maximum.at(HC, (izc, ixc), rho[selc])
    for _ in range(4): HC = np.where(HC > 0, HC, ndi.maximum_filter(HC, 3))
    gc = (np.arange(NC) + .5) * RC - NC * RC / 2; GCU, GCZ = np.meshgrid(gc, gc); cu = cz = 0.0
    for R_ in [0.10] * 3 + [0.085] * 8:
        m_ = (np.hypot(GCU - cu, GCZ - cz) < R_) & (HC > 0.835); lab, _n = ndi.label(m_); l_ = lab[int(NC / 2 + cz / RC), int(NC / 2 + cu / RC)]; mm = lab == l_ if l_ else m_; cu, cz = GCU[mm].mean(), GCZ[mm].mean()
    print('  centre moved by %.4f %.4f from the start guess' % (cu, cz)); u0 += cu; z0 += cz
    rr = np.hypot(R0 * t - u0, Z - z0); ann = (rr > 0.10) & (rr < 0.15) & (rho > 0.74)
    ua, za, ra = (R0 * t - u0)[ann], (Z - z0)[ann], rho[ann]; w = np.ones(len(ra), bool)
    for _ in range(6):                                   # plane fit rho = c0 + c1 u + c2 z of the window floor (robust: the low half of the points)
        M = np.c_[np.ones(w.sum()), ua[w], za[w]]; c = np.linalg.lstsq(M, ra[w], rcond=None)[0]; res = ra - (c[0] + c[1] * ua + c[2] * za); w = res < np.percentile(res, 50)
    # footprint of the solitaire flower: height raster, star-shaped walk out from the bead
    RES = 0.0008; NR = 360; sel = rr < 0.13; du_, dz_ = (R0 * t - u0)[sel], (Z - z0)[sel]; hh_ = rho[sel]
    ix = ((du_ + NR * RES / 2) / RES).astype(int).clip(0, NR - 1); iz = ((dz_ + NR * RES / 2) / RES).astype(int).clip(0, NR - 1)
    H = np.full((NR, NR), 0.0); np.maximum.at(H, (iz, ix), hh_)
    for _ in range(4): H = np.where(H > 0, H, ndi.maximum_filter(H, 3))
    gu = (np.arange(NR) + 0.5) * RES - NR * RES / 2; GU, GZ = np.meshgrid(gu, gu); thrm = c[0] + c[1] * GU + c[2] * GZ + 0.016
    NA = 120; Rp = np.zeros(NA)
    for k in range(NA):
        a = 2 * np.pi * k / NA; rs = np.arange(0.032, RMAX + 1e-9, 0.001); pu = rs * np.cos(a); pz = rs * np.sin(a)
        hi_ = H[((pz + NR * RES / 2) / RES).astype(int).clip(0, NR - 1), ((pu + NR * RES / 2) / RES).astype(int).clip(0, NR - 1)]
        th_ = c[0] + c[1] * pu + c[2] * pz + 0.016; i_ = first_run(hi_ < th_); Rp[k] = rs[i_] if i_ is not None else RVINE
    Rp = np.maximum(Rp, 0.032); Rp = ndi.maximum_filter(ndi.median_filter(Rp, size=3, mode='wrap'), size=7, mode='wrap')   # median drops 1-sample spikes, then a +-18 deg max filter so the gaps between petals are cut as far as the neighbouring petals (no petal remnants left)
    GR = np.hypot(GU, GZ); GA = np.arctan2(GZ, GU) % (2 * np.pi); Rg = np.interp(GA, 2 * np.pi * np.arange(NA + 1) / NA, np.r_[Rp, Rp[0]])
    mask = GR <= Rg; mask = ndi.binary_dilation(mask, structure=np.ones((3, 3), bool), iterations=max(1, int(round(DIL / RES))))
    MR = 2; mask_s = mask[::1, ::1]
    # down-sample the mask to 0.0016 for the bit raster
    m2 = mask.reshape(NR // 2, 2, NR // 2, 2).any(axis=(1, 3)); RES2 = RES * 2
    print('  footprint radius per 30 deg:', np.round(Rp[::10], 3).tolist(), ' mask pixels', int(m2.sum()))
    print('side %+d  bead centre u %.4f z %.4f (th %.2f deg)  floor rho %.4f slope (%.3f, %.3f)' % (sg, u0, z0, np.degrees(u0 / R0), c[0], c[1], c[2]))
    th_c = u0 / R0                                       # signed angle of the centre (sg*th)
    dx, dy = (bp[:, 0] - xc) * S, (bp[:, 1] - yc) * S; a_, b_ = np.cos(np.radians(rot)), np.sin(np.radians(rot)); lx, ly = a_ * dx - b_ * dy, b_ * dx + a_ * dy
    def world(sgn_u):                                    # sgn_u=+1: band x -> +phi (phi = sg*th); -1: band x -> -phi.  Right-handedness is checked below.
        uu = sgn_u * lx; ph = th_c + uu / R0; rh = c[0] + c[1] * uu + c[2] * ly + SZ * (bp[:, 2] - ZF) - SINK; thv = sg * ph
        return np.c_[CX + rh * np.sin(thv), CY + rh * np.cos(thv), z0 + ly], thv
    pos, thv = world(1)
    # handedness: world images of band x,y,z at the centre
    e = 1e-3; th0 = sg * th_c; rad = np.array([np.sin(th0), np.cos(th0), 0]); tan = np.array([np.cos(th0), -np.sin(th0), 0]) * sg   # d(world)/d(phi)
    det = np.dot(np.cross(tan, [0, 0, 1]), rad)           # frame (phi, z, radial)
    su = 1 if det > 0 else -1
    pos, thv = world(su); print('  handedness det %+.0f -> band x -> %s phi' % (det, '+' if su > 0 else '-'))
    # normals: inverse-transpose of the (xy scale S, height scale SZ) then rotate into (phi-direction, z, radial)
    nl = np.c_[bn[:, 0] / S, bn[:, 1] / S, bn[:, 2] / SZ]; nl[:, 0], nl[:, 1] = a_ * nl[:, 0] - b_ * nl[:, 1], b_ * nl[:, 0] + a_ * nl[:, 1]
    rv = np.c_[np.sin(thv), np.cos(thv), np.zeros(len(thv))]; tv = np.c_[np.cos(thv), -np.sin(thv), np.zeros(len(thv))] * sg * su   # direction of +band-x in world
    nw = nl[:, [0]] * tv + nl[:, [1]] * np.array([0, 0, 1.0]) + nl[:, [2]] * rv; nw /= np.linalg.norm(nw, axis=1, keepdims=True)
    ff = f if True else f[:, ::-1]
    fn = np.cross(pos[ff[:, 1]] - pos[ff[:, 0]], pos[ff[:, 2]] - pos[ff[:, 0]]); vn = nw[ff].sum(axis=1); sgn = (fn * vn).sum(axis=1)
    print('  face normal vs vertex normal agree: %.1f%%' % (100 * (sgn > 0).mean()))
    if (sgn > 0).mean() < 0.5: ff = ff[:, ::-1]
    V.append(pos); NN.append(nw); UU.append(buv); FF.append(ff + base); base += len(pos)
    # flat floor disc under the cut (rings x segments), constant UV of a solitaire floor vertex
    Rd = np.interp(2 * np.pi * np.arange(NSEG := 48) / NSEG, 2 * np.pi * np.arange(NA + 1) / NA, np.r_[Rp, Rp[0]]) + DIL + 0.004   # disc outline = the footprint (so no flat sheet sticks out past the cut)
    fr = np.linspace(0, 1, 13); dpts = [(0.0, 0.0)] + [(fr_ * Rd[s_] * np.cos(2 * np.pi * s_ / NSEG), fr_ * Rd[s_] * np.sin(2 * np.pi * s_ / NSEG)) for fr_ in fr[1:] for s_ in range(NSEG)]; dtri = [(0, 1 + s_, 1 + (s_ + 1) % NSEG) for s_ in range(NSEG)]
    for r_ in range(1, 12):
        for s_ in range(NSEG):
            a0 = 1 + (r_ - 1) * NSEG + s_; a1 = 1 + (r_ - 1) * NSEG + (s_ + 1) % NSEG; b0 = 1 + r_ * NSEG + s_; b1 = 1 + r_ * NSEG + (s_ + 1) % NSEG; dtri += [(a0, b0, b1), (a0, b1, a1)]
    dpts = np.array(dpts); dtri = [(0, 1 + s_, 1 + (s_ + 1) % NSEG) for s_ in range(NSEG)]
    for r_ in range(1, 12):
        for s_ in range(NSEG):
            a0 = 1 + (r_ - 1) * NSEG + s_; a1 = 1 + (r_ - 1) * NSEG + (s_ + 1) % NSEG; b0 = 1 + r_ * NSEG + s_; b1 = 1 + r_ * NSEG + (s_ + 1) % NSEG; dtri += [(a0, b0, b1), (a0, b1, a1)]
    dtri = np.array(dtri); uu = dpts[:, 0]; ph = th_c + uu / R0; rh = c[0] + c[1] * uu + c[2] * dpts[:, 1] - DSINK; thv2 = sg * ph
    dpos = np.c_[CX + rh * np.sin(thv2), CY + rh * np.cos(thv2), z0 + dpts[:, 1]]; dn = np.c_[np.sin(thv2), np.cos(thv2), np.zeros(len(thv2))]
    fn2 = np.cross(dpos[dtri[:, 1]] - dpos[dtri[:, 0]], dpos[dtri[:, 2]] - dpos[dtri[:, 0]]); 
    if (fn2 * dn[dtri].sum(axis=1)).sum() < 0: dtri = dtri[:, ::-1]
    fn2 = np.cross(dpos[dtri[:, 1]] - dpos[dtri[:, 0]], dpos[dtri[:, 2]] - dpos[dtri[:, 0]]); dn = np.tile(fn2.sum(axis=0) / np.linalg.norm(fn2.sum(axis=0)), (len(dpos), 1))   # the disc is the tilted window-floor plane: its normal is the plane normal, not the radial direction (4 deg off -> a bright mirror reflection, the pale plate)
    fl = np.where((rr > 0.11) & (rr < 0.16) & (rho > 0.74) & (rho < c[0] + c[1] * (R0 * t - u0) + c[2] * (Z - z0) + 0.004))[0]; cols = TEX[(SUV[fl, 1] * (TEX.shape[0] - 1)).astype(int), (SUV[fl, 0] * (TEX.shape[1] - 1)).astype(int)].astype(float); k0 = fl[np.argmin(np.abs(cols - np.median(cols, axis=0)).sum(axis=1))]   # floor vertex whose texture colour is the median of the window floor
    FV.append(dpos); FN.append(dn); FU.append(np.tile(SUV[k0], (len(dpos), 1))); FF2.append(dtri + fbase); fbase += len(dpos)
    cuts.append({'sgn': sg, 'u': round(u0, 4), 'z': round(z0, 4), 'f': [round(c[0] + DH, 4), round(c[1], 4), round(c[2], 4)], 'n': NR // 2, 'res': RES2, 'm': base64.b64encode(np.packbits(m2.ravel())).decode()})   # cut triangles whose centroid (du, dz) is in the mask and rho > f0 + f1*du + f2*dz
V = np.vstack(V).astype(np.float32); NN = np.vstack(NN).astype(np.float32); UU = np.vstack(UU).astype(np.float32); FF = np.vstack(FF).astype(np.uint32)
print('CUTS =', json.dumps(cuts), ' R0 =', R0)
FV = np.vstack(FV).astype(np.float32); FN = np.vstack(FN).astype(np.float32); FU = np.vstack(FU).astype(np.float32); FF2 = np.vstack(FF2).astype(np.uint32)

# ---- write GLB: node 'relief' (band UVs) + node 'floor' (solitaire UV); dummy materials (the viewer picks the band material / the solitaire material)
arrs = [V, NN, UU, FF, FV, FN, FU, FF2]; blobs = [a.tobytes() for a in arrs]; offs = []; o = 0
for bl in blobs: offs.append(o); o += len(bl)
BIN = b''.join(blobs); BIN += b'\0' * (-len(BIN) % 4)
acc_ = []
for k, a in enumerate(arrs):
    if k % 4 == 3: acc_.append({'bufferView': k, 'componentType': 5125, 'count': a.size, 'type': 'SCALAR'})
    else: acc_.append({'bufferView': k, 'componentType': 5126, 'count': len(a), 'type': ['VEC3', 'VEC3', 'VEC2'][k % 4], **({'min': a.min(0).tolist(), 'max': a.max(0).tolist()} if k % 4 == 0 else {})})
j = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0, 1]}], 'nodes': [{'name': 'relief', 'mesh': 0}, {'name': 'floor', 'mesh': 1}],
     'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3, 'mode': 4, 'material': 0}]}, {'primitives': [{'attributes': {'POSITION': 4, 'NORMAL': 5, 'TEXCOORD_0': 6}, 'indices': 7, 'mode': 4, 'material': 0}]}],
     'materials': [{'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 1, 'roughnessFactor': 0.5}, 'doubleSided': True}],
     'buffers': [{'byteLength': len(BIN)}],
     'bufferViews': [{'buffer': 0, 'byteOffset': offs[i], 'byteLength': len(blobs[i]), 'target': 34963 if i % 4 == 3 else 34962} for i in range(8)], 'accessors': acc_}
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
open(out, 'wb').write(b'glTF' + struct.pack('<II', 2, 12 + 8 + len(js) + 8 + len(BIN)) + struct.pack('<I', len(js)) + b'JSON' + js + struct.pack('<I', len(BIN)) + b'BIN\0' + BIN)
print('wrote', out, os.path.getsize(out), 'bytes')
