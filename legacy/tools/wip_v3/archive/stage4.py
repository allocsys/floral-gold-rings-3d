# stage 4: per-region smoothed relief, grooves, domes, symmetrize, write period + previews
exec(open('tools/wip_v3/stage3.py').read())
sm=lambda a:a*a*(3-2*a)
# leaf/scroll veins -> shallow grooves (not inside flower zones)
inner=cv2.erode(m0,ell(9*S))
vein=((bh>40)&(inner>0)&(zone<.5)).astype(np.uint8)
vein=cv2.morphologyEx(vein,cv2.MORPH_OPEN,ell(2*S))
l,n=ndi.label(vein); sz=ndi.sum(vein,l,range(1,n+1))
keep=np.zeros(n+1,bool); keep[1:]=sz>=70*S*S; vein=keep[l].astype(np.uint8)
vf=1-0.30*np.clip(g(vein.astype(np.float32),1.6*S)*2,0,1)
# petal slits -> soft grooves that reach the recess floor
from skimage.morphology import skeletonize
sk=cv2.dilate(skeletonize(slit>0).astype(np.uint8),ell(2*S))        # narrow slits -> crisp ~2px engraved lines
wide=cv2.erode(slit,ell(2*S))                                        # wide slots keep their body, minus the shadow rim
sl=np.clip(g(np.maximum(sk,wide).astype(np.float32),0.9*S)*2.2,0,1)

HS=np.zeros((H2,W2),np.float32)
PADp=40*S
for i,o in enumerate(ndi.find_objects(lab),1):
    if o is None: continue
    ys,xs=o
    y0,y1=max(ys.start-PADp,0),min(ys.stop+PADp,H2); x0,x1=max(xs.start-PADp,0),min(xs.stop+PADp,W2)
    R=(lab[y0:y1,x0:x1]==i)
    if R.sum()<150*S*S: continue
    R=cv2.morphologyEx(R.astype(np.uint8),cv2.MORPH_OPEN,ell(3*S))>0      # drop hair-thin spikes
    if R.sum()<150*S*S: continue
    sdf=(ndi.distance_transform_edt(R)-ndi.distance_transform_edt(~R)).astype(np.float32)
    petal=((i-1)%15)<14 and i<=45                      # marker ids: 15 per tile, last one is the scroll
    sdf=g(sdf,(3.6 if petal else 3.0)*S)                                   # smooth contour (no jaggies, no ribbing)
    d=np.maximum(sdf,0)/S                              # inward distance in 1x px
    loc=g(cv2.dilate(d,ell(31*S)),5*S)
    xe=np.clip(d/12,0,1); xc=np.clip(d/np.clip(loc,6,26),0,1)
    h=(0.72*sm(xe)+0.28*np.sqrt(1-(1-xc)**2))*vf[y0:y1,x0:x1]
    hr=np.clip(0.5+sdf,0,1)*(0.28+0.72*h)
    HS[y0:y1,x0:x1]=np.maximum(HS[y0:y1,x0:x1],hr)
HS*=(1-sl)
HS=g(HS,0.7*S/2)

def dome(hs,bx,by,r,base,top,pw=.5):
    x0,x1=max(int(bx-r-2),0),min(int(bx+r+3),W2); y0,y1=max(int(by-r-2),0),min(int(by+r+3),H2)
    yy_,xx_=np.mgrid[y0:y1,x0:x1]; rr=np.hypot(xx_-bx,yy_-by)
    dm=np.where(rr<r,base+(top-base)*np.sqrt(np.clip(1-(rr/r)**2,0,1))**(2*pw),0)
    hs[y0:y1,x0:x1]=np.maximum(hs[y0:y1,x0:x1],dm)
