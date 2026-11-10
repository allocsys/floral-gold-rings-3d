# Solitaire 4: re-space the 5 petals of each flower of site/solitaire2_sym.glb to an even 72 deg (and equal petal length) by a smooth rotation/scale field in the flower's tangent plane.
# Mesh is only moved (topology, UVs, textures, window/vines untouched); rho (height) of every vertex is kept, only its (arc u, z v) position changes; feathered to zero between r RF and RE.
# usage: python3 tools/meshy/warp_flower.py IN.glb OUT.glb      lobe data = tools/meshy/measure_flower.py output on solitaire2_sym (centre arc s 0.5492 z 0.0073)
import sys, json, struct, numpy as np
src, dst = sys.argv[1], sys.argv[2]
THC, CZ, RG = 0.5492 / 0.8, 0.0073, 0.83
PK = np.array([10., 140., 190., 250., 330.]); RK = np.array([0.112, 0.115, 0.130, 0.107, 0.110])   # measured lobe peak angle (deg in the (u,v) plane) and tip radius
LT = 0.115                                              # target tip radius for all petals
import os
RF, RE, SIG, RB = float(os.environ.get('RF', 0.11)), float(os.environ.get('RE', 0.32)), float(os.environ.get('SIG', 12.0)), 0.03              # full warp inside RF, zero beyond RE; angular blend width (deg); bead radius kept unscaled
d = 72.0 * np.arange(5) - PK; d = (d + 180) % 360 - 180; c = d.mean(); DEL = d - c   # rotation of each lobe: even 72 deg spacing, mean rotation 0
SK = np.where(np.arange(5) == 0, 1.0, LT / RK)          # lobe 0 (10 deg) touches the vine, radius not trustworthy: keep
print('lobe peaks', PK.tolist(), '-> targets', (PK + DEL).tolist(), ' rotations', np.round(DEL, 1).tolist(), ' radius scale', np.round(SK, 3).tolist())
b = open(src, 'rb').read(); jl, _ = struct.unpack('<II', b[12:20]); j = json.loads(b[20:20 + jl]); BIN = bytearray(b[20 + jl + 8:])
def view(i): a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]; return a, v['byteOffset'] + a.get('byteOffset', 0)
def acc(i, dt, n): a, o = view(i); return np.frombuffer(BIN, dt, a['count'] * n, o).reshape(-1, n)
P = acc(0, np.float32, 3).astype(np.float64); N = acc(2, np.float32, 3).astype(np.float64); F = acc(3, np.uint32, 1).reshape(-1, 3)
_, wid = np.unique(np.round(P, 5), axis=0, return_inverse=True); wid = wid.ravel(); nw = wid.max() + 1
WP = np.zeros((nw, 3)); WP[wid] = P
WF = wid[F]; WF = WF[(WF[:, 0] != WF[:, 1]) & (WF[:, 1] != WF[:, 2]) & (WF[:, 0] != WF[:, 2])]
rho = np.hypot(WP[:, 0], WP[:, 1]); sg = np.where(WP[:, 0] >= 0, 1.0, -1.0); th = np.abs(np.arctan2(WP[:, 0], WP[:, 1]))
u = RG * (th - THC); v = WP[:, 2] - CZ; r = np.hypot(u, v); ph = np.degrees(np.arctan2(v, u)) % 360
reg = (WP[:, 1] > 0.3) & (r < RE) & (th > 0.2) & (th < 1.2)
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
f = 1 - ss((r - RF) / (RE - RF))                        # radial feather
import os as _o
HL, HH = float(_o.environ.get('HL', 0)), float(_o.environ.get('HH', 0))
if HH > HL: f = f * ss((rho - HL) / (HH - HL))          # optional height mask: only the raised flower moves, vines/ground (rho low) stay
# angular map: monotone piecewise-linear through (lobe peak -> target), displacement smoothed circularly by SIG deg (no folds as long as slope stays > 0)
o = np.argsort(PK); kx = PK[o]; kd = DEL[o]; ks = SK[o]
kx3 = np.r_[kx - 360, kx, kx + 360]; kd3 = np.r_[kd, kd, kd]; ks3 = np.r_[ks, ks, ks]
gr = np.arange(360.0); gd = np.interp(gr, kx3, kd3); gs = np.interp(gr, kx3, ks3)
kk = np.exp(-0.5 * (np.minimum(gr, 360 - gr) / SIG) ** 2); kk /= kk.sum()
sm = lambda a: np.real(np.fft.ifft(np.fft.fft(a) * np.fft.fft(kk)))
gd, gs = sm(gd), sm(gs); gp = np.r_[gr, 360.0]; gd, gs = np.r_[gd, gd[0]], np.r_[gs, gs[0]]
slope = 1 + np.diff(gd); print('angular map slope min %.2f max %.2f' % (slope.min(), slope.max()))
rot = f * np.interp(ph, gp, gd); scl = 1 + f * ss((r - RB) / 0.02) * (np.interp(ph, gp, gs) - 1)
ph2 = np.radians(ph + rot); r2 = r * scl; u2 = r2 * np.cos(ph2); v2 = r2 * np.sin(ph2)
th2 = THC + u2 / RG; X = WP.copy(); X[:, 0] = sg * rho * np.sin(th2); X[:, 1] = rho * np.cos(th2); X[:, 2] = CZ + v2
X[~reg] = WP[~reg]
print('verts moved', int(reg.sum()), ' max shift %.4f mean %.4f' % (np.linalg.norm(X - WP, axis=1).max(), np.linalg.norm(X - WP, axis=1)[reg].mean()))
def vnorm(Pw):
    t = Pw[WF]; fn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); nn = np.zeros((nw, 3))
    for k in range(3): np.add.at(nn, WF[:, k], fn)
    return nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-20)
