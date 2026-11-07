"""v2 step 2: gold silhouette mask of the WHOLE panel of reference/band_face.png (rows 215..472, cols 70..2115).
Otsu seed -> GrabCut with [V, texture, S] features (texture separates pitted ground from smooth shaded gold) -> fill holes -> subtract dark slits (V<65 inside, area>=12; splits petal gaps) -> drop specks.
Measured periodicity: mask IoU vs itself shifted 815 px = 0.77 (peak 811-819), so period ~814.
usage: python3 tools/v2/mask_panel.py -> maps/v2/panel_mask.png (258x2046, 255=gold)"""
import cv2, numpy as np
from scipy import ndimage as ndi
im=cv2.imread('reference/band_face.png'); y0,y1=215,473
P=im[y0:y1,70:2116]
hsv=cv2.cvtColor(P,cv2.COLOR_BGR2HSV); V=hsv[...,2].astype(np.float32)
Vb=cv2.GaussianBlur(V,(0,0),1.5)
t,_=cv2.threshold(cv2.GaussianBlur(cv2.cvtColor(P,cv2.COLOR_BGR2GRAY),(0,0),1.5),0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
m0=cv2.morphologyEx((Vb>t*.85).astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))>0
mean=cv2.GaussianBlur(V,(0,0),3);hp=V-cv2.GaussianBlur(V,(0,0),2);tex=cv2.GaussianBlur(np.abs(hp),(0,0),4)
f=np.dstack([np.clip(Vb,0,255),np.clip(tex*8,0,255),hsv[...,1]]).astype(np.uint8)
d=ndi.distance_transform_edt(~m0); gc=np.full(m0.shape,cv2.GC_PR_BGD,np.uint8); gc[m0]=cv2.GC_PR_FGD
gc[ndi.binary_erosion(m0,iterations=3)&(Vb>150)]=cv2.GC_FGD; gc[d>14]=cv2.GC_BGD
cv2.grabCut(f,gc,None,np.zeros((1,65)),np.zeros((1,65)),6,cv2.GC_INIT_WITH_MASK)
m=(gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD)
m=ndi.binary_opening(ndi.binary_closing(m,np.ones((3,3))),np.ones((3,3))); m=ndi.binary_fill_holes(m)
s=(cv2.GaussianBlur(V,(0,0),1.0)<65)&ndi.binary_erosion(m,iterations=2)
lab,n=ndi.label(s);sz=ndi.sum(s,lab,range(1,n+1));s=np.isin(lab,[i+1 for i,z in enumerate(sz) if z>=12])
m=m&~ndi.binary_dilation(s,iterations=1)
# ground-texture removal (D-v2 s72d, user flagged ground speckle merged into gold between flower and scroll): pitted ground = wide patches of high local texture energy
T=cv2.GaussianBlur(np.abs(V-cv2.GaussianBlur(V,(0,0),1.5)),(0,0),2)
g=ndi.binary_erosion(ndi.binary_opening(T>14,structure=np.ones((11,11))),iterations=4)   # open 11 keeps wide patches only (rims are thin); erode 4 = compensate texture-blur bleed into gold
m=ndi.binary_opening(m&~g,structure=np.ones((5,5)))
lab,n=ndi.label(m);sz=ndi.sum(m,lab,range(1,n+1));m=np.isin(lab,[i+1 for i,z in enumerate(sz) if z>=80])
# edge refinement (s73): GrabCut/ground-removal edges are ragged (5-10 px wobble); the gold rim itself is a crisp bright threshold edge. Use the current mask only as the COARSE region:
# final = (blur(V,1.2) > 95, opened) inside dilate(mask, 6)  U  erode(mask, 3)  -> crisp pointed petals/leaf tips, shaded scroll interiors kept from the coarse mask
Vb2 = cv2.GaussianBlur(cv2.cvtColor(P, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.2)
T0 = ndi.binary_opening(Vb2 > 95, structure=np.ones((3, 3)))
m = (T0 & ndi.binary_dilation(m, iterations=6)) | ndi.binary_erosion(m, iterations=3)
m = ndi.binary_opening(m, structure=np.ones((3, 3)))
lab, n = ndi.label(m); sz = ndi.sum(m, lab, range(1, n + 1)); m = np.isin(lab, [i + 1 for i, z in enumerate(sz) if z >= 80])
cv2.imwrite('maps/v2/panel_mask.png',(m*255).astype(np.uint8))
# periodicity: IoU of mask vs mask shifted by period for shifts around 813 (x offset 70 removed)
