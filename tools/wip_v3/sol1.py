# sol1: solitaire shank ref (reference/solitaire_flat.png) -> gold mask + first-pass height map of the pattern window
import cv2,numpy as np,os
from scipy import ndimage as ndi
O=os.environ.get('SOL_OUT','/tmp/sol'); os.makedirs(O,exist_ok=True)
g=lambda a,s: cv2.GaussianBlur(a,(0,0),s)
im=cv2.imread('reference/solitaire_flat.png')
X0,X1,Y0,Y1=62,1308,166,269                       # pattern window (rails excluded); stone sits at x 605..760
c=im[Y0:Y1,X0:X1]; L=cv2.cvtColor(c,cv2.COLOR_BGR2LAB)[...,0].astype(np.float32)
hsv=cv2.cvtColor(c,cv2.COLOR_BGR2HSV).astype(np.float32)
sc=g(L,1.2)
th=float(os.environ.get('TH',104))
m=(sc>th).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
lab,n=ndi.label(m); sz=ndi.sum(m,lab,range(1,n+1)); 
for i,s in enumerate(sz):
    if s<12: m[lab==i+1]=0
print('window',c.shape,'gold frac',m.mean().round(3))
np.save(O+'/mask.npy',m)
ov=c.copy(); ov[m==0]=(ov[m==0]*0.35+np.array([0,0,160])*0.65).astype(np.uint8)
cv2.imwrite(O+'/mask_left.png',cv2.resize(ov[:, :560],None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST))
