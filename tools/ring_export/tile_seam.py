"""tile_seam.py SRC_TILE.glb OUT.json  -  stitch data for the Meshy band tile (site/band_meshy_tile.glb), source-tile frame.
The ring is N copies of one tile; tile t's END boundary (x = xmax) meets tile t+1's START boundary (x = xmin) with no shared vertices.
Output (raw GLB vertex indices, valid for any N / width / thickness because only positions are rescaled):
  tris   : zipper triangles joining the END chain of tile t to the START chain of tile t+1 (end verts = x==xmax, start verts = x==xmin)
  nIdx/nrm : corrected vertex normals for every raw vertex sitting on a seam plane (one normal shared by both sides)
Normals: the stored boundary normals are one-sided (median 19 deg, p90 52 deg apart across the seam = the visible step), so each seam vertex
gets the area-weighted face-normal sum over the faces of BOTH sides (own incident faces + mean of the opposite boundary verts' sums within 1.2e-3 in (y,z))."""
import sys, json, numpy as np, trimesh
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
EPS = 1e-6
g = list(trimesh.load(sys.argv[1], force='scene').geometry.values())[0]
V = np.array(g.vertices, float); N = np.array(g.vertex_normals, float); F = np.array(g.faces)
xmin, xmax = V[:, 0].min(), V[:, 0].max(); L = xmax - xmin
key = np.round(V * 1e5).astype(np.int64); _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
nw = len(first); Pw = V[first]; rep = first            # welded id -> representative raw index
Fw = inv[F]; ok = ~((Fw[:, 0] == Fw[:, 1]) | (Fw[:, 1] == Fw[:, 2]) | (Fw[:, 0] == Fw[:, 2])); Fw = Fw[ok]
# body = biggest connected component (the other is the separate bore sheet)
es = np.sort(np.r_[Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]], 1); ue = np.unique(es, axis=0)
nc, lab = connected_components(coo_matrix((np.ones(len(ue)), (ue[:, 0], ue[:, 1])), shape=(nw, nw)), directed=False)
used = np.unique(Fw); cs, cn = np.unique(lab[used], return_counts=True); body = cs[cn.argmax()]
Fb = Fw[lab[Fw[:, 0]] == body]; print('welded verts', nw, 'body tris', len(Fb), 'components', len(cs), 'sizes', cn.tolist())
e = np.r_[Fb[:, [0, 1]], Fb[:, [1, 2]], Fb[:, [2, 0]]]; kk = e[:, 0] * nw + e[:, 1]; rk = e[:, 1] * nw + e[:, 0]
B = e[~np.isin(kk, rk)]                                   # directed boundary edges of the body
isS = lambda a: Pw[a, 0] < xmin + EPS; isE = lambda a: Pw[a, 0] > xmax - EPS
Eend = np.array([b for b in B if isE(b[0]) and isE(b[1])]); Est = np.array([b for b in B if isS(b[0]) and isS(b[1])])
other = [b for b in B if not ((isE(b[0]) and isE(b[1])) or (isS(b[0]) and isS(b[1])))]
print('boundary edges: end', len(Eend), 'start', len(Est), 'other (not on a seam plane)', len(other))
def chains(E):
    nxt = {}
    for a, b in E: nxt.setdefault(a, []).append(b)
    indeg = {}
    for a, b in E: indeg[b] = indeg.get(b, 0) + 1
    used = set(); res = []
    def walk(s):
        path = [s]; v = s
        while True:
            c = [w for w in nxt.get(v, []) if (v, w) not in used]
            if not c: break
            w = c[0]; used.add((v, w))
            if w == s: return path, True
            path.append(w); v = w
        return path, False
    for s in [a for a in nxt if indeg.get(a, 0) == 0]: res.append(walk(s))
    for a in list(nxt):
        if any((a, w) not in used for w in nxt[a]): res.append(walk(a))
    return res
