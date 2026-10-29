exec(open('tools/wip_v3/stage2.py').read().split("# beads in window coords")[0])
beads=pickle.load(open(Z+'beads.pkl','rb'))            # middle tile only (k=1)
# flower centre domes as (x,y,r) for all 3 tiles
CEN=[]
for k in range(3):
    CEN+= [(X(0,k),Y(133),24*S),(X(599,k),Y(128),26*S)]
BEADS_ALL=[]
for k in range(3):
    for (bx,by,br) in beads: BEADS_ALL.append((bx+(k-1)*PW2,by,br))
DOMES=BEADS_ALL+CEN
GAP=2.5*S
m0=m.copy()
yy,xx=np.mgrid[0:H2,0:W2]
for bx,by,br in DOMES:
    x0,x1=int(bx-br-GAP-3),int(bx+br+GAP+3); y0,y1=int(max(by-br-GAP-3,0)),int(min(by+br+GAP+3,H2))
    sub=((xx[y0:y1,x0:x1]-bx)**2+(yy[y0:y1,x0:x1]-by)**2)<(br+GAP)**2
    m0[y0:y1,x0:x1][sub]=0
# remove tiny specks created
l,n=ndi.label(m0); sz=ndi.sum(m0,l,range(1,n+1))
for i,s in enumerate(sz):
    if s<250*S*S: m0[l==i+1]=0

SIDE=[(0,60),(80,62),(-80,62),(105,172),(-105,172),(22,212),(-22,212)]
CENT=[(599,45),(556,72),(642,72),(518,123),(680,123),(556,195),(642,195)]
EXTRA=[(280,200)]   # manual markers for scroll shapes merged with petals
mk=np.zeros((H2,W2),np.int32); lid=0; mdbg=[]
dt0=ndi.distance_transform_edt(m0)
for k in range(3):
    for xp,y in SIDE+CENT+EXTRA:
        lid+=1; cx,cy=int(round(X(xp,k))),int(round(Y(y)))
        # snap to the most interior gold pixel nearby so the marker never lands in a slit
        R=14*S; y0,y1=max(cy-R,0),min(cy+R,H2); x0,x1=max(cx-R,0),min(cx+R,W2)
        if x1-x0<R: continue
        win=dt0[y0:y1,x0:x1]; iy,ix=np.unravel_index(np.argmax(win),win.shape)
        cx,cy=x0+ix,y0+iy
        cv2.circle(mk,(cx,cy),3*S,lid,-1); mdbg.append((cx,cy,lid))
mk[m0==0]=0
dt1=ndi.distance_transform_edt(m0)/S
elev=(1-Ls/255)+0.25*(1-np.clip(dt1/8,0,1))
lab=watershed(elev,mk,mask=m0>0)
# unmarked components -> own labels
rest=(m0>0)&(lab==0); l,n=ndi.label(rest); lab[rest]=l[rest]+lid
# carve thin gaps along boundaries between different labels
def lines(lab):
    b=np.zeros(lab.shape,bool)
    for dy,dx in ((0,1),(1,0),(1,1),(1,-1)):
        a=lab[max(0,-dy):H2-max(0,dy), max(0,-dx):W2-max(0,dx)]
        bb=lab[max(0,dy):, max(0,dx):][:a.shape[0],:a.shape[1]] if dx>=0 else lab[dy:, :W2+dx][:a.shape[0],:a.shape[1]]
        if dx<0: a=lab[:H2-dy, -dx:][:bb.shape[0],:bb.shape[1]]
        d=(a!=bb)&(a>0)&(bb>0)
        if dx>=0: b[:a.shape[0]-0,:a.shape[1]][:d.shape[0],:d.shape[1]]|=d
        else: b[:d.shape[0],-dx:][:, :d.shape[1]]|=d
    return b
ln=lines(lab)
ln=cv2.dilate(ln.astype(np.uint8),ell(1.2*S))>0
lab[ln]=0
np.savez_compressed(Z+'s3.npz',lab=lab,m0=m0)
# overlay
rng=np.random.RandomState(3); pal=rng.randint(60,255,(lab.max()+1,3)).astype(np.uint8); pal[0]=0
col=pal[lab]
ov=(0.45*T2+0.55*col).astype(np.uint8)
for cx,cy,i in mdbg: cv2.circle(ov,(cx,cy),5,(0,0,255),-1)
for bx,by,br in DOMES: cv2.circle(ov,(int(bx),int(by)),int(br),(255,255,255),1)
seg=ov[:,PW2:2*PW2]
cv2.imwrite(Z+'lab1.png',seg[:,:1300]); cv2.imwrite(Z+'lab2.png',seg[:,1100:])
print('labels',len(np.unique(lab))-1)
