import sys,numpy as np
from scipy.spatial import cKDTree
d=np.load(sys.argv[1]); P=d['P']; I=d['I']; out=sys.argv[2]
src=open('repair.py').read()
# pull helper function defs
for name in ['bedges','chains','zipper']:
    s=src.index('def '+name); e=src.index('\ndef ',s+1) if '\ndef ' in src[s+1:] else src.index('\nth=np.degrees')
    e2=src.find('\nth=np.degrees'); e=min(x for x in [src.find('\ndef ',s+1),e2] if x>0)
    exec(src[s:e])
E=bedges(I); ch,_=chains(E); assert len(ch)==2 and all(c[1] for c in ch)
zs=[np.mean(P[c[0],2]) for c in ch]; print('loop mean z',zs,'radii',[ (np.hypot(P[c[0],0],P[c[0],1]).min().round(4),np.hypot(P[c[0],0],P[c[0],1]).max().round(4)) for c in ch])
A,B=ch[0][0],ch[1][0]
tri=zipper(A,B,True,P); print('bore strip tris',len(tri))
I3=np.vstack([I,np.array(tri)])
E=bedges(I3); print('boundary edges after bore',len(E))
# full checks
a,b,c=I3[:,0],I3[:,1],I3[:,2]
e=np.concatenate([I3[:,[0,1]],I3[:,[1,2]],I3[:,[2,0]]]); key=e[:,0].astype(np.int64)*len(P)+e[:,1]; u,cnt=np.unique(key,return_counts=True)
print('directed edges used >1:',int((cnt>1).sum()))
es=np.sort(e,axis=1); ue,uc=np.unique(es,axis=0,return_counts=True); print('open',int((uc==1).sum()),'nonmanifold',int((uc>2).sum()))
vol=np.einsum('ij,ij->i',P[I3[:,0]],np.cross(P[I3[:,1]],P[I3[:,2]])).sum()/6
print('signed volume %.3f mm3'%vol)
ar=0.5*np.linalg.norm(np.cross(P[I3[:,1]]-P[I3[:,0]],P[I3[:,2]]-P[I3[:,0]]),axis=1); print('zero-area tris',int((ar<1e-9).sum()),'min nonzero area',ar[ar>1e-9].min())
np.savez(out,P=P,I=I3)
# Euler / genus
V=len(np.unique(I3)); Ecount=len(ue); F=len(I3); print('V',V,'E',Ecount,'F',F,'chi',V-Ecount+F)
