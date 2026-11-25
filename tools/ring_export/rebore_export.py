import sys, numpy as np, trimesh
name, Ri = sys.argv[1], float(sys.argv[2])
fn = {'wide':'wide_band_ring_nostone','band':'band_ring_nostone'}[name]
d = np.load('out/%s_merged.npz'%name); V,F = d['V'],d['F']
m = trimesh.Trimesh(V,F,process=False); m.remove_unreferenced_vertices()
print(name,'verts',len(m.vertices),'tris',len(m.faces),'bodies',m.body_count,'watertight',m.is_watertight,'winding',m.is_winding_consistent,'euler',m.euler_number,'vol %.4f'%m.volume)
b=m.bounds; print(' inner dia check: min r %.4f'%np.hypot(m.vertices[:,0],m.vertices[:,1]).min(),'z',b[0,2].round(4),b[1,2].round(4))
m.export('out/%s.stl'%fn); m.export('out/%s.obj'%fn)
g = np.load('out/%s_glb.npz'%name); mg = trimesh.Trimesh(g['V'],g['F'],process=False); mg.remove_unreferenced_vertices(); mg.export('out/%s.glb'%fn)
import os; print(' sizes MB', {e: round(os.path.getsize('out/%s.%s'%(fn,e))/1e6,1) for e in ('stl','obj','glb')})
# emulate three.js computeVertexNormals on the GLB mesh (indexed, area-weighted) and measure rim vertices
V2=np.asarray(mg.vertices); F2=np.asarray(mg.faces); P=V2[F2]; cr=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0])
vn=np.zeros_like(V2)
for k in range(3): np.add.at(vn,F2[:,k],cr)
vn/=np.maximum(np.linalg.norm(vn,axis=1),1e-30)[:,None]
r=np.hypot(V2[:,0],V2[:,1]); rim=np.abs(r-Ri)<0.02
rh=np.stack([V2[:,0],V2[:,1],np.zeros(len(V2))],1); rh/=np.linalg.norm(rh,axis=1)[:,None]
tilt=np.degrees(np.arccos(np.clip(np.abs((vn*rh).sum(1)),0,1)))
bore_used=np.unique(F2[-int(sys.argv[3]):]) if len(sys.argv)>3 else None
print(' GLB rim-station normals: bore verts tilt from radial max %.2f deg (n=%d); flange rim verts tilt from axial max %.2f deg'%(
  tilt[bore_used].max(), len(bore_used), np.degrees(np.arccos(np.clip(np.abs(vn[np.setdiff1d(np.where(rim)[0],bore_used),2]),0,1))).max()))
