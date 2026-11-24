import sys, numpy as np, trimesh
from collections import defaultdict
path, Ri, name = sys.argv[1], float(sys.argv[2]), sys.argv[3]
m = trimesh.load(path, process=False)
V = np.asarray(m.vertices, float); F = np.asarray(m.faces)
r = np.hypot(V[:,0], V[:,1])
P = V[F]; e1 = P[:,1]-P[:,0]; e2 = P[:,2]-P[:,0]
cr = np.cross(e1, e2); A = 0.5*np.linalg.norm(cr, axis=1)
fn = cr/np.maximum(np.linalg.norm(cr,axis=1),1e-30)[:,None]
def ar(P):  # aspect = longest edge^2 / (2*area)  (equilateral ~1.15)
    a = np.linalg.norm(P[:,1]-P[:,0],axis=1); b = np.linalg.norm(P[:,2]-P[:,1],axis=1); c = np.linalg.norm(P[:,0]-P[:,2],axis=1)
    L = np.maximum(np.maximum(a,b),c)
    return L, L*L/np.maximum(np.linalg.norm(np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]),axis=1),1e-30)
zmax, zmin = V[:,2].max(), V[:,2].min()
print('==', name, 'Ri', Ri, 'z', round(zmin,4), round(zmax,4))
vn = np.zeros_like(V)  # area-weighted vertex normals (three.js computeVertexNormals)
for k in range(3): np.add.at(vn, F[:,k], cr)
vn /= np.maximum(np.linalg.norm(vn,axis=1),1e-30)[:,None]
onb = np.abs(r-Ri) < 2e-3
bs = onb[F].all(1)
print('bore strip tris', bs.sum(), 'area %.2f mm2' % A[bs].sum())
cen = P.mean(1); rh = np.stack([cen[:,0],cen[:,1],np.zeros(len(F))],1); rh /= np.linalg.norm(rh,axis=1)[:,None]
dev = np.degrees(np.arccos(np.clip(np.abs((fn*rh).sum(1)),0,1)))
print(' bore face normal dev from radial: median %.2f p90 %.2f max %.2f deg' % (np.median(dev[bs]), np.percentile(dev[bs],90), dev[bs].max()))
L, AR = ar(P)
print(' bore aspect: median %.1f p90 %.1f max %.0f ; >20: %d >50: %d ; edge len max %.3f mm' % (np.median(AR[bs]), np.percentile(AR[bs],90), AR[bs].max(), (AR[bs]>20).sum(), (AR[bs]>50).sum(), L[bs].max()))
for zs, nm in ((zmax,'z+'),(zmin,'z-')):
    sel = np.where(onb & (np.abs(V[:,2]-zs)<0.05))[0]
    rh_v = np.stack([V[sel,0],V[sel,1],np.zeros(len(sel))],1); rh_v /= np.linalg.norm(rh_v,axis=1)[:,None]
    ang = np.degrees(np.arccos(np.clip(np.abs((vn[sel]*rh_v).sum(1)),0,1)))
    print(' %s rim verts %d: vertex normal tilt from radial med %.1f p90 %.1f max %.1f deg' % (nm, len(sel), np.median(ang), np.percentile(ang,90), ang.max()))
for zs, nm in ((zmax,'z+'),(zmin,'z-')):
    pl = (np.abs(P[:,:,2]-zs)<0.01).all(1) & (r[F].min(1) < Ri+1.5)
    print(' flange %s tris %d area %.2f mm2; aspect median %.1f p90 %.1f max %.0f; >20: %d >50: %d; longest edge %.3f; area<1e-4 mm2: %d' % (nm, pl.sum(), A[pl].sum(), np.median(AR[pl]), np.percentile(AR[pl],90), AR[pl].max(), (AR[pl]>20).sum(), (AR[pl]>50).sum(), L[pl].max(), (A[pl]<1e-4).sum()))
