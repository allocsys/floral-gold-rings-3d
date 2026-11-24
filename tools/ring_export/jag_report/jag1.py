import sys, numpy as np, trimesh
path, Ri, name = sys.argv[1], float(sys.argv[2]), sys.argv[3]
m = trimesh.load(path, process=False)
V = np.asarray(m.vertices); F = np.asarray(m.faces)
r = np.hypot(V[:,0], V[:,1]); th = (np.degrees(np.arctan2(V[:,1], V[:,0])) % 360)
zmax, zmin = V[:,2].max(), V[:,2].min()
print(name, 'verts', len(V), 'z', round(zmin,4), round(zmax,4))
# bore strip: verts with r ~ Ri
bore = np.abs(r - Ri) < 2e-3
print('bore verts', bore.sum(), 'r range', r[bore].min(), r[bore].max())
for zs, nm in ((zmax,'z+'),(zmin,'z-')):
    sel = bore & (np.abs(V[:,2]-zs) < 0.05)
    t = th[sel]; zz = V[sel,2]; rr = r[sel]
    print(nm, 'n', sel.sum(), 'z mean %.4f std %.4f min %.4f max %.4f' % (zz.mean(), zz.std(), zz.min(), zz.max()),
          'r dev max %.5f' % np.abs(rr-Ri).max())
# wider look: flange face verts (|z| within .06 of the face plane) with r from Ri..Ri+0.6
for zs, nm in ((zmax,'z+'),(zmin,'z-')):
    sel = (np.abs(V[:,2]-zs) < 0.03) & (r < Ri+0.6)
    zz = V[sel,2]
    print(nm, 'flange-face verts r<Ri+.6:', sel.sum(), 'z spread %.4f..%.4f' % (zz.min(), zz.max()))
