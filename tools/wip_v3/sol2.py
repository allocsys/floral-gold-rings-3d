# sol2: sol1 mask -> height map H in [0,1] (1 = raised gold crown, 0 = engraved ground), cushion profile + ref-L shading detail
import cv2,numpy as np,os
from scipy import ndimage as ndi
O=os.environ.get('SOL_OUT','/tmp/sol'); g=lambda a,s: cv2.GaussianBlur(a,(0,0),s)
m=np.load(O+'/mask.npy').astype(np.uint8)
im=cv2.imread('reference/solitaire_flat.png'); X0,X1,Y0,Y1=62,1308,166,269
L=cv2.cvtColor(im[Y0:Y1,X0:X1],cv2.COLOR_BGR2LAB)[...,0].astype(np.float32)
S=int(os.environ.get('S',2)); m2=cv2.resize(m,None,fx=S,fy=S,interpolation=cv2.INTER_NEAREST)
d=ndi.distance_transform_edt(m2)/S                  # px (1x) inside gold
R=float(os.environ.get('R',4.0))                    # cushion radius in 1x px
cush=np.sqrt(np.clip(1-(1-np.clip(d/R,0,1))**2,0,1))   # quarter-circle rim profile
cush=g(cush.astype(np.float32),0.8*S)
Ls=cv2.resize(g(L,1.0),None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
det=np.clip((Ls-g(Ls,6*S))/60,-.12,.12)             # fine ref-shading detail (veins, petal creases) on top of the cushion
H=np.clip(cush*(m2>0)*(1+det)*0.96+0.04*(m2>0),0,1)
H=np.where(m2>0,H,0).astype(np.float32); H=g(H,0.6*S)
np.save(O+'/H.npy',H); print('H',H.shape,'mean',H.mean().round(3),'gold frac',(H>.5).mean().round(3))
cv2.imwrite(O+'/H_left.png',(H[:, :560*S]*255).astype(np.uint8))
