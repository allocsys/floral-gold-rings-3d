"""stage51 (D9): fill the real MISS gaps (red in diff.py) on top of the stage50 map.
usage: CROPX=7 python3 tools/wip_v3/stage51.py   -> /tmp/band_v3_out/band_period_v51.png
Real gap = MISS blob wider than ~8 px (opening 9x9) that touches the relief (<=3 px). Isolated blobs
(bright speckles in the bronze ground) are skipped. Fill = reconstruct the MISS pixels within 6 px of such a blob,
then give them the median edge profile of the existing relief (height vs distance inside the mask), so new
edges look like the old ones. Only pixels within 12 px of a fill are touched, and only ever raised (max)."""
import os, cv2, numpy as np
from scipy import ndimage as ndi
Z='/tmp/band_v3_out/'; CROPX=int(os.environ.get('CROPX',7)); S=2; PW2=2396
T2=cv2.imread(Z+'T2.png'); ref=T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H=cv2.imread(Z+'band_period_v50.png',-1).astype(np.float32)/65535; H=H[:520]
lab=cv2.cvtColor(cv2.GaussianBlur(ref,(0,0),1.5),cv2.COLOR_BGR2LAB).astype(np.float32)
C=np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]],np.float32)
g=np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2),[1,3]).astype(np.uint8)
g=cv2.morphologyEx(cv2.morphologyEx(g,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))>0
h=H>0.3; miss=g&~h
core=ndi.binary_opening(miss,np.ones((9,9),bool))
lbl,n=ndi.label(core,np.ones((3,3)))
dist=ndi.distance_transform_edt(~h)
keep=np.zeros_like(core); skipped=0
for i in range(1,n+1):
    b=lbl==i
    if dist[b].min()<=3: keep|=b
    else: skipped+=1; print('skip isolated blob area %d at x%d y%d'%(b.sum(),*np.argwhere(b).mean(0)[::-1]))
F=ndi.binary_dilation(keep,iterations=6)&miss
# smooth the ragged k-means edge of the fill (gaussian sigma 3 on the mask, 0.5 threshold); never shrinks below the raw blobs
F=(cv2.GaussianBlur(F.astype(np.float32),(0,0),3)>0.5)|keep
F&=~h
print('fill px %d (kept %d blobs, skipped %d)'%(F.sum(),n-skipped,skipped))
# median edge profile of the existing relief: height vs distance inside the mask
din=ndi.distance_transform_edt(h); R=24
prof=np.array([np.median(H[(h)&(din>d-0.5)&(din<=d+0.5)]) if d>0 else 0.3 for d in range(R+1)])
prof=np.maximum.accumulate(prof); print('edge profile', np.round(prof[::3],2))
pf=lambda d: np.interp(d,np.arange(R+1),prof).astype(np.float32)
m2=h|F; d2=ndi.distance_transform_edt(m2)
# continuous growth: relief = edge profile(distance to outside) x internal modulation M (veins, domes...).
# M = H/p(din) where reliable (din>=4), extended into the fill by normalised convolution (clipped 0.9..1.1 so grooves don't bleed).
rel=h&(din>=4)&(dist<=0)
M=np.where(rel,np.clip(H/np.maximum(pf(din),1e-3),0.9,1.1),0).astype(np.float32)
W=rel.astype(np.float32); sg=4
Mx=cv2.GaussianBlur(M,(0,0),sg)/np.maximum(cv2.GaussianBlur(W,(0,0),sg),1e-4)
Mx=np.where(cv2.GaussianBlur(W,(0,0),sg)>1e-3,Mx,1.0)
Hnew=pf(d2)*Mx; Hnew[~m2]=0
delta=d2-din                                   # >0 only where the mask grew; 0 elsewhere, continuous
w=np.clip(delta/2.0,0,1)
H2=np.where(delta>0,H+w*(Hnew-H),H)
H2=np.maximum(H2,H*0)                          # never negative
cv2.imwrite(Z+'band_period_v51.png',np.round(np.clip(H2,0,1)*65535).astype(np.uint16))
print('wrote v51; changed px', int((np.abs(H2-H)>1e-4).sum()), 'raised', int((H2>H+1e-4).sum()), 'lowered', int((H2<H-1e-4).sum()))
