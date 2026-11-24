import numpy as np,collections
d=np.load('/tmp/stage_welded.npz'); P=d['P'].copy(); F=d['F'].copy()
def vol(P,F): t=P[F]; return np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
def estats(F):
    e=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); es=np.sort(e,axis=1); u,inv,c=np.unique(es,axis=0,return_inverse=True,return_counts=True); return e,u,inv.ravel(),c
def stats(F,tag):
    e,u,inv,c=estats(F); dd=collections.Counter(map(tuple,e)); dup=sum(1 for v in dd.values() if v>1)
    print(f'{tag}: tris {len(F)} open {(c==1).sum()} nonmanifold {(c>2).sum()} dup-directed {dup} vol {vol(P,F):.4f}')
stats(F,'start'); V0=vol(P,F)
# 1) remove faces on non-manifold edges
e,u,inv,c=estats(F); fid=np.tile(np.arange(len(F)),3)
rm=np.unique(fid[np.isin(inv,np.where(c>2)[0])]); print('removing',len(rm),'faces on NM edges')
keep=np.ones(len(F),bool); keep[rm]=False; F=F[keep]; stats(F,'after NM removal')
# 2) boundary loops -> directed boundary edges
def loops(F):
    e=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]); es=np.sort(e,axis=1); u,inv,c=np.unique(es,axis=0,return_inverse=True,return_counts=True); inv=inv.ravel()
    b=e[c[inv]==1]; nxt=collections.defaultdict(list)
    for a,bb in b: nxt[a].append(bb)
    seen=set(); res=[]; bad=0
    for a,bb in map(tuple,b):
        if (a,bb) in seen: continue
        L=[a]; cur=a; nx=bb; seen.add((a,bb))
        while nx!=L[0]:
            L.append(nx); cand=[x for x in nxt[nx] if (nx,x) not in seen]
            if not cand: bad+=1; break
            seen.add((nx,cand[0])); cur,nx=nx,cand[0]
        res.append(L)
    return res,bad
L,bad=loops(F); print('boundary loops',len(L),'sizes',sorted(len(x) for x in L),'broken',bad)
newP=[];newF=[]; base=len(P)
for l in L:
    c=P[l].mean(0); cid=base+len(newP); newP.append(c)
    for k in range(len(l)):
        a,b=l[k],l[(k+1)%len(l)]; newF.append([b,a,cid])   # reverse of boundary edge a->b
    print(' loop',len(l),'at',np.round(c,3).tolist(),'dia %.3f'%(2*np.linalg.norm(P[l]-c,axis=1).mean()))
P=np.vstack([P,np.array(newP)]); F=np.vstack([F,np.array(newF)]); stats(F,'after caps')
print('volume change %.4f mm3 (%.4f%%)'%(vol(P,F)-V0,100*(vol(P,F)-V0)/V0))
np.savez('/tmp/stage_repaired.npz',P=P,F=F)