PP = Pw.copy(); PP[[i for i in range(nw) if isS(i)], 0] += L   # start boundary moved onto the end plane
def zipper(A, Bc, P):
    Bw = Bc[::-1]; nA = len(A) - 1; nB = len(Bw) - 1; i = k = 0; tri = []
    while i < nA or k < nB:
        if i < nA and (k >= nB or np.linalg.norm(P[A[i + 1]] - P[Bw[k]]) <= np.linalg.norm(P[A[i]] - P[Bw[k + 1]])):
            tri.append((A[i + 1], A[i], Bw[k])); i += 1
        else:
            tri.append((Bw[k], Bw[k + 1], A[i])); k += 1
    return tri
def join(cs, P, tol=0.003):
    """boundary walks that are broken by a tiny crack (end of one within tol of the start of the next) are joined into one path"""
    cs = list(cs); seq = []
    pred = lambda c: any(c is not o and np.linalg.norm(P[c[0][0]] - P[o[0][-1]]) < tol for o in cs)
    heads = [c for c in cs if not pred(c)] or cs[:1]
    while cs:
        cur = heads.pop(0) if heads else cs[0]
        if cur not in cs: continue
        cs.remove(cur); path = list(cur[0])
        while True:
            nx = [o for o in cs if np.linalg.norm(P[o[0][0]] - P[path[-1]]) < tol]
            if not nx: break
            nx = min(nx, key=lambda o: np.linalg.norm(P[o[0][0]] - P[path[-1]])); cs.remove(nx); path += nx[0]
        seq.append((path, False))
    return seq
Ac = join(chains(Eend), PP); Bc = join(chains(Est), PP); print('joined: ', end='')
print('chains end', [(len(c), cl) for c, cl in Ac], 'start', [(len(c), cl) for c, cl in Bc])
tris = []; usedB = set()
for pa, cla in Ac:
    best = None
    for bi, (pb, clb) in enumerate(Bc):
        if bi in usedB or clb != cla: continue
        d, _ = cKDTree(PP[pb]).query(PP[pa]); m = d.mean()
        if best is None or m < best[0]: best = (m, bi)
    assert best is not None and best[0] < 0.01, ('unmatched chain', len(pa), best)
    usedB.add(best[1]); tris += zipper(pa, Bc[best[1]][0], PP)
assert len(usedB) == len(Bc), 'unmatched start chains'
tris = np.array(tris); print('zipper tris', len(tris))
# degenerate (zero-area in 3D after translation) zipper tris are kept: they are needed for watertightness; area stat only
ar = np.linalg.norm(np.cross(PP[tris[:, 1]] - PP[tris[:, 0]], PP[tris[:, 2]] - PP[tris[:, 0]]), axis=1) / 2
print('zipper tri area (tile units^2): max %.3e, zero-area %d' % (ar.max(), (ar < 1e-14).sum()))
# topology check: add a second tile copy by translation => every body boundary edge must now be paired (seam closed)
Fz = np.r_[Fb, tris]; e = np.r_[Fz[:, [0, 1]], Fz[:, [1, 2]], Fz[:, [2, 0]]]; kk = e[:, 0] * nw + e[:, 1]; rk = e[:, 1] * nw + e[:, 0]
print('open edges in a ring of copies: expected = only non-seam boundary edges ->', int((~np.isin(kk, rk)).sum()) - len(Eend) - len(Est) + 0 * 1, '(end/start edges are paired through the zipper, not directly)')
# which welded verts are seam verts
seamW = np.where(Pw[:, 0] < xmin + EPS)[0].tolist() + np.where(Pw[:, 0] > xmax - EPS)[0].tolist(); seamW = np.array(seamW)
# normals: same recipe as the rest of the mesh (area-weighted sum of the incident face normals = three.js computeVertexNormals), but over the
# faces on BOTH sides of the join: own incident faces + the mean of the incident-face sums of the opposite-side boundary verts within RM of (y,z)
Pf = Pw; cr = np.cross(Pf[Fb[:, 1]] - Pf[Fb[:, 0]], Pf[Fb[:, 2]] - Pf[Fb[:, 0]]); S = np.zeros((nw, 3))
for c in range(3): np.add.at(S, Fb[:, c], cr)
RM = 0.0012; sideS = np.where(Pw[:, 0] < xmin + EPS)[0]; sideE = np.where(Pw[:, 0] > xmax - EPS)[0]
bodyv = np.zeros(nw, bool); bodyv[np.unique(Fb)] = True; sideS = sideS[bodyv[sideS]]; sideE = sideE[bodyv[sideE]]
nrmW = {}; seamW = np.r_[sideS, sideE]
for mine, opp in ((sideS, sideE), (sideE, sideS)):
    tr = cKDTree(Pw[opp][:, 1:])
    for v in mine:
        ids = tr.query_ball_point(Pw[v][1:], RM)
        if not ids: _, k = tr.query(Pw[v][1:]); ids = [int(k)]
        n = S[v] + S[opp[ids]].mean(0)
        if np.linalg.norm(n) > 1e-12: nrmW[v] = n / np.linalg.norm(n)
