"""stage54 (D13): snap the relief silhouette (H>.3) onto the ref gold mask (diff.py definition) by a decaying edge-displacement warp.
usage: CROPX=7 python3 tools/wip_v3/stage54.py [in.png] -> /tmp/band_v3_out/band_period_v54.png ; ITERS, DECAY env.
delta = SD_ref - SD_map (signed distances, + inside); per iter H <- H sampled at p + delta*decay(|SD_map|)*unit-inward-normal. Then measure with diff.py."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z='/tmp/band_v3_out/'; CROPX=int(os.environ.get('CROPX',7)); S=2; PW2=2396
ITERS=int(os.environ.get('ITERS',6)); DECAY=float(os.environ.get('DECAY',10))
inp=sys.argv[1] if len(sys.argv)>1 else Z+'band_period_v53.png'
T2=cv2.imread(Z+'T2.png'); ref=T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H=(cv2.imread(inp,-1).astype(np.float32)/65535)[:520]
lab=cv2.cvtColor(cv2.GaussianBlur(ref,(0,0),1.5),cv2.COLOR_BGR2LAB).astype(np.float32)
C=np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]],np.float32)
g=np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2),[1,3]).astype(np.uint8)
g=cv2.morphologyEx(cv2.morphologyEx(g,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))>0
sd=lambda m: (ndi.distance_transform_edt(m)-ndi.distance_transform_edt(~m)).astype(np.float32)
SR=sd(g); yy,xx=np.mgrid[0:520,0:H.shape[1]].astype(np.float32)
def iou(H): h=H>0.3; return (g&h).sum()/(g|h).sum()
print('start IoU %.4f'%iou(H))
for i in range(ITERS):
    SM=cv2.GaussianBlur(sd(H>0.3),(0,0),1.0); d=np.clip(SR-SM,-12,12)
    w=np.exp(-np.abs(SM)/DECAY); gy,gx=np.gradient(SM); n=np.hypot(gx,gy)+1e-6
    dd=cv2.GaussianBlur(d*w,(0,0),1.5)
    H=cv2.remap(H,xx+dd*gx/n,yy+dd*gy/n,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    print('iter %d IoU %.4f'%(i+1,iou(H)))
cv2.imwrite(Z+'band_period_v54.png',np.round(np.clip(H,0,1)*65535).astype(np.uint16)); print('wrote v54')
