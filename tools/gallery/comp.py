import numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
V=np.load('V.npy'); F=np.load('F.npy'); P=V[F]; C=P.mean(1)
Z0=0.175
# triangles on +z face, any centroid z>Z0, within generous bbox
sel=np.where((C[:,2]>Z0)&(C[:,0]>-0.2)&(C[:,0]<0.2)&(C[:,1]>0.5)&(C[:,1]<0.85))[0]
# connect via shared vertex ids
idxmap={}
rows=[];cols=[]
vt={}
for k,t in enumerate(sel):
    for v in F[t]: vt.setdefault(int(v),[]).append(k)
for v,l in vt.items():
    for a in l[1:]: rows.append(l[0]); cols.append(a)
n=len(sel); A=sp.coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,n))
nc,lab=connected_components(A,directed=False)
sizes=np.bincount(lab); 
print('components',nc,'sizes top',sorted(sizes)[-5:])
for c in np.argsort(sizes)[::-1][:4]:
    t=sel[lab==c]; pp=P[t].reshape(-1,3)
    print(c,sizes[c],'bbox',pp.min(0).round(4),pp.max(0).round(4))
big=np.argsort(sizes)[::-1][0]
np.save('comp_tris.npy',sel[lab==big])