Nraw_w = N[first]
print('seam welded verts', len(seamW), 'with corrected normal', len(nrmW))
old = N[first][list(nrmW)]; new = np.array(list(nrmW.values())); ang = np.degrees(np.arccos(np.clip((old * new).sum(1), -1, 1)))
print('corrected vs stored normal deg: median %.1f p90 %.1f' % (np.median(ang), np.percentile(ang, 90)))
# band blend (normals only, geometry untouched): the relief itself has a real slope change at the join (heights match, the two tile edges do not carry the same
# petal edges), which lights as a hard line. Interior body verts within BAND of a seam plane get their stored normal eased towards the shared seam normal of the
# nearest seam vertex (same side), weight smoothstep(1 - dx/BAND): 1 at the seam, 0 at BAND, so the lighting changes over ~0.1 mm instead of in one step.
BAND = float(sys.argv[3]) if len(sys.argv) > 3 else 0.012
bandIdx = []; bandNrm = []
Nraw = N
for side, seamIds in (('S', sideS), ('E', sideE)):
    tr = cKDTree(Pw[seamIds]); 
    xs = xmin if side == 'S' else xmax
    for r in range(len(V)):
        if abs(V[r, 0] - xs) >= BAND or abs(V[r, 0] - xs) < EPS: continue
        w = inv[r]
        if not bodyv[w]: continue
        d, k = tr.query(Pw[w]); 
        if d > 0.004: continue
        if Nraw[r] @ nrmW[seamIds[k]] < np.cos(np.radians(30)): continue   # nearest seam vertex is on a different facet (groove/edge): leave this vertex alone
        t = 1 - abs(V[r, 0] - xs) / BAND; f = t * t * (3 - 2 * t)
        n = (1 - f) * Nraw[r] + f * nrmW[seamIds[k]]; nn = np.linalg.norm(n)
        if nn > 1e-9: bandIdx.append(int(r)); bandNrm.append(n / nn)
print('band', BAND, 'blended interior verts', len(bandIdx))
# apply to ALL raw verts at the seam positions (UV-split duplicates)
rawS = np.where((V[:, 0] < xmin + EPS) | (V[:, 0] > xmax - EPS))[0]
nIdx = [int(r) for r in rawS if inv[r] in nrmW]; nrm = np.array([nrmW[inv[r]] for r in nIdx])
nIdx += bandIdx; nrm = np.vstack([nrm, np.array(bandNrm)]) if len(bandIdx) else nrm
# end/start pair angle after correction (same (y,z) neighbour): should be ~0 by construction
out = {'L': L, 'xmin': xmin, 'xmax': xmax, 'tris': [int(rep[v]) for t in tris for v in t], 'nIdx': nIdx, 'nrm': [round(float(x), 5) for x in nrm.ravel()]}
json.dump(out, open(sys.argv[2], 'w'), separators=(',', ':')); print('wrote', sys.argv[2], 'tris', len(tris), 'nIdx', len(nIdx))
