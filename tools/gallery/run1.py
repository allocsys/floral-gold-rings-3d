import numpy as np
from rast import *
V=np.load('V.npy'); F=np.load('F.npy'); P=V[F]; C=P.mean(1)
box=(C[:,0]>-0.16)&(C[:,0]<0.16)&(C[:,1]>0.57)&(C[:,1]<0.77)&(C[:,2]>0)
zb=raster(P[box]); np.save('zb_all.npy',zb)
ct=np.load('comp_tris.npy')
sel=np.where((C[:,2]>0.175)&box)[0]
zhi=raster(P[sel]); np.save('zb_hi.npy',zhi)
print(np.nanmin(zb),np.nanmax(zb),np.isnan(zb).mean(),'hi px',(~np.isnan(zhi)).sum())
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(1,2,figsize=(14,5))
ax[0].imshow(zb,origin='lower',extent=[X0,X1,Y0,Y1],cmap='viridis'); ax[0].set_title('+z top-view max z')
ax[1].imshow(~np.isnan(zhi),origin='lower',extent=[X0,X1,Y0,Y1]); ax[1].set_title('tris with centroid z>0.175')
plt.savefig('h1.png',dpi=70)
