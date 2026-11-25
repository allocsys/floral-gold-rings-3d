"""Rebuild the bore strip of a repaired band ring as a clean strip with matched rim stations.
usage: rebore.py in.stl Ri outprefix
 - removes the old bore strip (tris with all 3 verts at r=Ri)
 - inserts vertices on the flange rim edges (ON the existing chord, so geometry is unchanged) at every angle of the other rim
 - builds a new quad strip (2 tris per quad) between the two rim loops, winding consistent
 - writes outprefix_merged.npz (watertight mesh) and outprefix_glb.npz (bore verts duplicated => hard edge for smooth shading)"""
import sys, numpy as np, trimesh
from collections import defaultdict
src, Ri, outp = sys.argv[1], float(sys.argv[2]), sys.argv[3]
TOL = 0.02  # deg
m = trimesh.load(src, process=True)
V = np.asarray(m.vertices, float); F = np.asarray(m.faces).copy()
r = np.hypot(V[:,0], V[:,1]); onb = np.abs(r-Ri) < 2e-3
bs = onb[F].all(1); G = F[~bs]

# collapse micro rim edges (tile-seam steps of 0.6-3.2 um) so no three stations are collinear
MICRO = 0.01; rimids = np.where(onb)[0]; ncol = 0
while True:
    touch0 = np.isin(G, rimids).any(1); Gt = G[touch0]
    hs = set()
    for f in Gt:
        for a,b in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])): hs.add((int(a),int(b)))
    rs = set(rimids.tolist()); cand = [(np.linalg.norm(V[a]-V[b]), a, b) for (a,b) in hs if (b,a) not in hs and a in rs and b in rs]
    cand = [c for c in cand if c[0] < MICRO]
    if not cand: break
    _, a, b = min(cand)
    hit = (G == a).any(1) & (G == b).any(1); assert hit.sum() == 1, hit.sum()
    G = G[~hit]; G[G == b] = a; V[a] = 0.5*(V[a] + V[b]); ncol += 1
print('micro rim edges collapsed:', ncol)
vol0 = m.volume
# boundary half-edges of flange mesh = rim loops
he = set()
for f in G:
    for a,b in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])): he.add((int(a),int(b)))
bd = [(a,b) for (a,b) in he if (b,a) not in he]
nxt = {a:b for a,b in bd}; assert len(nxt)==len(bd)
seen=set(); loops=[]
for s in nxt:
    if s in seen: continue
    L=[s]; seen.add(s); c=nxt[s]
    while c!=s: L.append(c); seen.add(c); c=nxt[c]
    loops.append(L)
assert len(loops)==2
loops.sort(key=lambda L: -V[L,2].mean())   # [z+ loop, z- loop]
rimv = set(v for L in loops for v in L)
# only tris touching the rim are edited
touch = np.isin(G, list(rimv)).any(1)
Tkeep = G[~touch]; T = [tuple(map(int,t)) for t in G[touch]]
D = {}
def reg(i):
    a,b,c = T[i]; D[(a,b)]=i; D[(b,c)]=i; D[(c,a)]=i
def unreg(i):
    a,b,c = T[i]
    for k in ((a,b),(b,c),(c,a)): D.pop(k,None)
for i in range(len(T)): reg(i)
Vl = [tuple(v) for v in V]
def ang(v): return np.degrees(np.arctan2(Vl[v][1], Vl[v][0]))
def ordered_ascending(L):
    th = np.degrees(np.unwrap(np.radians([ang(v) for v in L])))
    sig = 1 if th[-1] > th[0] else -1
    return sig, th
def add_vertex_on_chord(a, b, beta):
    pa = np.array(Vl[a]); pb = np.array(Vl[b]); d = np.array([np.cos(np.radians(beta)), np.sin(np.radians(beta))])
    cx = lambda p,q: p[0]*q[1]-p[1]*q[0]
    t = -cx(pa[:2], d) / cx((pb-pa)[:2], d)
    assert -1e-9 <= t <= 1+1e-9, t
    Vl.append(tuple(pa + t*(pb-pa))); return len(Vl)-1
def split_edge(a, b, pts):   # directed flange edge a->b, pts ordered from a to b
    i = D[(a,b)]; t = T[i]
    k = t.index(a); assert t[(k+1)%3]==b; c = t[(k+2)%3]
    unreg(i)
    chain = [a]+pts+[b]
    new = [(chain[j], chain[j+1], c) for j in range(len(chain)-1)]
    T[i] = new[0]; reg(i)
    for nt in new[1:]:
        T.append(nt); reg(len(T)-1)
