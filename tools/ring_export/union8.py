import sys, numpy as np, manifold3d as m3d, trimesh
from scipy.spatial import cKDTree
src, out = sys.argv[1], sys.argv[2]
d = np.load(src); P = d['P'].astype(np.float64); I = d['I'].astype(np.int64).copy()
def areas(I):
    a, b, c = P[I[:,0]], P[I[:,1]], P[I[:,2]]
    return 0.5*np.linalg.norm(np.cross(b-a, c-a), axis=1)
A = areas(I); zero = np.where(A < 1e-12)[0]
print('zero-area tris', len(zero))
# map directed edge -> tri
def build():
    m = {}
    for t, (x, y, z) in enumerate(I): m[(x,y)] = t; m[(y,z)] = t; m[(z,x)] = t
    return m
em = build(); flipped = 0; dead = set()
for t in zero:
    if t in dead: continue
    v = I[t]; L = [np.linalg.norm(P[v[(k+1)%3]]-P[v[k]]) for k in range(3)]
    k = int(np.argmax(L)); a, b, c = v[k], v[(k+1)%3], v[(k+2)%3]   # long edge a->b, c on it
    n = em.get((b, a))
    if n is None or n in dead: print('no neighbour', t); continue
    nv = I[n]; j = [i for i in range(3) if nv[i] == b][0]
    assert nv[(j+1)%3] == a; d = nv[(j+2)%3]
    t1, t2 = (a, d, c), (d, b, c)
    for tri in (t1, t2):
        aa = 0.5*np.linalg.norm(np.cross(P[tri[1]]-P[tri[0]], P[tri[2]]-P[tri[0]]))
        if aa < 1e-12: print('flip would make new sliver', t); break
    else:
        I[t] = t1; I[n] = t2; dead.add(n); flipped += 1
        for tri_id in (t, n):
            x, y, z = I[tri_id]
            for e in ((x,y),(y,z),(z,x)): em[e] = tri_id
print('flipped', flipped, '| zero-area tris now', int((areas(I) < 1e-12).sum()))
mf = m3d.Manifold(m3d.Mesh(vert_properties=P.astype(np.float32), tri_verts=I.astype(np.uint32)))
print('status', mf.status(), 'genus', mf.genus(), 'vol %.3f' % mf.volume(), 'components', len(mf.decompose()))
u = m3d.Manifold.batch_boolean([mf], m3d.OpType.Add)
m = u.to_mesh(); V = np.asarray(m.vert_properties)[:, :3].astype(np.float64); F = np.asarray(m.tri_verts).astype(np.int64)
tm = trimesh.Trimesh(V, F, process=False)
e = np.sort(tm.edges, axis=1); _, cnt = np.unique(e, axis=0, return_counts=True)
print('result V %d F %d | watertight %s | winding %s | euler %d | volume %.3f | open %d nonmanifold %d | bodies %d' % (len(V), len(F), tm.is_watertight, tm.is_winding_consistent, tm.euler_number, tm.volume, (cnt==1).sum(), (cnt>2).sum(), len(tm.split(only_watertight=False))))
dist, _ = cKDTree(V).query(P[np.unique(I)]); print('max displacement of original verts %.2e mm' % dist.max())
r = np.hypot(V[:,0], V[:,1]); print('inner dia %.3f outer dia %.3f z %.3f..%.3f' % (2*r.min(), 2*r.max(), V[:,2].min(), V[:,2].max()))
np.savez_compressed(out, P=V, I=F)