for bx,by,br in BEADS_ALL: dome(HS,bx,by,br,.3,1.0)
for bx,by,br in CEN: dome(HS,bx,by,br,.3,.95)
# stipple dots sitting in the recess: small bright round blobs away from the gold shapes
th=cv2.morphologyEx(g(Lab,0.8*S),cv2.MORPH_TOPHAT,ell(15*S))
cand=(th>38).astype(np.uint8)
cand=cv2.morphologyEx(cand,cv2.MORPH_OPEN,ell(2*S))
near=cv2.dilate(((m0>0)|(HS>0.3)).astype(np.uint8),ell(7*S))
domes_m=np.zeros((H2,W2),np.uint8)
for bx,by,br in DOMES: cv2.circle(domes_m,(int(bx),int(by)),int(br+GAP+4),1,-1)
cand=cand&(1-near)&(1-domes_m)
l,n=ndi.label(cand); nd=0; DOTS=[]
for i,o in enumerate(ndi.find_objects(l),1):
    ys,xs=o; mm=(l[o]==i); a_=mm.sum()
    if 30*S*S<=a_<=400*S*S:
        bw,bhh=xs.stop-xs.start,ys.stop-ys.start
        if max(bw,bhh)/max(1,min(bw,bhh))<1.7 and a_/(bw*bhh)>.55:
            yy_,xx_=np.nonzero(mm); cx_,cy_=xs.start+xx_.mean(),ys.start+yy_.mean()
            if HS[int(cy_),int(cx_)]<0.05: DOTS.append((cx_,cy_,np.sqrt(a_/np.pi)*1.15))   # only dots sitting in the recess
for bx,by,r_ in DOTS: dome(HS,bx,by,r_,.14,.54); nd+=1
print('dots',nd)
dbgd=T2.copy()
for bx,by,r_ in DOTS: cv2.circle(dbgd,(int(bx),int(by)),int(r_)+2,(0,255,0),1)
cv2.imwrite(Z+'dots_dbg.png',dbgd[:,PW2:2*PW2])
# one exact period, symmetrized about the flower axes (j <-> 1-j on the cycle)
Hp=HS[:,PW2:2*PW2].copy()
idx=(1-np.arange(PW2))%PW2
Hp=0.5*(Hp+Hp[:,idx]); Hp=np.clip(Hp,0,1).astype(np.float32)
cv2.imwrite(Z+'band_period_v3.png',(Hp*65535).astype(np.uint16))
print('period',Hp.shape,'seam jump',float(np.abs(Hp[:,0]-Hp[:,-1]).max()))

def shade(hs):
    gg=hs*30*S
    gx=cv2.Sobel(gg,cv2.CV_32F,1,0,ksize=3)/8; gy=cv2.Sobel(gg,cv2.CV_32F,0,1,ksize=3)/8
    nn=np.dstack([-gx,-gy,np.ones_like(gx)]); nn/=np.linalg.norm(nn,axis=2,keepdims=True)
    Ld=np.array([-.4,-.6,.69]); Ld/=np.linalg.norm(Ld)
    dif=np.clip(nn@Ld,0,1); spec=np.clip((2*(nn@Ld)[...,None]*nn-Ld)[...,2],0,1)**25
    col=dif[...,None]*np.array([60,170,240])/255.*.85+spec[...,None]*.7+.04
    col=np.where(hs[...,None]>.05,col,np.array([18,30,45])/255.*(.6+.4*dif[...,None]))
    return (np.clip(col,0,1)*255).astype(np.uint8)
ref_p=T2[:,PW2:2*PW2]; rel=shade(Hp); vir=cv2.applyColorMap((Hp*255).astype(np.uint8),cv2.COLORMAP_VIRIDIS)
cv2.imwrite(Z+'v3_preview.png',np.vstack([ref_p,vir,rel]))
for nm,(a,b) in {'A':(0,700),'B':(850,1550)}.items():
    z=np.vstack([ref_p[:,a:b],rel[:,a:b]]); cv2.imwrite(Z+f'v3_zoom_{nm}.png',cv2.resize(z,None,fx=1.8,fy=1.8,interpolation=cv2.INTER_CUBIC))
tile=np.hstack([Hp[:,-700:],Hp[:,:700]]); cv2.imwrite(Z+'v3_seam.png',shade(tile))
