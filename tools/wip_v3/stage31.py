import os
# stage 25 (WIP) = stage24 + leaf/stem slashes cut deep (VCUT) instead of a shallow 30% dent, smoother non-petal outlines (SDFSM). Output band_period_v31.png
# stage 24 (WIP) = stage23 + side-flower petals (top/UL/UR/bottom pair) follow the ref lit outline via closing instead of a convex hull (SCLS/SOPN/SSM). Output band_period_v31.png
# stage 23 (WIP) = stage22 + surface: rounder crown (CW), sharper edge (CENSIG), thin raised rim (RIMH), wider bevel (BEV). Output band_period_v23.png
# stage 22 (WIP) = stage21 + ref-style starburst gaps at the bead (WW0B/WLENB/RINGB). Output band_period_v23.png
# stage 21 (WIP) = stage20 + fewer/shorter/thinner/shallower veins (RIBD). Output band_period_v23.png
# stage 20 (WIP) = stage19 + same ref-outline rebuild for LL/LR. Output band_period_v23.png
# stage 19 (WIP) = stage17 + L/R petals rebuilt from ref lit region (LRTHR, LRSM). Output band_period_v23.png
# stage 18 (WIP) = stage17 + L/R rounded shoulders (LRR/LRS/LRA). Output band_period_v23.png
# stage 17 (WIP) = stage16 + UL/UR rounded outer tops (URR opening, URS smoothing). Output band_period_v23.png
# stage 16 (WIP) = stage15 + top petal rebuilt from ref width profile: no stalk, rounded cap, long taper tucked under UL/UR, faint lower midrib. Output band_period_v16.png
# stage 15 (WIP) = stage14 + tighter petal-to-bead gap (BEADC env), blunter L/R tips. Output band_period_v16.png
# stage 14 (WIP) = stage13 + spur removal (opening) on the 6 petals, shorter/fewer veins. Output band_period_v16.png
# stage 13 (WIP) = stage12 + centre-flower petals TOUCH neighbours (nearest-petal gap fill, thin slits kept between every pair, merge check). Output band_period_v16.png
# stage 12 (WIP) = stage11 + top petal follows MEASURED ref width profile (egg, narrower top), soft midrib, blunter L/R petal tips. Output band_period_v16.png
# stage 11 (WIP) = stage10 + top petal cap is a FULL ellipse (smooth oval shoulders, no pinched ears). Output band_period_v16.png
# stage 10 (WIP) = stage9 + rounded top-petal cap, thinner slits, extra fine veins on L/R petals. Output band_period_v16.png
# stage 9 (WIP) = stage8 + centre petals with narrow bevel (BEV), flatter crown (CW), deeper veins (RIBD). Output band_period_v16.png
# stage 8 (WIP) = stage7 + top centre petal tucked UNDER the UL/UR petals (own wider footprint, hidden under neighbours). Output band_period_v16.png
# stage 6 (WIP): stage5 generalised to BOTH flowers (side + centre). Output band_period_v16.png
exec(open('tools/wip_v3/stage3.py').read())
# stage 7 (WIP): stage6 + centre-flower petals rebuilt as SMOOTH parametric leaf shapes (width profile measured from the ref region, smoothed) instead of hull facets
FLW=[(0,133,24,range(0,7)),(599,128,26,range(7,14))]   # (axis x in period, y, dome r, marker idx in tile)
def flw_of(i):
    m=(i-1)%15
    return FLW[0] if m<7 else FLW[1] if m<14 else None
def flw_pos(f,cmx,cmy):                      # nearest tile copy of flower f -> (fx,fy,k)
    k=min(range(3),key=lambda kk:np.hypot(cmx-X(f[0],kk),cmy-Y(f[1])))
    return X(f[0],k),Y(f[1]),k
# flower polish (no slit bites, pointed tips, midribs, pillowy petals)

# --- rebuild centre petals as clean convex leaf shapes (fills the slit bites in the inner ends) ---
WSIG=3.2
BEV=4.5; CW=float(os.environ.get('CW',0.40)); RIBD=float(os.environ.get('RIBD',0.40)); CENSIG=float(os.environ.get('CENSIG',1.2)); RIMH=float(os.environ.get('RIMH',0.06)); BEV=float(os.environ.get('BEV',6.0))   # centre petals: narrow rounded bevel, flat-ish crown, visible engraved veins
NOHULL_W0=6.0; NOHULL_SLOPE=0.60
SCLS=float(os.environ.get('SCLS',24)); SOPN=float(os.environ.get('SOPN',10)); SSM=float(os.environ.get('SSM',4.0))   # stage24: side petals: closing / opening radius (1x px), smoothing
TAPER_W0=3.0; TAPER_SLOPE=0.78; SMOOTH_HULL=3.0   # leaf taper toward the dome, facet rounding
import os; WEDGE_LEN=float(os.environ.get('WLEN',52)); WEDGE_W0=float(os.environ.get('WW0',4.8))                 # 1x px: wedge length from dome edge, half-width at the dome
CZ0=np.zeros((H2,W2),np.uint8)
for k in range(3):
    for f in FLW: cv2.circle(CZ0,(int(X(f[0],k)),int(Y(f[1]))),int(215*S),1,-1)
for k in range(3):                                   # bottom pair of the side flower is one merged label -> split at the axis
    ia,ib=15*k+6,15*k+7                                # marker idx 5 (BR) and 6 (BL) of tile k (ids are 1-based)
    un=(lab==ia)|(lab==ib)
    if un.sum()<500: continue
    axx=int(X(0,k)); cols=np.arange(W2)[None,:]
    lab[un&(cols<axx)]=ib; lab[un&(cols>=axx)]=ia
