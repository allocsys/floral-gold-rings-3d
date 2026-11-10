import cv2,numpy as np
from skimage.metrics import structural_similarity as ssim
p=cv2.imread('/tmp/band_v3_out/v43_preview.png')
ref=p[0:520];hm=p[520:1040];rel=p[1040:1560]
g=lambda x:cv2.cvtColor(x,cv2.COLOR_BGR2GRAY)
gr,gl=g(ref),g(rel)
# silhouette: ref bright vs heightmap raised
m_ref=(cv2.GaussianBlur(gr,(0,0),2)>60)
m_hm=(g(hm)>25)
iou=(m_ref&m_hm).sum()/(m_ref|m_hm).sum()
# edges
er=cv2.Canny(gr,60,140);el=cv2.Canny(gl,60,140)
dr=cv2.distanceTransform(255-er,cv2.DIST_L2,3);dl=cv2.distanceTransform(255-el,cv2.DIST_L2,3)
prec=(dr[el>0]<3).mean();rec=(dl[er>0]<3).mean()
sc,sm=ssim(gr,gl,full=True,gaussian_weights=True)
print('IoU silhouette %.3f | edge precision %.3f recall %.3f | SSIM %.3f'%(iou,prec,rec,sc))
# heatmap: edge-distance mismatch
mis=np.zeros(gr.shape,np.float32)
mis[er>0]=np.minimum(dl[er>0],12)/12      # ref edges missing in relief
mis2=np.zeros(gr.shape,np.float32);mis2[el>0]=np.minimum(dr[el>0],12)/12
vis=ref.copy()//2
vis[(er>0)]=(0,0,255)           # ref edges red
vis[(el>0)]=(0,255,0)           # relief edges green
both=(cv2.dilate(er,None)>0)&(el>0)
vis[both]=(255,255,255)
cv2.imwrite('/tmp/edges_overlay.png',vis)
sh=cv2.applyColorMap((np.clip(1-sm,0,1)*255).astype(np.uint8),cv2.COLORMAP_JET)
cv2.imwrite('/tmp/ssim_heat.png',sh)
# grid scores
cw=1198//4
print('worst cells (cols x rows) by local SSIM:')
cells=[]
for cy in range(0,520,130):
  for cx in range(0,2396,300):
    cells.append((sm[cy:cy+130,cx:cx+300].mean(),cx,cy))
for s,cx,cy in sorted(cells)[:6]:print('  x%d y%d  %.2f'%(cx,cy,s))
out=np.vstack([vis,sh])
cv2.imwrite('/mnt/user-data/outputs/err_report.png',cv2.resize(out,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA))