def stations_after_insert(L, other_angles):
    """insert on loop L (ordered list of vertex ids, directed as flange) a vertex at every angle in other_angles that has no vertex of L within TOL"""
    sig, th = ordered_ascending(L)
    w = sig*th; w0 = w[0]
    own = np.mod(th, 360)
    def near(beta):
        d = np.abs((own - np.mod(beta,360) + 180) % 360 - 180); return d.min() <= TOL
    cat = np.append(w, w0+360)
    ins = defaultdict(list)   # edge index -> list of (w, beta)
    done = []
    for beta in sorted(set(np.round(other_angles, 6))):
        if near(beta): continue
        if any(abs(((beta-q+180)%360)-180) <= TOL for q in done): continue
        done.append(beta)
        wb = sig*beta; wb = w0 + ((wb - w0) % 360)
        e = int(np.searchsorted(cat, wb, 'right')-1); assert 0 <= e < len(L)
        ins[e].append((wb, beta))
    newL = []; n = len(L)
    for e in range(n):
        a = L[e]; b = L[(e+1)%n]
        pts=[]
        for wb,beta in sorted(ins.get(e,[])):
            pts.append(add_vertex_on_chord(a,b,beta))
        if pts: split_edge(a,b,pts)
        newL.append(a); newL.extend(pts)
    return newL
A, B = loops
angA = [ang(v) for v in A]; angB = [ang(v) for v in B]
nA0, nB0 = len(A), len(B)
A2 = stations_after_insert(A, angB)
B2 = stations_after_insert(B, angA)
print('rim stations: A %d -> %d, B %d -> %d' % (nA0, len(A2), nB0, len(B2)))
# to ascending angle order
def asc(L):
    sig, th = ordered_ascending(L)
    return (L if sig==1 else L[::-1])
Aa, Ba = asc(A2), asc(B2)
# rotate so both start at the station with the smallest angle mod 360 starting at angle of Aa[0]
def rot_to(L, a0):
    th = np.mod([ang(v) for v in L], 360); d = np.abs((th - a0 + 180) % 360 - 180)
    k = int(np.argmin(d)); assert d[k] <= TOL, d[k]
    # if several within TOL (dup cluster) choose the first in ascending order
    idx = [j for j in range(len(L)) if d[j] <= TOL]
    # choose the one that has no predecessor within TOL (cluster start)
    for j in idx:
        pj = (j-1) % len(L)
        if d[pj] > TOL: k=j; break
    return L[k:]+L[:k]
Aa = rot_to(Aa, np.mod(ang(Aa[0]),360)); Ba = rot_to(Ba, np.mod(ang(Aa[0]),360))
nA, nB = len(Aa), len(Ba)
def sa(L, i):  # unwrapped ascending angle of station i
    th = np.degrees(np.unwrap(np.radians([ang(v) for v in L]))); return th
wA = sa(Aa,0); wB = sa(Ba,0)
wA = wA - wA[0] + 0.0; wB = wB - wB[0] + (np.mod(ang(Ba[0]),360) - np.mod(ang(Aa[0]),360)); 
# walk
i=j=0; tris=[]
while i < nA or j < nB:
    ai = Aa[i%nA]; bj = Ba[j%nB]
    nai = wA[i+1] if i+1 < nA else 360.0+wA[0]
    nbj = wB[j+1] if j+1 < nB else 360.0+wB[0]
    if i >= nA: adv='B'
    elif j >= nB: adv='A'
    elif abs(nai-nbj) <= TOL: adv='AB'
    elif nai < nbj: adv='A'
    else: adv='B'
    ai1 = Aa[(i+1)%nA]; bj1 = Ba[(j+1)%nB]
    if adv=='AB':
        tris += [(ai,ai1,bj1),(ai,bj1,bj)]; i+=1; j+=1
    elif adv=='A':
        tris += [(ai,ai1,bj)]; i+=1
    else:
        tris += [(ai,bj1,bj)]; j+=1
assert i==nA and j==nB, (i,j,nA,nB)
# orient bore tris vs flange half-edges
Dall = set(D.keys()); 
for t in Tkeep:
    pass
