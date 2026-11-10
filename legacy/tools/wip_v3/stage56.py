"""stage56 (D18): make the crown (edge-to-top) profile width-proportional like the ref instead of fixed-px.
usage: CROPX=7 python3 tools/wip_v3/stage56.py [in.png] -> /tmp/band_v3_out/band_period_v56.png ; env ALPHA (default 1), WREF (px, default 40), R (local max radius, 70).
d = px inside the map silhouette (H>.3), lm = local max of d (local petal half-width, as cdiff.py). P(d) = median height vs d (monotone).
H' = H * P(d*(WREF/lm)^ALPHA) / P(d): a petal narrower than WREF reaches its crown earlier, a wider one later. Multiplicative, so veins/domes/grooves ride on top.
D19: narrow class (local half-width <40, blended over 10px) uses ALPHA_N=2 WREF_N=35 -> v58: narrow-petal profile RMSE .103->.063 lead -.074->-.025, corr(L,H) .557, R2 .329, ridge .946/.928, IoU/line unchanged.
CHAIN FOR v57/v58 (CROPX=7): ...stage54 -> stage56 -> stage55 RIB=0 KNEE=.70 COMP=.6 -> stage52 -> stage55 RIB=.22 COMP=1. Measured with cdiff.py (v56 -> v57): corr(L,H) .532->.558, R2 .308->.331, wide-petal profile RMSE .089->.066, narrow lead -.074->-.058; IoU/line/ridge unchanged.
Only the smooth ratio is applied (gaussian 1.5, clipped .6..1.6); H<=.3 (ground, slits) untouched."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z='/tmp/band_v3_out/'
ALPHA=float(os.environ.get('ALPHA',1)); WREF=float(os.environ.get('WREF',40)); R=int(os.environ.get('R',70)); RMAX=60
ALPHA_N=float(os.environ.get('ALPHA_N',2)); WREF_N=float(os.environ.get('WREF_N',35)); LSPLIT=float(os.environ.get('LSPLIT',40))  # narrow class (lm<LSPLIT, blended over 10px) gets its own ALPHA_N/WREF_N
inp=sys.argv[1] if len(sys.argv)>1 else Z+'c54.png'
H=(cv2.imread(inp,-1).astype(np.float32)/65535)[:520]
h=H>0.3
d=cv2.distanceTransform(h.astype(np.uint8),cv2.DIST_L2,5)
lm=np.maximum(cv2.dilate(d,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*R+1,2*R+1))),1)
prof=np.array([np.median(H[h&(d>k-0.5)&(d<=k+0.5)]) if k>0 else 0.3 for k in range(RMAX+1)]); prof=np.maximum.accumulate(prof)
print('profile P(d)',np.round(prof[::4],2))
P=lambda x: np.interp(x,np.arange(RMAX+1),prof).astype(np.float32)
rt=lambda a,w: P(d*(w/lm)**a)/np.maximum(P(d),1e-3)
wn=np.clip((LSPLIT+5-lm)/10,0,1)
ratio=np.where(h,wn*rt(ALPHA_N,WREF_N)+(1-wn)*rt(ALPHA,WREF),1).astype(np.float32)
ratio=np.clip(cv2.GaussianBlur(ratio,(0,0),1.5),0.6,1.6); ratio[~h]=1
H2=np.where(h,np.clip(H*ratio,0.3001,1),H)
print('ALPHA %.2f WREF %.0f; px changed %d; ratio min %.2f max %.2f'%(ALPHA,WREF,int((np.abs(H2-H)>1e-4).sum()),ratio[h].min(),ratio[h].max()))
cv2.imwrite(Z+'band_period_v56.png',np.round(H2*65535).astype(np.uint16)); print('wrote v56 (stage56)')
