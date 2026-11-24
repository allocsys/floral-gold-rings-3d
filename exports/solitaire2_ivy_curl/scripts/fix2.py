import json,base64,numpy as np,collections
r=json.load(open('/tmp/export.json'))
p=np.frombuffer(base64.b64decode(r['gold']['p']),np.float32).reshape(-1,3).astype(np.float64)
i=np.frombuffer(base64.b64decode(r['gold']['i']),np.uint32).reshape(-1,3)
def vol(P,F): t=P[F]; return np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
def edges(F):
    e=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); es=np.sort(e,axis=1); u,inv,c=np.unique(es,axis=0,return_inverse=True,return_counts=True); return e,u,inv.ravel(),c
def stats(P,F,tag):
    e,u,inv,c=edges(F); d=collections.Counter(map(tuple,e)); dup=sum(1 for v in d.values() if v>1)
    print(f'{tag}: verts {len(P)} tris {len(F)} open {(c==1).sum()} nonmanifold {(c>2).sum()} dup-directed-edges {dup} volume {vol(P,F):.3f}')
# 1 weld + drop degenerate/duplicate faces
q=np.round(p,4); uq,first,inv=np.unique(q,axis=0,return_index=True,return_inverse=True); inv=inv.ravel(); P=p[first]; F=inv[i]
n0=len(F); F=F[(F[:,0]!=F[:,1])&(F[:,1]!=F[:,2])&(F[:,0]!=F[:,2])]
key=np.sort(F,axis=1); _,k=np.unique(key,axis=0,return_index=True); dupfaces=len(F)-len(k); F=F[np.sort(k)]
print('dropped degenerate',n0-len(F)-dupfaces,'duplicate faces',dupfaces)
V0=vol(P,F); stats(P,F,'welded')
# 2 non-manifold: inspect
e,u,inv_e,c=edges(F); nm=np.where(c>2)[0]; fid=np.tile(np.arange(len(F)),3)
area=lambda f:0.5*np.linalg.norm(np.cross(P[f[1]]-P[f[0]],P[f[2]]-P[f[0]]))
for x in nm:
    fs=np.unique(fid[inv_e==x]); print('NM edge',u[x],'faces',[(int(f),round(area(F[f]),5)) for f in fs])
np.savez('/tmp/stage_welded.npz',P=P,F=F)