def orient(t):
    a,b,c = t
    for (u,v,w_) in ((a,b,c),(b,c,a),(c,a,b)):
        if (u,v) in Dall: return (v,u,w_)       # flange has u->v, bore needs v->u
        if (v,u) in Dall: return (u,v,w_)
    raise RuntimeError('tri without rim edge')
tris = [orient(t) for t in tris]
tris = [t for t in tris if len(set(t))==3]

# flip zero-area (collinear) bore tris into their neighbour: longest edge u-v of tri (u,v,p), neighbour (v,u,q) -> (p,u,q),(p,q,v)
def area(t):
    a,b,c = [np.array(Vl[k]) for k in t]; return 0.5*np.linalg.norm(np.cross(b-a,c-a))
for it in range(50):
    bad = [i for i,t in enumerate(tris) if area(t) < 1e-9]
    if not bad: break
    E = {}
    for i,t in enumerate(tris):
        E[(t[0],t[1])]=i; E[(t[1],t[2])]=i; E[(t[2],t[0])]=i
    i = bad[0]; t = tris[i]
    cand = []
    for k in range(3):
        u,v,p = t[k], t[(k+1)%3], t[(k+2)%3]
        cand.append((np.linalg.norm(np.array(Vl[u])-np.array(Vl[v])), u,v,p))
    cand.sort(reverse=True)
    for _,u,v,p in cand:
        j = E.get((v,u))
        if j is None: continue
        q = [x for x in tris[j] if x not in (u,v)][0]
        n1, n2 = (p,u,q), (p,q,v)
        if area(n1) > 1e-9 and area(n2) > 1e-9:
            tris[i] = n1; tris[j] = n2; break
    else:
        raise RuntimeError('cannot flip tri %d' % i)
print('flips applied until zero-area gone, remaining zero-area:', sum(area(t) < 1e-9 for t in tris))
Vn = np.array(Vl)
Fn = np.vstack([Tkeep, np.array(T), np.array(tris)]).astype(np.int64)
mm = trimesh.Trimesh(Vn, Fn, process=False)
# ----- checks
print('new bore tris', len(tris), '(old %d)' % bs.sum())
print('watertight', mm.is_watertight, 'winding consistent', mm.is_winding_consistent, 'euler', mm.euler_number, 'volume %.4f (before %.4f, delta %.5f%%)' % (mm.volume, vol0, 100*(mm.volume-vol0)/vol0))
print('components', len(mm.split(only_watertight=False)) if False else mm.body_count)
import manifold3d as M
mf = M.Manifold(M.Mesh(vert_properties=np.asarray(Vn,np.float32), tri_verts=np.asarray(Fn,np.uint32)))
print('manifold3d status', mf.status(), 'genus', mf.genus(), 'vol %.4f' % mf.volume())
# bore tri quality
P = Vn[np.array(tris)]; cr = np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]); A_ = 0.5*np.linalg.norm(cr,axis=1)
Lm = np.max([np.linalg.norm(P[:,k]-P[:,(k+1)%3],axis=1) for k in range(3)],axis=0)
AR = Lm**2/np.maximum(2*A_,1e-30)
print('bore tris: aspect median %.1f p90 %.1f max %.0f ; >50: %d ; min area %.2e mm2 ; zero-area(<1e-9): %d' % (np.median(AR), np.percentile(AR,90), AR.max(), (AR>50).sum(), A_.min(), (A_<1e-9).sum()))
rr = np.hypot(Vn[:,0],Vn[:,1]); print('inserted verts radial dev from Ri: max %.5f mm' % (Ri-rr[len(V):]).max() if len(Vn)>len(V) else '')
np.savez_compressed(outp+'_merged.npz', V=Vn, F=Fn)
# GLB variant: bore tris get their own rim vertices (hard edge for smooth shading)
nbore = len(tris); Fb = Fn[-nbore:].copy(); used = np.unique(Fb)
remap = {int(u): len(Vn)+k for k,u in enumerate(used)}
Fb2 = np.vectorize(remap.get)(Fb)
Vg = np.vstack([Vn, Vn[used]]); Fg = np.vstack([Fn[:-nbore], Fb2])
np.savez_compressed(outp+'_glb.npz', V=Vg, F=Fg)
print('GLB variant verts', len(Vg), 'dup rim verts', len(used))
