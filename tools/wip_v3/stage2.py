exec(open('tools/wip_v3/stage1.py').read())
from scipy.ndimage import map_coordinates
Ls=g(Lab,1.0*S)
TH=np.linspace(0,2*np.pi,72,endpoint=False)
def refine(cx,cy,r):
    best=(-1e9,cx,cy,r)
    dxs=np.arange(-5,5.01,.5)*S; drs=np.arange(-4,4.01,.5)*S
    DX,DY,DR=np.meshgrid(dxs,dxs,drs,indexing='ij')
    DX,DY,DR=DX.ravel(),DY.ravel(),DR.ravel()
    ci=cx+DX[:,None]+(DR[:,None]-1.5*S)*np.cos(TH)[None]; ri=cy+DY[:,None]+(DR[:,None]-1.5*S)*np.sin(TH)[None]
    co=cx+DX[:,None]+(DR[:,None]+1.5*S)*np.cos(TH)[None]; ro=cy+DY[:,None]+(DR[:,None]+1.5*S)*np.sin(TH)[None]
    # radius is r+DR ; recompute with base r
    ci=cx+DX[:,None]+(r+DR[:,None]-1.5*S)*np.cos(TH)[None]; ri=cy+DY[:,None]+(r+DR[:,None]-1.5*S)*np.sin(TH)[None]
    co=cx+DX[:,None]+(r+DR[:,None]+1.5*S)*np.cos(TH)[None]; ro=cy+DY[:,None]+(r+DR[:,None]+1.5*S)*np.sin(TH)[None]
    vi=map_coordinates(Ls,[ri.ravel(),ci.ravel()],order=1,mode='nearest').reshape(ci.shape)
    vo=map_coordinates(Ls,[ro.ravel(),co.ravel()],order=1,mode='nearest').reshape(co.shape)
    # robust: use 30th percentile of per-angle contrast so a bright neighbour on one side doesn't dominate
    con=np.percentile(vi-vo,35,axis=1)
    pen=0.15*(np.abs(DX)+np.abs(DY)+np.abs(DR))/S
    sc=con-pen; i=np.argmax(sc)
    return (cx+DX[i],cy+DY[i],r+DR[i],sc[i])
# beads in window coords (x_w,y_w,r) restricted to the repeat unit x_w 147..746
BEADS_W=[(330,43,24),(365,165,22),(228,240,18),(510,238,26),(598,118,21),(278,78,16),(745,243,10)]
beads=[]   # (x_T2,y_T2,r_T2) for middle tile
dbg=T2.copy()
for xw,yw,r in BEADS_W:
    xp=xw-147
    if xw==745: xp=599
    for cx_p in ([xp,PW-xp] if xp not in (0,599) else [xp]):
        cx,cy=X(cx_p,1),Y(yw)
        rx,ry,rr,sc=refine(cx,cy,r*S)
        beads.append((rx,ry,rr))
        cv2.circle(dbg,(int(round(cx)),int(round(cy))),int(r*S),(0,255,0),1)
        cv2.circle(dbg,(int(round(rx)),int(round(ry))),int(round(rr)),(255,255,255),1)
        print(f'bead x_w={xw}: shift ({(rx-cx)/S:+.1f},{(ry-cy)/S:+.1f}) r {r}->{rr/S:.1f} score {sc:.1f}')
x0=PW2; seg=dbg[:,x0:x0+PW2]
cv2.imwrite(Z+'beads_dbg.png',cv2.resize(seg[:,:1300],None,fx=1,fy=1))
cv2.imwrite(Z+'beads_dbg2.png',seg[:,1100:2396])
pickle.dump(beads,open(Z+'beads.pkl','wb'))
