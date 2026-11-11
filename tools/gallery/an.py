import numpy as np
V=np.load('V.npy'); F=np.load('F.npy')
P=V[F]; C=P.mean(1); N=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]); 
nl=np.linalg.norm(N,axis=1)+1e-12; N=N/nl[:,None]
box=(C[:,0]>-0.135)&(C[:,0]<0.135)&(C[:,1]>0.595)&(C[:,1]<0.745)
for sg in (1,-1):
    s=box&(C[:,2]*sg>0)
    print('face',sg,'tris',s.sum())
    z=C[s,2]*sg
    h,e=np.histogram(z,bins=14,range=(0,0.224)); print(' z hist',list(zip(np.round(e[:-1],3),h)))
    up=s&(N[:,2]*sg>0.3); dn=s&(N[:,2]*sg<-0.3)
    print(' up-facing',up.sum(),'down-facing',dn.sum(),' z range up',C[up,2].min()*sg if sg>0 else None)
    hi=s&(C[:,2]*sg>0.175); print(' tris z>0.175',hi.sum(),'edge len median',np.median(np.linalg.norm(P[hi,1]-P[hi,0],axis=1)))
