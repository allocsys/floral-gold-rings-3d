import sys; sys.path.insert(0,'/tmp')
from glb import load
import numpy as np
K=np.array([[-0.1514,0.8885,-0.1514],[-0.1566,0.8905,0.1486],[0.1507,0.8883,-0.1511],[0.1554,0.8906,0.1483]])
def runtime_drop(P,T):
    C=P[T].mean(1); x,y,z=C.T; r=np.hypot(x,z); d=np.zeros(len(T),bool)
    for k in K:
        d|=np.linalg.norm(C-k,axis=1)<0.07
        d|=(y>0.905)&(np.hypot(x-np.sign(k[0])*0.137,z-np.sign(k[2])*0.135)<0.065)
    d|=(abs(x)<0.14)&(abs(z)>0.1)&(r>0.15)&(r<0.25)
    for k in K:
        dx=(x-k[0])*-np.sign(k[0]); dy=y-k[1]; dz=(z-k[2])*-np.sign(k[2])
        d|=(dx>0)&(dz>-0.005)&(dy<-0.008)&(dx*dx+dy*dy+dz*dz<0.105**2)
    return d
def weld(P):
    key=np.round(P*1e5).astype(np.int64); _,idx,inv=np.unique(key,axis=0,return_index=True,return_inverse=True); return inv.ravel()
def boundary_edges(Tw):
    e=np.concatenate([Tw[:,[0,1]],Tw[:,[1,2]],Tw[:,[2,0]]]); es=np.sort(e,1)
    u,inv,cnt=np.unique(es,axis=0,return_inverse=True,return_counts=True)
    return u[cnt==1],u,inv.ravel(),cnt
import os
BR=float(os.environ.get('BR',0.07)); CR=float(os.environ.get('CR',0.065)); BU=float(os.environ.get('BU',0.07))
def runtime_drop2(P,T):
    C=P[T].mean(1); x,y,z=C.T; d=np.zeros(len(T),bool)
    for k in K:
        dist=np.linalg.norm(C-k,axis=1); d|=(dist<np.where(y>k[1],BU,BR))
        d|=(y>0.905)&(np.hypot(x-np.sign(k[0])*0.137,z-np.sign(k[2])*0.135)<CR)
    return d
