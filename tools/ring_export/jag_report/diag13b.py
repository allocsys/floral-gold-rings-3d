import sys, numpy as np, trimesh, json, struct
path, glb, Ri, name = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
m = trimesh.load(path, process=False); V=np.asarray(m.vertices,float); F=np.asarray(m.faces)
r=np.hypot(V[:,0],V[:,1]); th=np.degrees(np.arctan2(V[:,1],V[:,0]))%360
P=V[F]; cr=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0])
vn=np.zeros_like(V)
for k in range(3): np.add.at(vn,F[:,k],cr)
vn/=np.maximum(np.linalg.norm(vn,axis=1),1e-30)[:,None]
onb=np.abs(r-Ri)<2e-3
for zs,nm in ((V[:,2].max(),'z+'),(V[:,2].min(),'z-')):
    sel=np.where(onb&(np.abs(V[:,2]-zs)<0.05))[0]; sel=sel[np.argsort(th[sel])]
    rh=np.stack([V[sel,0],V[sel,1],np.zeros(len(sel))],1); rh/=np.linalg.norm(rh,axis=1)[:,None]
    ang=np.degrees(np.arccos(np.clip(np.abs((vn[sel]*rh).sum(1)),0,1)))
    ax=ang>45
    flips=(ax[1:]!=ax[:-1]).sum()
    print(name,nm,'rim verts',len(sel),'normal closer to AXIAL:',ax.sum(),'(%.0f%%)'%(100*ax.mean()),'| flips radial<->axial:',flips,'| mean gap between flips %.2f deg'%(360/max(flips,1)))
d=open(glb,'rb').read(); jl=struct.unpack('<I',d[12:16])[0]; j=json.loads(d[20:20+jl])
for p in j['meshes'][0]['primitives']: print(name,'GLB attributes:',list(p['attributes'].keys()))
