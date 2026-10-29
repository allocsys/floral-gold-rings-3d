# stage 1: tile -> 2x, gold mask, slit carve, beads, watershed regions  (debug overlays)
import cv2, numpy as np, os, pickle
from scipy import ndimage as ndi
from skimage.segmentation import watershed
ROOT='.'; Z='/tmp/band_v3_out/'
S=2
def ell(k):
    k=int(round(k)); k=k if k%2 else k+1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k))
g=lambda a,s: cv2.GaussianBlur(a,(0,0),s)

ref=cv2.imread(ROOT+'/reference/rings_flat.png')
im=cv2.resize(ref[255:425,25:760],None,fx=2.2,fy=2.2,interpolation=cv2.INTER_CUBIC)
c=im[48:308,66:1502]
A=c[:,147:747]
P=np.hstack([A,A[:,::-1][:,1:-1]]); PW=P.shape[1]          # one exact period (1198 cols)
T=np.hstack([P,P,P])
T2=cv2.resize(T,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
H2,W2=T2.shape[:2]; PW2=PW*S
X=lambda xp,k=1: (xp+PW*k)*S+(S-1)/2      # period-x (1x) -> T2 col
Y=lambda y: y*S+(S-1)/2

Lab=cv2.cvtColor(T2,cv2.COLOR_BGR2LAB).astype(np.float32)[...,0]
sd=np.sqrt(np.maximum(g(Lab*Lab,3*S)-g(Lab,3*S)**2,0))
score=g(Lab,2.5*S)-0.6*sd   # (kept for old outline / debug)

def build(close_k,hole_max):
    m=(score>104).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,ell(close_k*S))
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,ell(5*S))
    inv=1-m; l,n=ndi.label(inv); sz=ndi.sum(inv,l,range(1,n+1))
    for i,s in enumerate(sz):
        if s<hole_max*S*S: m[l==i+1]=1
    return m
big,small=build(13,1200),build(7,120)

FLOWERS=[(0,133,24),(599,128,26)]                 # (axis x in period, y, centre-dome radius)
zone=np.zeros((H2,W2),np.float32)
for k in range(3):
    for fx,fy,_ in FLOWERS:
        cv2.ellipse(zone,(int(X(fx,k)),int(Y(130))),(125*S,150*S),0,0,360,1,-1)
zone=g(zone,12*S)
m=np.where(zone>.5,small,big).astype(np.uint8)

# ---- precise outline (v7): topology-safe base mask (light blur, small close) + local half-max edge refinement
def base_mask(sig=1.2,close_k=5,hole=60,speck=40):
    sc=g(Lab,sig*S)-0.6*sd
    b=(sc>104).astype(np.uint8)
    b=cv2.morphologyEx(b,cv2.MORPH_CLOSE,ell(close_k*S))
    b=cv2.morphologyEx(b,cv2.MORPH_OPEN,ell(3*S))
    l,n=ndi.label(b); sz=ndi.sum(b,l,range(1,n+1))
    for i,s_ in enumerate(sz):
        if s_<speck*S*S: b[l==i+1]=0
    inv=1-b; l,n=ndi.label(inv); sz=ndi.sum(inv,l,range(1,n+1))
    for i,s_ in enumerate(sz):
        if s_<hole*S*S: b[l==i+1]=1
    return b
def refine_edges(b,sig=0.8,R=6,B=5):
    # inside the +-B px band around the base boundary, put the edge at the half-way level between the
    # local gold plateau (max L inside, radius R) and the local recess level (min L outside)
    Lf=g(Lab,sig*S); r=int(R*S)
    hi=g(cv2.dilate(np.where(b>0,Lf,0).astype(np.float32),ell(2*r+1)),2*S)
    lo=g(cv2.erode(np.where(b>0,255,Lf).astype(np.float32),ell(2*r+1)),2*S)
    d=cv2.distanceTransform(b,cv2.DIST_L2,5)-cv2.distanceTransform(1-b,cv2.DIST_L2,5)
    new=np.where(np.abs(d)<B*S,Lf>0.5*(hi+lo),b>0).astype(np.uint8)
    l,n=ndi.label(new); sz=ndi.sum(new,l,range(1,n+1))
    for i,s_ in enumerate(sz):
        if s_<40*S*S: new[l==i+1]=0
    return new
def fill_slits(b,w=8,maxarea=900):
    # dark features narrower than w px that touch the wide recess at <=1 place are slits/pin holes inside a
    # leaf: fill them (later stages re-cut them as soft grooves). Features bridging two recess areas are
    # real gaps between shapes and stay open.
    inv=(1-b).astype(np.uint8)
    far=cv2.morphologyEx(inv,cv2.MORPH_OPEN,ell(w*S))
    far=cv2.dilate(far,ell(3))                        # recover opening shrink at the contact line
    narrow=(inv>0)&(far==0)
    l,n=ndi.label(narrow); out=b.copy()
    sl=ndi.find_objects(l)
    for i,sli in enumerate(sl):
        y0,y1=max(sli[0].start-6*S,0),min(sli[0].stop+6*S,b.shape[0])
        x0,x1=max(sli[1].start-6*S,0),min(sli[1].stop+6*S,b.shape[1])
        comp=(l[y0:y1,x0:x1]==i+1).astype(np.uint8)
        if comp.sum()>maxarea*S*S: continue
        touch=cv2.dilate(comp,ell(5*S))&(far[y0:y1,x0:x1]>0)&(inv[y0:y1,x0:x1]>0)
        k,_=ndi.label(touch)
        if _<=1: out[y0:y1,x0:x1][comp>0]=1
    return out
def smooth_mask(b,sig=1.2):
    d=cv2.distanceTransform(b,cv2.DIST_L2,5)-cv2.distanceTransform(1-b,cv2.DIST_L2,5)
    out=(g(d.astype(np.float32),sig*S)>0).astype(np.uint8)
    inv=1-out; l,n=ndi.label(inv); sz=ndi.sum(inv,l,range(1,n+1))   # pin holes left after smoothing
    for i,s_ in enumerate(sz):
        if s_<150*S*S: out[l==i+1]=1
    return out
if not os.environ.get('OLD_OUTLINE'):
    m=refine_edges(base_mask())
    m=smooth_mask(fill_slits(m))

g8=cv2.cvtColor(T2,cv2.COLOR_BGR2GRAY).astype(np.float32)
bh=cv2.morphologyEx(g(g8,1.2*S),cv2.MORPH_BLACKHAT,ell(13*S))
slit=((bh>52)&(zone>.5)).astype(np.uint8)
slit=cv2.morphologyEx(slit,cv2.MORPH_OPEN,ell(2*S))
l,n=ndi.label(slit); sz=ndi.sum(slit,l,range(1,n+1))
for i,s in enumerate(sz):
    if s<90*S*S: slit[l==i+1]=0

np.savez_compressed(Z+'s1.npz',m=m,slit=slit,bh=bh,zone=zone,score=score)
cv2.imwrite(Z+'T2.png',T2)
print(T2.shape,PW,PW2)
