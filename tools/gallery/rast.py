import numpy as np
X0,X1,Y0,Y1,H=-0.16,0.16,0.57,0.77,0.0005
W=int(round((X1-X0)/H)); Hh=int(round((Y1-Y0)/H))
def raster(P, vals=None):
    """ortho z-buffer from +z: returns max z per pixel (nan where empty) for triangles P (n,3,3)"""
    zb=np.full((Hh,W),np.nan,np.float32)
    for t in P:
        xs=(t[:,0]-X0)/H; ys=(t[:,1]-Y0)/H
        x0=int(max(np.floor(xs.min()),0)); x1=int(min(np.ceil(xs.max()),W-1)); y0=int(max(np.floor(ys.min()),0)); y1=int(min(np.ceil(ys.max()),Hh-1))
        if x1<x0 or y1<y0: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(d)<1e-12: continue
        a=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d
        b=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d
        c=1-a-b; m=(a>=-1e-9)&(b>=-1e-9)&(c>=-1e-9)
        if not m.any(): continue
        z=a*t[0,2]+b*t[1,2]+c*t[2,2]
        sub=zb[y0:y1+1,x0:x1+1]
        cur=np.where(np.isnan(sub),-9,sub)
        upd=m&(z>cur); sub[upd]=z[upd]
    return zb
