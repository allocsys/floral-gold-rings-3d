# Smooth ONLY the two flower reliefs of site/solitaire2_sym.glb (Solitaire 3, step 1), everything else untouched.
# usage: python3 tools/meshy/smooth_flowers.py IN.glb OUT.glb [CX CZ R_FULL R_FEATHER ITERS]   (flowers at x=+-CX, z=CZ, model units)
# 1 weld duplicate (UV-seam) vertices by rounded position; 2 Taubin smoothing (lambda 0.5 / mu -0.53, volume preserving) weighted by a cosine feather: weight 1 inside R_FULL (xz distance to the flower centre, only vertices with y>0.3 = outer side), 0 beyond R_FEATHER
# 3 recompute smooth normals from the new geometry for vertices with weight>0 (others keep the original); 4 patch POSITION/NORMAL bytes in place; textures/UVs/indices byte-identical. Prints roughness before/after.
import sys, json, struct, numpy as np, scipy.sparse as sp
src, dst = sys.argv[1], sys.argv[2]
CX, CZ, RF, RE, IT = [float(v) for v in sys.argv[3:8]] if len(sys.argv) > 7 else (0.515, 0.0, 0.13, 0.19, 12)
IT = int(IT)
b = open(src, 'rb').read(); jl, _ = struct.unpack('<II', b[12:20]); j = json.loads(b[20:20 + jl]); BIN = bytearray(b[20 + jl + 8:])
def view(i):
    a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]; o = v['byteOffset'] + a.get('byteOffset', 0); return a, o
def acc(i, dt, n):
    a, o = view(i); return np.frombuffer(BIN, dt, a['count'] * n, o).reshape(-1, n)
P = acc(0, np.float32, 3).astype(np.float64); N = acc(2, np.float32, 3).astype(np.float64); F = acc(3, np.uint32, 1).reshape(-1, 3)
u, wid = np.unique(np.round(P, 5), axis=0, return_inverse=True); wid = wid.ravel(); nw = len(u)
WP = np.zeros((nw, 3)); WP[wid] = P                                     # welded positions (exact, first-write)
WF = wid[F]; WF = WF[(WF[:, 0] != WF[:, 1]) & (WF[:, 1] != WF[:, 2]) & (WF[:, 0] != WF[:, 2])]
E = np.vstack([WF[:, [0, 1]], WF[:, [1, 2]], WF[:, [2, 0]]]); A = sp.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(nw, nw)).tocsr(); A = ((A + A.T) > 0).astype(float)
deg = np.asarray(A.sum(1)).ravel(); deg[deg == 0] = 1
def lap(X): return (A @ X) / deg[:, None] - X
# weight: both flowers, cosine feather on xz distance
d = np.minimum(np.hypot(WP[:, 0] - CX, WP[:, 2] - CZ), np.hypot(WP[:, 0] + CX, WP[:, 2] - CZ))
w = np.clip((RE - d) / (RE - RF), 0, 1); w = 0.5 - 0.5 * np.cos(np.pi * w)
w = w * (WP[:, 1] > 0.3)                                                # flowers are on the +y (outer top) side only: the ring's opposite side at the same x,z stays untouched
inn = (d < RF) & (WP[:, 1] > 0.3)
def rough(X): return np.linalg.norm(lap(X)[inn], axis=1).mean()
r0 = rough(WP); X = WP.copy()
for _ in range(IT):
    X += 0.5 * w[:, None] * lap(X); X += -0.53 * w[:, None] * lap(X)
disp = np.linalg.norm(X - WP, axis=1)
print('welded verts', nw, 'in flower discs', int(inn.sum()), 'feathered', int((w > 0).sum()))
print('roughness (mean |umbrella laplacian|) in flower: before %.6f after %.6f  (%.1f%%)' % (r0, rough(X), 100 * rough(X) / r0))
print('displacement: mean %.5f max %.5f model units (flower radius ~0.12)' % (disp[w > 0].mean(), disp.max()))
# normals from new geometry (area weighted) for the touched vertices
def vnorm(Pw):
    t = Pw[WF]; fn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); nn = np.zeros((nw, 3))
    for k in range(3): np.add.at(nn, WF[:, k], fn)
    return nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-20)
NW = vnorm(X); NW0 = vnorm(WP); touched = w > 0
cosd = (NW[touched] * NW0[touched]).sum(1); print('normal change: mean %.2f deg max %.2f deg' % (np.degrees(np.arccos(np.clip(cosd, -1, 1))).mean(), np.degrees(np.arccos(np.clip(cosd, -1, 1))).max()))
P2 = P.copy(); N2 = N.copy(); tv = touched[wid]
P2[tv] = X[wid[tv]]; N2[tv] = NW[wid[tv]]
# volume (divergence theorem) before/after on the welded mesh
def vol(Pw): t = Pw[WF]; return np.einsum('ij,ij->i', t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6
print('volume before %.6f after %.6f (%.4f%%)' % (vol(WP), vol(X), 100 * (vol(X) / vol(WP) - 1)))
# left/right symmetry of the result (welded, mirrored x)
key = lambda Q: np.lexsort((Q[:, 2], Q[:, 1], np.round(Q[:, 0], 4)))
M = X.copy(); M[:, 0] *= -1; _, ia = np.unique(np.round(WP, 5), axis=0, return_index=True)
from scipy.spatial import cKDTree
dd, _ = cKDTree(X).query(M); print('mirror asymmetry after: max %.6f mean %.7f' % (dd.max(), dd.mean()))
for i, arr in ((0, P2), (2, N2)):
    a, o = view(i); BIN[o:o + a['count'] * 12] = arr.astype(np.float32).tobytes()
    a['min'] = arr.astype(np.float32).min(0).tolist(); a['max'] = arr.astype(np.float32).max(0).tolist()
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4); bb = bytes(BIN)
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bb)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bb), 0x004E4942) + bb
open(dst, 'wb').write(out); print('wrote', dst, len(out))
