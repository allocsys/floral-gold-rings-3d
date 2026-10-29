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
score=g(Lab,2.5*S)-0.6*sd

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
