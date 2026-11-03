# sol3: sol2 H (left half A incl. rails, stone-end at the RIGHT of A) -> site/relief_sol.js : half-circle map from the stone (u=0) to the bottom (u=1),
# segments A_rev (stone-end first) | A | A_rev  => outer ends meet mirror-wise at every joint, bottom seam is a mirror axis (geometry.js reflects u at both ends)
import cv2,numpy as np,os,base64
O=os.environ.get('SOL_OUT','/tmp/sol'); H=np.load(O+'/H.npy')               # S=2 supersampled, rows = Y0..Y1
S=2; H1=cv2.resize(H,(H.shape[1]//S,H.shape[0]//S),interpolation=cv2.INTER_AREA)
A=H1[:, ::-1]                                                              # stone-end first
K=16                                                                        # D45: the ref's end-cap groove sits in the outer-end columns of the rails -> notch at every outer joint; extend the rail profile from column K inwards
for r0,r1 in ((0,14),(H1.shape[0]-13,H1.shape[0])): A[r0:r1,-K:]=A[r0:r1,[-K-1]]
seg=np.hstack([A,A[:,::-1],A])                                             # stone-end .. outer | outer .. stone-end | stone-end .. outer
u8=np.clip(np.round(seg*255),0,255).astype(np.uint8); Hh,W=u8.shape
open('site/relief_sol.js','w').write('// Solitaire shank relief (maps from reference/solitaire_flat.png via tools/wip_v3/sol1..3.py): half circle, u=0 at the stone .. u=1 at the bottom (mirrored at both ends), rows across the shank width. 8-bit, base64.\nexport const RELIEF_SOL = { W: %d, H: %d, b64: \'%s\' };\n'%(W,Hh,base64.b64encode(u8.tobytes()).decode()))
cv2.imwrite(O+'/sol_map.png',u8); print('map',u8.shape,'js bytes',os.path.getsize('site/relief_sol.js'))