cids=[i for i in np.unique(lab[CZ0>0]) if i>0 and ((i-1)%15)<14 and i<=45]
hulls={}
for i in cids:
    reg=((lab==i)&(CZ0>0)).astype(np.uint8)
    if reg.sum()<150*S*S: continue
    cs,_=cv2.findContours(reg,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    _yy0,_xx0=np.nonzero(reg); _fc=flw_of(i)
    if _fc is not None and _fc[0]==599:                 # ---- centre flower: smooth parametric leaf ----
        _fx,_fy,_k=flw_pos(_fc,_xx0.mean(),_yy0.mean())
        _r=np.hypot(_xx0-_fx,_yy0-_fy); _j=np.argmax(_r); _a=np.arctan2(_yy0[_j]-_fy,_xx0[_j]-_fx)
        _a=0.5*_a+0.5*np.arctan2(_yy0.mean()-_fy,_xx0.mean()-_fx)       # axis between tip direction and centroid direction
        _ux,_uy=np.cos(_a),np.sin(_a)
        _t=((_xx0-_fx)*_ux+(_yy0-_fy)*_uy-_fc[2]*S)/S; _p=(-(_xx0-_fx)*_uy+(_yy0-_fy)*_ux)/S
        _tm=int(_t.max())+1; _nb=np.arange(-2,_tm+1)
        _lo=np.full(len(_nb),np.nan); _hi=np.full(len(_nb),np.nan)
        _bi=np.floor(_t).astype(int)+2
        for _b in range(len(_nb)):
            _s=_p[_bi==_b]
            if len(_s)>2: _lo[_b]=np.percentile(_s,0.5)-0.8; _hi[_b]=np.percentile(_s,99.5)+0.8
        _ok=~np.isnan(_lo)
        _lo=np.interp(_nb,_nb[_ok],_lo[_ok]); _hi=np.interp(_nb,_nb[_ok],_hi[_ok])
        _w=0.5*(_hi-_lo); _c=0.5*(_hi+_lo)
        _w=np.minimum(_w,TAPER_W0+TAPER_SLOPE*np.maximum(_nb+2,0)+1.0)
        _pad=18; _wp=np.concatenate([_w,np.linspace(_w[-1]*0.5,0,_pad)]); _nbp=np.arange(-2,_tm+1+_pad)
        _wp=ndi.gaussian_filter1d(_wp,WSIG,mode='nearest'); _cp=ndi.gaussian_filter1d(np.concatenate([_c,np.full(_pad,_c[-1])]),9,mode='nearest')
        _by0,_by1=int(max(_fy-215*S,0)),int(min(_fy+215*S,H2)); _bx0,_bx1=int(max(_fx-215*S,0)),int(min(_fx+215*S,W2))
        _gy,_gx=np.mgrid[_by0:_by1,_bx0:_bx1]
        _T=((_gx-_fx)*_ux+(_gy-_fy)*_uy-_fc[2]*S)/S; _P=(-(_gx-_fx)*_uy+(_gy-_fy)*_ux)/S
        _W=np.interp(_T,_nbp,_wp,left=0,right=0); _C=np.interp(_T,_nbp,_cp)
        hm=np.zeros((H2,W2),np.uint8); hm[_by0:_by1,_bx0:_bx1]=((np.abs(_P-_C)<=_W)&(_W>0.7)&(_T>=-1)).astype(np.uint8)
        hm=(g(hm.astype(np.float32),1.0*S)>0.5).astype(np.uint8)
        hulls[i]=hm; continue
    NOHULL=((i-1)%15) in (3,4)          # side flower R/L petals run into long scroll tails: a convex hull would swallow the recess
    if (not NOHULL) and _fc is not None and _fc[0]==0:   # ---- stage24: side flower top/UL/UR/bottom pair: follow the ref lit outline (hole fill + closing), not a convex hull ----
        _fx,_fy,_k=flw_pos(_fc,_xx0.mean(),_yy0.mean()); _R=int(260*S)
        _y0,_y1=max(int(_fy)-_R,0),min(int(_fy)+_R,H2); _x0,_x1=max(int(_fx)-_R,0),min(int(_fx)+_R,W2)
        _lw=lab[_y0:_y1,_x0:_x1]
        _sb=ndi.binary_fill_holes(_lw==i).astype(np.uint8)
        _sb=cv2.morphologyEx(_sb,cv2.MORPH_CLOSE,ell(SCLS*S))
        _sb[(_lw>0)&(_lw!=i)]=0                                   # never grow into a neighbouring petal
        for _bx,_by,_br in DOMES:                                  # nor into a bead disc
            if _x0-_br<_bx<_x1+_br and _y0-_br<_by<_y1+_br: cv2.circle(_sb,(int(_bx-_x0),int(_by-_y0)),int(_br+GAP),0,-1)
        _sb=cv2.morphologyEx(_sb,cv2.MORPH_OPEN,ell(SOPN*S))       # drop lit bead rims / ears
        _l2,_n2=ndi.label(_sb)
        if _n2>1: _sb=(_l2==(1+int(np.argmax(ndi.sum(_sb,_l2,range(1,_n2+1)))))).astype(np.uint8)
        _sb=(g(_sb.astype(np.float32),SSM*S)>0.5).astype(np.uint8)
        hm=np.zeros((H2,W2),np.uint8); hm[_y0:_y1,_x0:_x1]=_sb
    elif NOHULL:
        hm=reg.copy()
        _f=flw_of(i); _y,_x=np.nonzero(reg); _fx,_fy,_k=flw_pos(_f,_x.mean(),_y.mean())
        _w0,_w1=int(max(_fx-170*S,0)),int(min(_fx+170*S,W2)); _h0,_h1=int(max(_fy-170*S,0)),int(min(_fy+170*S,H2))
        hm[_h0:_h1,_w0:_w1]=cv2.morphologyEx(hm[_h0:_h1,_w0:_w1],cv2.MORPH_CLOSE,ell(16*S))   # fill the wide slit fork; re-cut as a thin groove below
        _near=np.hypot(_x-_fx,_y-_fy)<110*S
        if _near.sum()>50:
            _a=np.arctan2(_y[_near].mean()-_fy,_x[_near].mean()-_fx); _ux,_uy=np.cos(_a),np.sin(_a)
            _gy,_gx=np.mgrid[0:H2,0:W2] if False else (None,None)
            _by0,_by1=int(max(_fy-110*S,0)),int(min(_fy+110*S,H2)); _bx0,_bx1=int(max(_fx-110*S,0)),int(min(_fx+110*S,W2))
            _yy,_xx=np.mgrid[_by0:_by1,_bx0:_bx1]; _t=(_xx-_fx)*_ux+(_yy-_fy)*_uy-(_f[2]*S); _p=np.abs(-(_xx-_fx)*_uy+(_yy-_fy)*_ux)
            _cut=(_p>(NOHULL_W0*S+NOHULL_SLOPE*np.maximum(_t,0)))&(np.hypot(_xx-_fx,_yy-_fy)<110*S)
            hm[_by0:_by1,_bx0:_bx1][_cut]=0
    else:
        pts=np.vstack(cs); hm=np.zeros((H2,W2),np.uint8); cv2.fillConvexPoly(hm,cv2.convexHull(pts),1)
    # taper the inner end toward the dome (leaf shape): half-width <= TAPER_W0 + TAPER_SLOPE*(distance from dome edge)
    if not NOHULL:
        yy_,xx_=np.nonzero(reg); cmx,cmy=xx_.mean(),yy_.mean()
        f=flw_of(i); fx,fy,k=flw_pos(f,cmx,cmy)
        a_=np.arctan2(cmy-fy,cmx-fx); ux,uy=np.cos(a_),np.sin(a_)
        by0,by1=int(max(fy-215*S,0)),int(min(fy+215*S,H2)); bx0,bx1=int(max(fx-215*S,0)),int(min(fx+215*S,W2))
        gy_,gx_=np.mgrid[by0:by1,bx0:bx1]; tt=(gx_-fx)*ux+(gy_-fy)*uy-(f[2]*S); pp=np.abs(-(gx_-fx)*uy+(gy_-fy)*ux)
        keep=(pp<=(TAPER_W0*S+TAPER_SLOPE*np.maximum(tt,0)))&(tt>-2*S)
        sub=hm[by0:by1,bx0:bx1]; sub[~keep]=0
    if not NOHULL: hm=(g(hm.astype(np.float32),SMOOTH_HULL*S)>0.46).astype(np.uint8)            # round the hull facets
    hulls[i]=hm
ids=list(hulls)
anyh=np.zeros((H2,W2),bool)
for hm in hulls.values(): anyh|=hm>0
anyh&=(lab==0)|np.isin(lab,ids)
own=np.zeros((H2,W2),np.int16); best=np.full((H2,W2),np.inf,np.float32)
for n,i in enumerate(ids):                        # running argmin (stacking all EDTs ran out of memory)
    d_=ndi.distance_transform_edt(lab!=i).astype(np.float32); u_=d_<best; own[u_]=n; best[u_]=d_[u_]
del d_,u_,best
newlab=lab.copy()
for n,i in enumerate(ids):
    sel=anyh&(own==n)&(hulls[i]>0)
    newlab[(lab==i)&(CZ0>0)&(hulls[i]==0)]=0          # remove original pixels outside the tapered leaf shape
    newlab[sel]=i

# ---- stage13: centre-flower petals touch their neighbours: fill the narrow gap between two petals (owner = nearest petal) ----
import os
ROUT=float(os.environ.get('ROUT',115))   # gap-fill reach shrinks with radius so outer corners stay rounded (no wings)
MOAT=float(os.environ.get('MOAT',20))
BASER=float(os.environ.get('BASER',62))
BEADC=float(os.environ.get('BEADC',0.8))
FILL_DM=float(os.environ.get('FILL_DM',26.0))     # 1x px: gaps narrower than 2*FILL_DM are closed (slits are re-cut below)
_PY=[0, 6.5, 7, 8, 10, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 80, 88, 96, 102, 108, 114, 120, 126, 132, 138, 146, 152]
_PW=[0, 0, 8, 11.5, 13, 14.5, 17.5, 21.5, 25.5, 29.5, 32.5, 35.5, 38.5, 41.5, 43.5, 45.5, 47.5, 49.5, 50.5, 51.5, 52.5, 53.5, 52.5, 53, 50, 46, 40, 33, 25, 17, 10, 3, 0]
_PY2=[0, 6.5, 7, 8, 10, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 80, 88, 96, 98, 102, 108, 114, 120, 128, 136, 144]   # footprint kept free of UL/UR fill (ref-visible part; below row ~98 UL/UR overlap the top petal)
_PW2=[0, 0, 8, 11.5, 13, 14.5, 17.5, 21.5, 25.5, 29.5, 32.5, 35.5, 38.5, 41.5, 43.5, 45.5, 47.5, 49.5, 50.5, 51.5, 52.5, 53.5, 52.5, 53, 53, 16, 13, 11, 9, 6, 3, 0]
FILLED=0
for _k in range(3):
    _fx,_fy=X(599,_k),Y(128); _R=int(140*S)
    _pid=[15*_k+j for j in (9,10,11,12,13,14)]            # UL, UR, L, R, LL, LR (top petal 15k+8 is built separately)
    _x0,_x1=int(max(_fx-_R,0)),int(min(_fx+_R,W2)); _y0,_y1=int(max(_fy-_R,0)),int(min(_fy+_R,H2))
    _sub=newlab[_y0:_y1,_x0:_x1]
    _ds=np.stack([ndi.distance_transform_edt(_sub!=q).astype(np.float32)/S if (_sub==q).any() else np.full(_sub.shape,1e3,np.float32) for q in _pid])
    _ow=np.argmin(_ds,0); _sr=np.sort(_ds,0); _d1,_d2=_sr[0],_sr[1]
    _gy,_gx=np.mgrid[_y0:_y1,_x0:_x1]
    _lens=np.abs(_gx-_fx)<=np.interp(_gy[:,0],_PY2,_PW2,left=0,right=0)[:,None]+3*S    # top petal footprint stays free
    _rr=np.hypot(_gx-_fx,_gy-_fy)/S
    _cand=(_sub==0)&(_d2<=FILL_DM*np.clip((ROUT-_rr)/(ROUT-55.0),0.2,1.0))&(~_lens)&(_rr<125)&(_rr>(26+BEADC))
    _ids=np.array(_pid)[_ow]
    _sub[_cand]=_ids[_cand]; FILLED+=int(_cand.sum())
    _cb=(_sub==0)&(~_lens)&(_rr<BASER)&(_rr>(26+BEADC))   # stage15: petal bases run right up to the bead (wedge slits re-cut below)
    _sub[_cb]=_ids[_cb]; FILLED+=int(_cb.sum())
    _dm=np.minimum(_ds[0],_ds[1]); _own=np.where(_ds[0]<=_ds[1],_pid[0],_pid[1])      # stage16: UL/UR overlap the lower sides of the top petal (no dark moat)
    _cm=(_sub==0)&(~_lens)&(_gy>=96)&(_gy<165)&(np.abs(_gx-_fx)<66)&(_dm<=MOAT)
    _sub[_cm]=_own[_cm]; FILLED+=int(_cm.sum())
print('stage13 gap-fill px',FILLED)
# dark wedge gaps between neighbouring petals: widest at the dome, tapering outwards (as in the reference)
cen_info={}
for i in ids:
    yy_,xx_=np.nonzero(newlab==i)
    if len(xx_)==0: continue
    f=flw_of(i); fx,fy,k=flw_pos(f,xx_.mean(),yy_.mean())
    if np.hypot(xx_.mean()-fx,yy_.mean()-fy)<200*S:
        cen_info.setdefault((f[0],k),[]).append(np.arctan2(yy_.mean()-fy,xx_.mean()-fx))
for (fxp,k),angs in cen_info.items():
    if fxp==0: continue                                   # stage24: side flower: the centroid-angle wedge cut a sliver into the L petal; gaps come from the label lines
    f=[q for q in FLW if q[0]==fxp][0]
    angs=np.sort(np.array(angs)); fx,fy=X(f[0],k),Y(f[1])
    nxt=np.roll(angs,-1); nxt[-1]+=2*np.pi
    for a,b in zip(angs,nxt):
        gdir=(a+b)/2; half=(b-a)/2
        if abs(((gdir+np.pi/2+np.pi)%(2*np.pi))-np.pi)<np.radians(35): continue   # top-petal gaps are already clean slits; the wedge hooked the UL/UR petals
        r0=(f[2]+1.0)*S; L=WEDGE_LEN*S; w0=WEDGE_W0*S
        ux,uy=np.cos(gdir),np.sin(gdir); nx,ny=-uy,ux
        poly=np.array([[fx+ux*r0+nx*w0,fy+uy*r0+ny*w0],[fx+ux*(r0+L)+nx*0.4*S,fy+uy*(r0+L)+ny*0.4*S],
                       [fx+ux*(r0+L)-nx*0.4*S,fy+uy*(r0+L)-ny*0.4*S],[fx+ux*r0-nx*w0,fy+uy*r0-ny*w0]]).astype(np.int32)
        cv2.fillPoly(newlab,[poly],0)
# dome clearance + gaps between petals (wider close to the dome, like the wedge gaps in the reference)
for k in range(3):
    for f in FLW: cv2.circle(newlab,(int(X(f[0],k)),int(Y(f[1]))),int((f[2]+BEADC)*S),0,-1)
lnb=lines(newlab); lnb=cv2.dilate(lnb.astype(np.uint8),ell(1.0*S))>0
near=np.zeros((H2,W2),np.uint8)
for k in range(3):
    for f in FLW[:1]: cv2.circle(near,(int(X(f[0],k)),int(Y(f[1]))),int(95*S),1,-1)   # stage13: wide carve only at side flower
lnw=cv2.dilate(lines(newlab).astype(np.uint8),ell(2.0*S))>0
newlab[lnb|(lnw&(near>0))]=0
lab=newlab
import os
LRTHR=float(os.environ.get('LRTHR',190)); LRSM=float(os.environ.get('LRSM',1.5)); LRSL=float(os.environ.get('LRSL',2.5))
# ---- stage19: L/R petals rebuilt from the reference lit region (plump convex sides, pointed tip) ----
_V=cv2.cvtColor(T2,cv2.COLOR_BGR2HSV)[...,2]
_lm=cv2.morphologyEx((_V>LRTHR).astype(np.uint8),cv2.MORPH_OPEN,ell(3*S)); _ll,_ln=ndi.label(_lm)
for _k in range(3):
    _fx,_fy=int(X(599,_k)),int(Y(128))
    for _q in (15*_k+11,15*_k+12,15*_k+13,15*_k+14):
        _yy,_xx=np.nonzero(lab==_q)
        _side=-1 if _xx.mean()<_fx else 1
        _sy,_sx=int(_yy.mean()),int(_xx.mean())
        _c=_ll[_sy,_sx]
        if _c==0:                                              # centroid not lit: take the most common lit comp under the current petal
            _vals=_ll[lab==_q]; _vals=_vals[_vals>0]; _c=int(np.bincount(_vals).argmax()) if len(_vals) else 0
        if _c>0: print('stage20 petal',_q-15*_k,'ref comp area(1x)',int((_ll==_c).sum()/S/S),'cur area',int((lab==_q).sum()/S/S))
        if _c==0: print('stage19: no ref comp for',_q); continue
        _cy,_cx=np.nonzero(_ll==_c); _hm=np.zeros((H2,W2),np.uint8)
        cv2.fillConvexPoly(_hm,cv2.convexHull(np.stack([_cx,_cy],1).astype(np.int32)),1)   # hull fills the vein notches near the bead
        _t=g(_hm.astype(np.float32),LRSM*S)>0.5
        _y0,_y1=max(_fy-130*S,0),min(_fy+130*S,H2); _x0,_x1=max(_fx-130*S,0),min(_fx+130*S,W2)
        _yg,_xg=np.mgrid[_y0:_y1,_x0:_x1]
        _tt=np.zeros((H2,W2),bool); _tt[_y0:_y1,_x0:_x1]=(np.hypot(_xg-_fx,_yg-_fy)>(26+BEADC+0.5)*S)
        _t&=_tt
        lab[(lab==_q)&(~_t)]=0
        lab[_t&((lab==0)|(lab==_q))]=_q
        _nb=np.isin(lab,[15*_k+j for j in (9,10,11,12,13,14) if 15*_k+j!=_q])
        _nbd=cv2.dilate(_nb.astype(np.uint8),ell(LRSL*S))>0                          # keep a thin slit to every neighbour
        lab[(lab==_q)&_nbd]=0
# ---- stage22: ref-style starburst: wide dark wedge gaps between petals at the bead (tapering outwards) + dark ring around the bead ----
WW0B=float(os.environ.get('WW0B',8.0)); WLENB=float(os.environ.get('WLENB',50.0)); RINGB=float(os.environ.get('RINGB',3.0))
for _k in range(3):
    _fx,_fy=X(599,_k),Y(128); _pid=[15*_k+j for j in (9,10,11,12,13,14)]
    _an=[]
    for _q in _pid:
        _yy,_xx=np.nonzero(lab==_q); _an.append(np.arctan2(_yy.mean()-_fy,_xx.mean()-_fx))
    _an=np.sort(np.array(_an)); _nx=np.roll(_an,-1); _nx[-1]+=2*np.pi
    for _a,_b in zip(_an,_nx):
        _gd=(_a+_b)/2
        if abs(((_gd+np.pi/2+np.pi)%(2*np.pi))-np.pi)<np.radians(35): continue      # top gap (top petal sits there) stays a clean slit
        _r0=(26+0.5)*S; _L=WLENB*S; _w0=WW0B*S
        _ux,_uy=np.cos(_gd),np.sin(_gd); _nx_,_ny_=-_uy,_ux
        _poly=np.array([[_fx+_ux*_r0+_nx_*_w0,_fy+_uy*_r0+_ny_*_w0],[_fx+_ux*(_r0+_L)+_nx_*0.4*S,_fy+_uy*(_r0+_L)+_ny_*0.4*S],
                        [_fx+_ux*(_r0+_L)-_nx_*0.4*S,_fy+_uy*(_r0+_L)-_ny_*0.4*S],[_fx+_ux*_r0-_nx_*_w0,_fy+_uy*_r0-_ny_*_w0]]).astype(np.int32)
        _pm=np.zeros((H2,W2),np.uint8); cv2.fillPoly(_pm,[_poly],1)
        lab[(_pm>0)&np.isin(lab,_pid)]=0
    _cr=np.zeros((H2,W2),np.uint8); cv2.circle(_cr,(int(_fx),int(_fy)),int((26+RINGB)*S),1,-1)
    lab[(_cr>0)&np.isin(lab,_pid)]=0
# ---- stage13 merge check: each of the 6 filled petals must stay its own component, with a slit to every neighbour ----
for _k in range(3):
    _pid=[15*_k+j for j in (9,10,11,12,13,14)]
    for q in _pid:                                      # drop 1-px specks left by the slit carve
        _l0,_n0=ndi.label(lab==q,structure=np.ones((3,3)))
        for _j in range(1,_n0+1):
            if (_l0==_j).sum()<50: lab[_l0==_j]=0
    _u=np.isin(lab,_pid); _l,_n=ndi.label(_u,structure=np.ones((3,3)))
    _cnt=[len(np.unique(_l[lab==q]))-(1 if 0 in np.unique(_l[lab==q]) else 0) for q in _pid]
    print('tile',_k,'petal comps (8-conn, expect 6):',_n,'per-label pieces',_cnt)
# ---- stage14: remove thin spurs/ears at petal shoulders (opening per petal, keep largest piece) ----
OPEN_R2=float(os.environ.get('OPEN_R2',9.0))
SMO=float(os.environ.get('SMO',3.0))
OPEN_R=float(os.environ.get('OPEN_R',5.5))
URR=float(os.environ.get('URR',16.0)); URS=float(os.environ.get('URS',6.0))
for _k in range(3):
    for q in [15*_k+j for j in (9,10,11,12,13,14)]:
        m=(lab==q).astype(np.uint8)
        if not m.any(): continue
        mo=cv2.morphologyEx(m,cv2.MORPH_OPEN,ell(OPEN_R*S))
        _fx_,_fy_=X(599,_k),Y(128); _yy_,_xx_=np.mgrid[0:H2,0:W2]
        _ang=np.degrees(np.arctan2(np.abs(_yy_-_fy_),np.abs(_xx_-_fx_))); _rrz=np.hypot(_xx_-_fx_,_yy_-_fy_)/S
        _zone=(_ang>=15)&(_ang<=58)&(_rrz>45)                  # shoulders between petals: stronger opening kills fin-like fill remnants (tips at ~0 deg stay)
        mo=np.where(_zone,cv2.morphologyEx(m,cv2.MORPH_OPEN,ell(OPEN_R2*S)),mo).astype(np.uint8)
        l_,n_=ndi.label(mo)
        if n_>1:
            sz_=ndi.sum(mo,l_,range(1,n_+1)); mo=(l_==(1+int(np.argmax(sz_)))).astype(np.uint8)
        lab[(m>0)&(mo==0)]=0
        mb=g(((lab==q)).astype(np.float32),SMO)>0.5          # stage16: round corners / drop nubs (remove-only smoothing)
        lab[((lab==q))&(~mb)]=0
        if (q%15) in (9,10):                                  # stage17: UL/UR plump oval tops: round outer corners (remove-only, big opening + smoothing, outer zone only)
            m2=(lab==q).astype(np.uint8)
            _out=(_rrz>60)
            mo2=np.where(_out,cv2.morphologyEx(m2,cv2.MORPH_OPEN,ell(URR*S)),m2).astype(np.uint8)
            ms2=g(mo2.astype(np.float32),URS*S)>0.5
            mo2=np.where(_out,mo2&ms2,mo2).astype(np.uint8)
            l_,n_=ndi.label(mo2)
            if n_>1:
                sz_=ndi.sum(mo2,l_,range(1,n_+1)); mo2=(l_==(1+int(np.argmax(sz_)))).astype(np.uint8)
            lab[(m2>0)&(mo2==0)]=0

sm=lambda a:a*a*(3-2*a)
# leaf/scroll veins -> shallow grooves (not inside flower zones)
inner=cv2.erode(m0,ell(9*S))
VTH=float(os.environ.get('VTH',90)); VIN=float(os.environ.get('VIN',4)); VMIN=float(os.environ.get('VMIN',30))
_g8s=g(cv2.cvtColor(T2,cv2.COLOR_BGR2GRAY).astype(np.float32),0.8*S)     # stage25: slashes = very dark pixels inside the shapes (solid, not the blackhat ring)
vein=((_g8s<VTH)&(cv2.erode(m0,ell(VIN*S))>0)&(zone<.5)).astype(np.uint8)
vein=cv2.morphologyEx(vein,cv2.MORPH_OPEN,ell(1.5*S))
l,n=ndi.label(vein); sz=ndi.sum(vein,l,range(1,n+1))
keep=np.zeros(n+1,bool); keep[1:]=sz>=VMIN*S*S; vein=keep[l].astype(np.uint8)
VCUT=float(os.environ.get('VCUT',1.0)); VSM=float(os.environ.get('VSM',0.7)); SDFSM=float(os.environ.get('SDFSM',5.0))
vf=np.ones((H2,W2),np.float32)                 # stage25: no shallow dent; slashes are cut deep below
vcut=0   # set below (needs the final vein mask)
# petal slits -> soft grooves that reach the recess floor
from skimage.morphology import skeletonize
sk=cv2.dilate(skeletonize(slit>0).astype(np.uint8),ell(2*S))        # narrow slits -> crisp ~2px engraved lines
wide=cv2.erode(slit,ell(2*S))                                        # wide slots keep their body, minus the shadow rim
sl=np.clip(g(np.maximum(sk,wide).astype(np.float32),0.9*S)*2.2,0,1)

CZ=np.zeros((H2,W2),np.uint8)
for k in range(3):
    for f in FLW: cv2.circle(CZ,(int(X(f[0],k)),int(Y(f[1]))),int(215*S),1,-1)
slk=np.clip(g(sk.astype(np.float32),0.9*S)*2.2,0,1)                  # thin skeleton-only slit grooves
sl=sl*(1-CZ)                                   # no slit carving inside the flowers (it bit the petals)
NH=np.isin(lab,[q for q in range(1,46) if ((q-1)%15) in (3,4)]).astype(np.float32)
sl=np.maximum(sl,slk*CZ*g(cv2.erode(NH.astype(np.uint8),ell(6*S)).astype(np.float32),1.5*S))   # ...but keep thin grooves inside the long side R/L petals
HS=np.zeros((H2,W2),np.float32)
CPET=[]                                        # (label id, tile k) of centre petals
PADp=40*S
STEMSM=float(os.environ.get('STEMSM',7.0)); DSM=float(os.environ.get('DSM',7.0)); PILS=float(os.environ.get('PILS',0.40)); PILWS=float(os.environ.get('PILWS',9))
DLMIN=float(os.environ.get('DLMIN',160))
RAYW=float(os.environ.get('RAYW',0.7)); RAYB=float(os.environ.get('RAYB',1.0))
PILC=float(os.environ.get('PILC',0.65)); PILN=float(os.environ.get('PILN',0.70)); PILW=float(os.environ.get('PILW',16)); EDW=float(os.environ.get('EDW',3.0))
for i,o in enumerate(ndi.find_objects(lab),1):
    if o is None: continue
    ys,xs=o
    y0,y1=max(ys.start-PADp,0),min(ys.stop+PADp,H2); x0,x1=max(xs.start-PADp,0),min(xs.stop+PADp,W2)
    R=(lab[y0:y1,x0:x1]==i)
    if ((i-1)%15)==7 and i<=45: continue             # top centre petal handled separately (tucked under UL/UR)
    if R.sum()<150*S*S: continue
    R=cv2.morphologyEx(R.astype(np.uint8),cv2.MORPH_OPEN,ell(3*S))>0      # drop hair-thin spikes
    if R.sum()<150*S*S: continue
    sdf=(ndi.distance_transform_edt(R)-ndi.distance_transform_edt(~R)).astype(np.float32)
    cyy,cxx=np.nonzero(lab[y0:y1,x0:x1]==i); cmx,cmy=cxx.mean()+x0,cyy.mean()+y0
    _f=flw_of(i); cen=False
    if _f is not None:
        _fx,_fy,_k=flw_pos(_f,cmx,cmy); cen=np.hypot(cmx-_fx,cmy-_fy)<200*S
    if cen: CPET.append((i,cmx,cmy))
    petal=((i-1)%15)<14 and i<=45                      # marker ids: 15 per tile, last one is the scroll
    sdf=g(sdf,(CENSIG if cen else 3.6 if petal else STEMSM)*S)                                   # smooth contour (no jaggies, no ribbing)
    d=np.maximum(sdf,0)/S                              # inward distance in 1x px
    if (not petal) and (not cen): d=g(d,DSM*S)*(sdf>0)    # D1: round off the medial-axis crease of stems/crescents
    loc=g(cv2.dilate(d,ell(31*S)),5*S)
    xe=np.clip(d/(BEV if cen else (PILW if petal else PILWS)),0,1); xc=np.clip(d/np.clip(loc,6,26),0,1)
    cw=PILC if cen else (PILN if petal else PILS)
    h=((1-cw)*sm(xe)+cw*np.sqrt(1-(1-xc)**2))*vf[y0:y1,x0:x1]
    if cen: h=np.clip(h+RIMH*np.exp(-((d-2.5)/1.4)**2)*vf[y0:y1,x0:x1],0,1.05)     # stage23: thin raised rim
    hr=np.clip(0.5+sdf/EDW,0,1)*(0.28+0.72*h)
    HS[y0:y1,x0:x1]=np.maximum(HS[y0:y1,x0:x1],hr)
LENS_W=52; LENS_YM=78; LENS_H=66
for k in range(3):                              # top centre petal: wider footprint that disappears UNDER the UL/UR petals
    T_,UL_,UR_=15*k+8,15*k+9,15*k+10
    Tm=(lab==T_)
    if Tm.sum()<150*S*S: continue
    Nm=((lab==UL_)|(lab==UR_))
    _yy,_xx=np.nonzero(Tm); y0_,y1_=_yy.min(),_yy.max()
    _R=(LENS_H**2+LENS_W**2)/(2.0*LENS_W); _d=_R-LENS_W; _cx=X(599,k)         # ogive (pointed oval) = lens of two circles; widest at LENS_YM, tip at LENS_YM-LENS_H
    _gy,_gx=np.mgrid[0:H2,0:W2]
    lens=(((_gx-(_cx+_d))**2+(_gy-LENS_YM)**2)<=_R*_R)&(((_gx-(_cx-_d))**2+(_gy-LENS_YM)**2)<=_R*_R)
    ell_=(((_gx-_cx)/LENS_W)**2+((_gy-LENS_YM)/LENS_H)**2)<=1.0                    # blunt oval upper half (matches ref widths at y=40/20)
    _py=_PY; _pw=_PW
    _wy=np.interp(_gy[:,0],_py,_pw,left=0,right=0)[:,None]
    shape=np.abs(_gx-_cx)<=_wy
    Wm=(shape&(~np.isin(lab,[q for q in np.unique(lab) if q not in (0,T_)])))   # above the widest row: exactly the oval (drops label spike)
    Wm=(g(Wm.astype(np.float32),2.0*S)>0.5)
    dc=np.zeros((H2,W2),np.uint8); cv2.circle(dc,(int(X(599,k)),int(Y(128))),int((26+2.2)*S),1,-1); Wm&=(dc==0)
    sdf=(ndi.distance_transform_edt(Wm)-ndi.distance_transform_edt(~Wm)).astype(np.float32); sdf=g(sdf,2.6*S)
    d=np.maximum(sdf,0)/S; loc=g(cv2.dilate(d,ell(31*S)),5*S)
    xe=np.clip(d/BEV,0,1); xc=np.clip(d/np.clip(loc,6,26),0,1)
    hw=((1-CW)*sm(xe)+CW*np.sqrt(1-(1-xc)**2))*vf
    hw=np.clip(hw+RIMH*np.exp(-((d-2.5)/1.4)**2)*vf,0,1.05)
    hw=np.clip(0.5+sdf,0,1)*(0.28+0.72*hw)
    dN=ndi.distance_transform_edt(~Nm)/S
    _mr=np.exp(-((_gx-_cx)/(1.8*S))**2)*np.clip((_gy-62)/16.0,0,1)*np.clip((132-_gy)/16.0,0,1)
    hw=(hw+0.025*_mr*(hw>0.3)).astype(np.float32)
    hw*=0.80+0.20*sm(np.clip(dN/9.0,0,1))                    # sinks as it goes under the neighbours' edges
    wN=np.clip(g(Nm.astype(np.float32),1.0*S)*1.6,0,1)
    HS=np.maximum(HS,hw*(1-wN))
HS*=(1-sl)
rib=np.zeros((H2,W2),np.float32)
for (i,cmx,cmy) in CPET:
    f=flw_of(i); fx,fy,k=flw_pos(f,cmx,cmy)
    ang=np.arctan2(cmy-fy,cmx-fx); ux,uy=np.cos(ang),np.sin(ang)
    reg=(lab==i); ts=np.arange(0,260*S,1.0)
    px=(fx+ux*ts).astype(int).clip(0,W2-1); py=(fy+uy*ts).astype(int).clip(0,H2-1)
    inr=reg[py,px]
    if not inr.any(): continue
    t0=ts[np.argmax(inr)]; t1=ts[len(inr)-1-np.argmax(inr[::-1])]
    _lr=abs(np.sin(ang))<0.5                              # stage21: few thin short veins like the ref (L/R: midrib + 2 short side lines near the bead; others: midrib + 2 very short)
    _vl=[(0,6,.62,.60),(0.20,10,.40,.45),(-0.20,10,.40,.45),(0.40,10,.28,.36),(-0.40,10,.28,.36)] if _lr else [(0,6,.55,.55),(0.18,10,.34,.40),(-0.18,10,.34,.40),(0.36,10,.24,.32),(-0.36,10,.24,.32)]
    for da,f0,f1,wk in _vl:   # centre vein + two fine side veins
        a0=t0+f0*S; a1=t0+f1*(t1-t0)
        vx,vy=np.cos(ang+da),np.sin(ang+da)
        for t in np.arange(a0,a1,S*0.5):
            u=(t-a0)/(a1-a0); w=(1.8*(1-u)+0.3)*wk*S/2*RAYW
            cv2.circle(rib,(int(fx+vx*t),int(fy+vy*t)),max(1,int(round(w))),1,-1)
PMk=cv2.erode(np.isin(lab,[c[0] for c in CPET]).astype(np.uint8),ell(10*S)).astype(np.float32)   # keep veins off the petal outline
rib=np.clip(g(rib,RAYB*S)*2.2,0,1)*g(PMk,1.5*S)
HS*=(1-RIBD*rib)
VDIL=float(os.environ.get('VDIL',1.0))
vcut=np.clip(g(cv2.dilate(vein,ell(2*VDIL*S+1)).astype(np.float32),VSM*S)*1.6,0,1)
HS*=(1-VCUT*vcut)
print('stage25 slash px (1x)',int(vein.sum()/S/S))
# ---- stage24: the ref's dark clefts inside the side-flower petals -> engraved grooves (area that was dark in the ref but got filled into the petal) ----
CLD=float(os.environ.get('CLD',1.0)); CLMIN=float(os.environ.get('CLMIN',40)); CLER=float(os.environ.get('CLER',5))
CLF=np.zeros((H2,W2),np.float32)
for _k in range(3):
    _fx,_fy=X(0,_k),Y(133); _rr=np.hypot(np.arange(W2)[None,:]-_fx,np.arange(H2)[:,None]-_fy)/S
    for _q in range(15*_k+1,15*_k+8):
        _pm=(lab==_q)
        if not _pm.any(): continue
        _cl=(cv2.erode(_pm.astype(np.uint8),ell(CLER*S))>0)&(m0==0)&(_rr>26+3)&(_rr<150)
        _cl=cv2.morphologyEx(_cl.astype(np.uint8),cv2.MORPH_OPEN,ell(1.5*S))
        _l,_n=ndi.label(_cl)
        for _j in range(1,_n+1):
            if (_l==_j).sum()>=CLMIN*S*S: CLF[_l==_j]=1
print('stage24 cleft px (1x)',int(CLF.sum()/S/S))
HS*=(1-CLD*np.clip(g(CLF,1.1*S)*1.8,0,1))
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
            if HS[int(cy_),int(cx_)]<0.05:
                _vm=float(Lab[o][mm].mean())
                if not (_vm>=DLMIN or a_/S/S>=140): continue          # F6: drop dim speckles (ref has only a few bright dots, not clusters of 3-4)
                _c=np.cov(np.vstack([xx_-xx_.mean(),yy_-yy_.mean()])); _w,_v=np.linalg.eigh(_c)
                _ra=2.0*np.sqrt(max(_w[1],1e-3))*1.15; _rb=2.0*np.sqrt(max(_w[0],1e-3))*1.15   # ellipse semi-axes (teardrop-ish)
                _th=np.arctan2(_v[1,1],_v[0,1])
                DOTS.append((cx_,cy_,_ra,_rb,_th))
def edome(hs,bx,by,ra,rb,th,base,top,pw=.5):
    R_=max(ra,rb); x0,x1=max(int(bx-R_-2),0),min(int(bx+R_+3),W2); y0,y1=max(int(by-R_-2),0),min(int(by+R_+3),H2)
    yy_,xx_=np.mgrid[y0:y1,x0:x1]; u=(xx_-bx)*np.cos(th)+(yy_-by)*np.sin(th); v=-(xx_-bx)*np.sin(th)+(yy_-by)*np.cos(th)
    rr=np.sqrt((u/ra)**2+(v/rb)**2)
    dm=np.where(rr<1,base+(top-base)*np.sqrt(np.clip(1-rr**2,0,1))**(2*pw),0)
    hs[y0:y1,x0:x1]=np.maximum(hs[y0:y1,x0:x1],dm)
for bx,by,ra_,rb_,th_ in DOTS: edome(HS,bx,by,ra_,rb_,th_,.14,.54); nd+=1
print('dots',nd)
dbgd=T2.copy()
for bx,by,ra_,rb_,th_ in DOTS: cv2.ellipse(dbgd,(int(bx),int(by)),(int(ra_)+2,int(rb_)+2),float(np.degrees(th_)),0,360,(0,255,0),1)
cv2.imwrite(Z+'dots_dbg.png',dbgd[:,PW2:2*PW2])
# one exact period, symmetrized about the flower axes (j <-> 1-j on the cycle)
Hp=HS[:,PW2:2*PW2].copy()
idx=(1-np.arange(PW2))%PW2
Hp=0.5*(Hp+Hp[:,idx]); Hp=np.clip(Hp,0,1).astype(np.float32)
# F3: grainy stippled ground. periodic noise (wraps on the period) added to the floor only, after symmetrizing
STIP_A=0.040; STIP_SIG=0.9*S/2
rng=np.random.default_rng(7)
nz=rng.standard_normal(Hp.shape).astype(np.float32)
nz=ndi.gaussian_filter(nz,STIP_SIG,mode=('nearest','wrap'))
nz=(nz-nz.mean())/nz.std()
grain=np.clip((nz-0.3)/1.4,0,1)            # sparse bright grains, rest stays at floor
fl=(Hp<0.05).astype(np.uint8)
dist=cv2.distanceTransform(np.pad(fl,((0,0),(PW2,PW2)),mode='wrap'),cv2.DIST_L2,5)[:,PW2:-PW2]
w=np.clip((dist-1.5*S)/(3*S),0,1)           # fade near shape edges so outlines stay clean
Hp=np.where(Hp<0.05,np.clip(Hp+STIP_A*grain*w,0,0.049),Hp).astype(np.float32)
cv2.imwrite(Z+'band_period_v31.png',(Hp*65535).astype(np.uint16))
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
cv2.imwrite(Z+'v31_preview.png',np.vstack([ref_p,vir,rel]))
for nm,(a,b) in {'A':(0,700),'B':(850,1550)}.items():
    z=np.vstack([ref_p[:,a:b],rel[:,a:b]]); cv2.imwrite(Z+f'v31_zoom_{nm}.png',cv2.resize(z,None,fx=1.8,fy=1.8,interpolation=cv2.INTER_CUBIC))
tile=np.hstack([Hp[:,-700:],Hp[:,:700]]); cv2.imwrite(Z+'v31_seam.png',shade(tile))
# debug overlay: relief outline (HS>0.3) on the reference, centre flower crop
_o=T2[:,PW2:2*PW2].copy(); _m=(Hp>0.3).astype(np.uint8)
_cs,_=cv2.findContours(_m,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE); cv2.drawContours(_o,_cs,-1,(0,255,0),1)
cv2.imwrite(Z+'v31_overlay_centre.png',cv2.resize(_o[:,1198-330:1198+330],None,fx=1.6,fy=1.6,interpolation=cv2.INTER_CUBIC))

# crops of both flowers (reference | relief), from the 3-tile map
relT=shade(HS)
for nm,fxp in (('side',0),('centre',599)):
    cx=int(X(fxp,1)); a,b=cx-440,cx+440
    cv2.imwrite(Z+f'v31_flower_{nm}.png',np.hstack([T2[:,a:b],relT[:,a:b]]))
# debug: final petal outlines (side flower, middle tile) on the reference, zoomed
_o=T2.copy()
for _q in range(16,23):
    _cs,_=cv2.findContours((lab==_q).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); cv2.drawContours(_o,_cs,-1,(0,255,0),1)
_cx=int(X(0,1)); cv2.imwrite(Z+'v31_side_outline.png',cv2.resize(_o[:,_cx-330:_cx+330],None,fx=1.6,fy=1.6,interpolation=cv2.INTER_CUBIC))
# stage24 merge check (side flower): 7 petals per tile must stay separate components (8-conn)
for _k in range(3):
    _ps=[15*_k+j for j in range(1,8)]; _l,_n=ndi.label(np.isin(lab,_ps),structure=np.ones((3,3)))
    print('side tile',_k,'petal comps (8-conn, expect 5: 4/5 join the scroll tails, so check pieces instead):',_n,[int((lab==q).sum()/S/S) for q in _ps])