NW = vnorm(X); tv = reg[wid]; P2 = P.copy(); N2 = N.copy(); P2[tv] = X[wid[tv]]; N2[tv] = NW[wid[tv]]
def vol(Pw): t = Pw[WF]; return np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6
from scipy.spatial import cKDTree
M = X.copy(); M[:, 0] *= -1; dd, _ = cKDTree(X).query(M)
print('volume %.6f -> %.6f (%+.3f%%)  mirror asymmetry max %.6f' % (vol(WP), vol(X), 100 * (vol(X) / vol(WP) - 1), dd.max()))
# fold check: signed area of triangles in the (u,v) tangent plane must not flip in the edit region
def uv(Pw): t = np.abs(np.arctan2(Pw[:, 0], Pw[:, 1])); return np.c_[RG * (t - THC), Pw[:, 2] - CZ]
def area(Q): a, b_, c_ = Q[WF[:, 0]], Q[WF[:, 1]], Q[WF[:, 2]]; return (b_[:, 0] - a[:, 0]) * (c_[:, 1] - a[:, 1]) - (b_[:, 1] - a[:, 1]) * (c_[:, 0] - a[:, 0])
a0, a1 = area(uv(WP)), area(uv(X)); m = reg[WF].all(1) & (np.abs(a0) > 1e-9) & (WP[WF[:, 0], 1] > 0.3); print('tangent-plane triangle flips in region (sign change of projected area):', int(((a0[m] * a1[m]) < 0).sum()), 'of', int(m.sum()))
for i, arr in ((0, P2), (2, N2)):
    a, o = view(i); BIN[o:o + a['count'] * 12] = arr.astype(np.float32).tobytes(); a['min'] = arr.astype(np.float32).min(0).tolist(); a['max'] = arr.astype(np.float32).max(0).tolist()
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4); bb = bytes(BIN)
open(dst, 'wb').write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bb)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bb), 0x004E4942) + bb); print('wrote', dst)
