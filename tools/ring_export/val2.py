import sys,numpy as np,manifold3d as m3d
d=np.load(sys.argv[1]); P=d['P']; I=d['I']
mf=m3d.Manifold(m3d.Mesh(vert_properties=P.astype(np.float32),tri_verts=I.astype(np.uint32)))
print('manifold3d: status',mf.status(),'| genus',mf.genus(),'| vol %.3f mm3 | area %.2f mm2 | empty %s'%(mf.volume(),mf.surface_area(),mf.is_empty()))
zs=np.linspace(P[:,2].min()+1e-4,P[:,2].max()-1e-4,1200); a=np.array([mf.slice(float(z)).area() for z in zs])
v=np.trapezoid(a,zs); print('z-slice integral volume %.3f mm3 (slices 1200)'%v)
