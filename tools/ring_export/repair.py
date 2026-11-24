import sys,numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
fn=sys.argv[1]; out=sys.argv[2]
exec(open('chk.py').read().split("f=sys.argv[1]")[0])
sys.argv=[0,fn]
def prep(p,i):
    pw,iw=weld(p,i); ok=~((iw[:,0]==iw[:,1])|(iw[:,1]==iw[:,2])|(iw[:,0]==iw[:,2])); j=iw[ok]
    es=np.sort(np.concatenate([j[:,[0,1]],j[:,[1,2]],j[:,[2,0]]]),axis=1); ue=np.unique(es,axis=0)
    n=len(pw); g=coo_matrix((np.ones(len(ue)),(ue[:,0],ue[:,1])),shape=(n,n)); nc,lab=connected_components(g,directed=False)
    used=np.unique(j); cs,cn=np.unique(lab[used],return_counts=True); body=cs[cn.argmax()]
    keep=np.isin(lab[j[:,0]],[body]); j=j[keep]; used=np.unique(j); rm=np.full(n,-1); rm[used]=np.arange(len(used))
    return pw[used],rm[j],int((~ok).sum()),len(cs)
M=load(fn); P=[];I=[];own=[];off=0
for t,(p,i) in enumerate(M):
    pw,j,nd,nc=prep(p,i); P.append(pw); I.append(j+off); own.append(np.full(len(pw),t)); off+=len(pw)
    if t==0: print('tile prep: dropped degenerate',nd,'comps before',nc,'-> verts',len(pw),'tris',len(j))
P=np.vstack(P); I=np.vstack(I); own=np.concatenate(own); print('ring verts',len(P),'tris',len(I))
def bedges(I):
    e=np.concatenate([I[:,[0,1]],I[:,[1,2]],I[:,[2,0]]]); key=e[:,0]*len(P)+e[:,1]; rk=e[:,1]*len(P)+e[:,0]
    s=np.isin(key,rk); return e[~s]
def chains(E):
    nxt={}; 
    for a,b in E: nxt.setdefault(a,[]).append(b)
    pinch=sum(len(v)>1 for v in nxt.values()); 
    indeg={}; 
    for a,b in E: indeg[b]=indeg.get(b,0)+1
    used=set(); res=[]
    starts=[a for a in nxt if indeg.get(a,0)==0]
    def walk(s,closed):
        path=[s]; v=s; 
        while True:
            c=[w for w in nxt.get(v,[]) if (v,w) not in used]
            if not c: break
            w=c[0]; used.add((v,w)); 
            if w==s and closed: return path,True
            path.append(w); v=w
        return path,False
    for s in starts:
        pth,_=walk(s,False); res.append((pth,False))
    for a in list(nxt):
        if any((a,w) not in used for w in nxt[a]):
            pth,cl=walk(a,True); res.append((pth,cl))
    return res,pinch
def zipper(A,B,closed,P):
    # A face-sense path, B face-sense path (antiparallel): walk B reversed
    Bw=B[::-1]
    if closed:
        d=np.linalg.norm(P[Bw]-P[A[0]],axis=1); k0=int(d.argmin()); Bw=Bw[k0:]+Bw[:k0]
        A=list(A)+[A[0]]; Bw=list(Bw)+[Bw[0]]
    nA=len(A)-1; nB=len(Bw)-1; i=k=0; tri=[]
    while i<nA or k<nB:
        if i<nA and (k>=nB or np.linalg.norm(P[A[i+1]]-P[Bw[k]])<=np.linalg.norm(P[A[i]]-P[Bw[k+1]])):
            tri.append((A[i+1],A[i],Bw[k])); i+=1
        else:
            tri.append((Bw[k],Bw[k+1],A[i])); k+=1
    return tri
th=np.degrees(np.arctan2(P[:,1],P[:,0]))%360; dmod=np.abs(((th+30)%60)-30)
E=bedges(I); onp=dmod<2e-3; seamE=E[onp[E[:,0]]&onp[E[:,1]]]
print('boundary edges',len(E),'seam edges',len(seamE))
new=[]; 
for k in range(6):
    a0=60*k
    sk=seamE[np.abs(((th[seamE[:,0]]-a0+180)%360)-180)<1]
    tile_hi=own[sk[:,0]]
    Aedges=sk[tile_hi==(k-1)%6]; Bedges=sk[tile_hi==k]
    Ac,pa=chains(Aedges); Bc,pb=chains(Bedges); 
    print(f'plane {a0}: end-side edges {len(Aedges)} start-side {len(Bedges)} chains {len(Ac)}/{len(Bc)} pinch {pa}/{pb}')
    usedB=set()
    for (pa_,cla) in Ac:
        best=None
        for bi,(pb_,clb) in enumerate(Bc):
            if bi in usedB or clb!=cla: continue
            t=cKDTree(P[pb_]); d,_=t.query(P[pa_]); m=d.mean()
            if best is None or m<best[0]: best=(m,bi)
        if best is None or best[0]>0.3: print('  UNMATCHED chain len',len(pa_),best); continue
        usedB.add(best[1]); new+=zipper(pa_,Bc[best[1]][0],cla,P)
    if len(usedB)!=len(Bc): print('  unmatched B chains',len(Bc)-len(usedB))
I2=np.vstack([I,np.array(new)]); print('seam tris added',len(new))
E=bedges(I2); ch,pinch=chains(E); print('remaining boundary edges',len(E),'loops/paths',len(ch),[(len(c[0]),c[1]) for c in ch][:10],'pinch',pinch)
np.savez(out,P=P,I=I2,own=own)
