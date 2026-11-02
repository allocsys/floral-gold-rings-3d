"""stage53 (D12): raise the ref's bright ridges (ribs/veins) that the map lacks, on top of v52.
usage: CROPX=7 python3 tools/wip_v3/stage53.py [in.png] -> /tmp/band_v3_out/band_period_v53.png ; RIB env = height added (default .06)
Ridge strength = white-tophat of ref Lab-L (K=15) soft-thresholded, tiny comps dropped, smoothed; H2 = H + RIB*s inside ref gold (eroded RIM)
where H > .3 (relief exists), then clipped to 1. Measure with tdiff.py / idiff.py / diff.py."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z='/tmp/band_v3_out/'; CROPX=int(os.environ.get('CROPX',7)); S=2; PW2=2396
inp = sys.argv[1] if len(sys.argv)>1 else 'maps/band_period.png'
K,TB,SPAN,RIM,MINPX,RIB = 15,10,20,8,40,float(os.environ.get('RIB',0.06))
T2=cv2.imread(Z+'T2.png'); ref=T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H=(cv2.imread(inp,-1).astype(np.float32)/65535)[:520]
lab=cv2.cvtColor(cv2.GaussianBlur(ref,(0,0),1.5),cv2.COLOR_BGR2LAB).astype(np.float32)
C=np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]],np.float32)
g=np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2),[1,3]).astype(np.uint8)
g=cv2.morphologyEx(cv2.morphologyEx(g,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
reg=(cv2.erode(g,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*RIM+1,)*2))>0)&(H>0.3)
L=cv2.cvtColor(cv2.GaussianBlur(ref,(0,0),1.0),cv2.COLOR_BGR2LAB)[:,:,0].astype(np.float32)
th=cv2.morphologyEx(L,cv2.MORPH_TOPHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(K,K)))
ridge=(th>TB)&reg
lb,n=ndi.label(ridge,np.ones((3,3))); sz=ndi.sum(ridge,lb,range(1,n+1)); ridge&=np.isin(lb,1+np.where(sz>=MINPX)[0])
s=np.clip((th-TB)/SPAN,0,1)*ridge
s=np.clip(cv2.GaussianBlur(s.astype(np.float32),(0,0),1.5)*1.6,0,1)
H2=np.where(reg,np.minimum(H+RIB*s,1.0),H)
print('ridge px %d; raised px %d; mean raise %.3f'%(ridge.sum(),int((H2>H+1e-4).sum()),float((H2-H)[H2>H+1e-4].mean())))
cv2.imwrite(Z+'band_period_v53.png',np.round(np.clip(H2,0,1)*65535).astype(np.uint16)); print('wrote v53')
