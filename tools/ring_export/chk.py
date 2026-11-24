import json,base64,sys,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def load(f):
    r=json.load(open(f)); M=[]
    for m in r['meshes']:
        p=np.frombuffer(base64.b64decode(m['p']),np.float32).reshape(-1,3).astype(np.float64)
        i=np.frombuffer(base64.b64decode(m['i']),np.uint32).reshape(-1,3).astype(np.int64)
        M.append((p,i))
    return M
def weld(p,i,tol=1e-4):
    k=np.round(p/tol).astype(np.int64); u,inv=np.unique(k,axis=0,return_inverse=True); inv=inv.ravel()
    first=np.zeros(len(u),np.int64); first[inv[::-1]]=np.arange(len(p))[::-1]
    return p[first],inv[i]
def analyse(p,i,label):
    a,b,c=i[:,0],i[:,1],i[:,2]
    degen=(a==b)|(b==c)|(a==c)
    area=0.5*np.linalg.norm(np.cross(p[b]-p[a],p[c]-p[a]),axis=1)
    zero=area<1e-9
    j=i[~degen]
    srt=np.sort(j,axis=1); _,cnt=np.unique(srt,axis=0,return_counts=True)
    dupf=int((cnt-1).sum())
    e=np.concatenate([j[:,[0,1]],j[:,[1,2]],j[:,[2,0]]])
    es=np.sort(e,axis=1); ue,inv,ecnt=np.unique(es,axis=0,return_inverse=True,return_counts=True)
    open_=ue[ecnt==1]; nm=ue[ecnt>2]
    # directed duplicates (winding inconsistency)
    d=e[:,0]*len(p)+e[:,1]; _,dc=np.unique(d,return_counts=True); ddup=int((dc>1).sum())
    # components
    n=len(p); g=coo_matrix((np.ones(len(es)),(es[:,0],es[:,1])),shape=(n,n))
    used=np.unique(j); nc,lab=connected_components(g,directed=False)
    ncomp=len(np.unique(lab[used]))
    # signed volume
    v=np.einsum('ij,ij->i',p[j[:,0]],np.cross(p[j[:,1]],p[j[:,2]])).sum()/6
    print(f"{label}: verts {n} tris {len(i)} | degenerate {int(degen.sum())} zero-area(after weld) {int(zero.sum())} dup faces {dupf} | open edges {len(open_)} non-manifold {len(nm)} dir-dup {ddup} | components {ncomp} | signed vol {v:.3f} mm3")
    return open_,nm,lab,j
def cluster(p,edges,label,eps=0.05,maxshow=12):
    if len(edges)==0: return
    mid=(p[edges[:,0]]+p[edges[:,1]])/2; ln=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)
    from scipy.spatial import cKDTree
    t=cKDTree(mid); n=len(mid); par=list(range(n))
    def f(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for a,b in t.query_pairs(eps): par[f(a)]=f(b)
    from collections import defaultdict
    G=defaultdict(list)
    for k in range(n): G[f(k)].append(k)
    cl=sorted(G.values(),key=lambda x:-len(x))
    print(f"  {label}: {n} edges in {len(cl)} clusters, total length {ln.sum():.3f} mm")
    for c in cl[:maxshow]:
        m=mid[c].mean(0); print(f"    {len(c)} edges len {ln[c].sum():.3f} mm at ({m[0]:.2f},{m[1]:.2f},{m[2]:.2f})")
f=sys.argv[1]; M=load(f); name=f
print("==",name)
W=[]
for t,(p,i) in enumerate(M):
    pw,iw=weld(p,i); W.append((pw,iw)); o,nm,lab,j=analyse(pw,iw,f"tile{t}")
    if t<2: cluster(pw,o,"open",maxshow=6); cluster(pw,nm,"nonmanifold",maxshow=6)
# merged ring (all tiles welded together)
off=0;P=[];I=[]
for pw,iw in W: P.append(pw); I.append(iw+off); off+=len(pw)
P=np.vstack(P);I=np.vstack(I)
pw,iw=weld(P,I); print("-- merged ring (6 tiles welded at 1e-4)")
o,nm,lab,j=analyse(pw,iw,"ring")
cluster(pw,o,"open",maxshow=15); cluster(pw,nm,"nonmanifold",maxshow=10)
r=np.hypot(pw[:,0],pw[:,1]); print(f"  radius {r.min():.3f}..{r.max():.3f} z {pw[:,2].min():.3f}..{pw[:,2].max():.3f}")
np.savez(f.replace('.json','_weld.npz'),p=pw,i=iw)
