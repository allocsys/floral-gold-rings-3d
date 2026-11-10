"""stage55 (D15): headroom + stronger ridges. usage: CROPX=7 python3 tools/wip_v3/stage55.py [in.png] -> /tmp/band_v3_out/band_period_v55.png
env: RIB (ridge height, default .22), KNEE (default .70), COMP (slope above knee, default .6).
1) compress heights above KNEE: H' = KNEE + (H-KNEE)*COMP (H>KNEE) so the plateau stops clipping at 1 and ridges can stand above it
   (silhouette threshold .3 and slits untouched). 2) raise ref bright ridges exactly as stage53 (white-tophat Lab-L K=15 TB=10) with RIB.
CHAIN USED FOR v55 (all CROPX=7): stage54(in v51) -> stage55 RIB=0 KNEE=.70 COMP=.6 -> stage52 -> stage55 RIB=.22 COMP=1. Measure with tdiff.py (ridge recall/precision, clipped frac, ridge recall on plateau), idiff.py, diff.py."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z='/tmp/band_v3_out/'; CROPX=int(os.environ.get('CROPX',7)); S=2; PW2=2396
inp = sys.argv[1] if len(sys.argv)>1 else Z+'chain_v54_52.png'
K,TB,SPAN,RIM,MINPX = 15,10,20,8,40
RIB=float(os.environ.get('RIB',0.22)); KNEE=float(os.environ.get('KNEE',0.70)); COMP=float(os.environ.get('COMP',0.6))
T2=cv2.imread(Z+'T2.png'); ref=T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H=(cv2.imread(inp,-1).astype(np.float32)/65535)[:520]
lab=cv2.cvtColor(cv2.GaussianBlur(ref,(0,0),1.5),cv2.COLOR_BGR2LAB).astype(np.float32)
C=np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]],np.float32)
g=np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2),[1,3]).astype(np.uint8)
g=cv2.morphologyEx(cv2.morphologyEx(g,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
Hc=np.where(H>KNEE,KNEE+(H-KNEE)*COMP,H)
reg=(cv2.erode(g,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*RIM+1,)*2))>0)&(H>0.3)
L=cv2.cvtColor(cv2.GaussianBlur(ref,(0,0),1.0),cv2.COLOR_BGR2LAB)[:,:,0].astype(np.float32)
th=cv2.morphologyEx(L,cv2.MORPH_TOPHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(K,K)))
ridge=(th>TB)&reg
lb,n=ndi.label(ridge,np.ones((3,3))); sz=ndi.sum(ridge,lb,range(1,n+1)); ridge&=np.isin(lb,1+np.where(sz>=MINPX)[0])
s=np.clip((th-TB)/SPAN,0,1)*ridge
s=np.clip(cv2.GaussianBlur(s.astype(np.float32),(0,0),1.5)*1.6,0,1)
H2=np.where(reg,np.minimum(Hc+RIB*s,1.0),Hc)
print('RIB %.2f KNEE %.2f COMP %.2f; compressed px %d; raised px %d'%(RIB,KNEE,COMP,int((H>KNEE).sum()),int((H2>Hc+1e-4).sum())))
cv2.imwrite(Z+'band_period_v55.png',np.round(np.clip(H2,0,1)*65535).astype(np.uint16)); print('wrote v55')
