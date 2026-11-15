import sys,json,struct; sys.path.insert(0,'/tmp/w')
from prep import *
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SRC='/tmp/r/site/nodiamond1.glb'
def rawload(p):
    d=open(p,'rb').read(); jl,_=struct.unpack('<II',d[12:20]); j=json.loads(d[20:20+jl]); off=20+jl+8; return d,j,d[off:]
def run(out,peel=20,smooth=30,maxedge=0.012,minc=6000,region=0.5):
    d0,j,bin=rawload(SRC)
    P,N,T=load(SRC)
    UV=np.frombuffer(bin,np.float32,len(P)*2,j['bufferViews'][2]['byteOffset']).reshape(-1,2)
    w=weld(P); nw=w.max()+1
    first=np.zeros(nw,int); first[w[::-1]]=np.arange(len(P))[::-1]
    Pw=P[first].astype(np.float64)
    keep=~runtime_drop(P,T)
    Tw=w[T]
    # small components
    def comps(mask):
        t=Tw[mask]; r=np.r_[t[:,0],t[:,1],t[:,2]]; c=np.r_[t[:,1],t[:,2],t[:,0]]
        g=coo_matrix((np.ones(len(r)),(r,c)),shape=(nw,nw)); nc,lab=connected_components(g,directed=False)
        cnt=np.bincount(lab[t[:,0]],minlength=nc); return lab[Tw[:,0]],cnt
    lab,cnt=comps(keep); small=cnt[lab]<minc; 
    n0=keep.sum(); keep&=~small; print('removed small comps tris',(n0-keep.sum()))
    cen=lambda m: Pw[Tw[m]].mean(1)
    inhead=lambda: (np.hypot(*(Pw[Tw].mean(1)[:,[0,2]].T))<region)&(Pw[Tw].mean(1)[:,1]>0.75)
    IH=inhead()
    for it in range(peel):
        t=Tw[keep]; e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]); es=np.sort(e,1)
        u,inv,c=np.unique(es,axis=0,return_inverse=True,return_counts=True); inv=inv.ravel()
        bnd=(c[inv]==1).reshape(3,-1).T  # per-tri per-edge boundary flags
        nb=bnd.sum(1)
        p=Pw[t]; L=np.stack([np.linalg.norm(p[:,1]-p[:,0],axis=1),np.linalg.norm(p[:,2]-p[:,1],axis=1),np.linalg.norm(p[:,0]-p[:,2],axis=1)],1)
        area=0.5*np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)+1e-12
        asp=L.max(1)**2/(2*area)
        bvset=np.zeros(nw,bool); bvset[u[c==1].ravel()]=True
        allb=bvset[t].all(1)   # strip triangle: all 3 verts on the boundary
        bad=(nb>=2)|allb|((nb==1)&((L.max(1)>maxedge)|(asp>10)))
        idx=np.where(keep)[0]; kill=idx[bad&IH[idx]]
        print('peel',it,'boundary tris',(nb>0).sum(),'killed',len(kill))
        if not len(kill): break
        keep[kill]=False
        lab,cnt=comps(keep); keep&=~(cnt[lab]<minc)
    # boundary smoothing
    t=Tw[keep]; e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]); es=np.sort(e,1)
    u,inv,c=np.unique(es,axis=0,return_inverse=True,return_counts=True)
    b=u[c==1]; print('boundary edges',len(b))
    nbr={}
    for a,bb in b: nbr.setdefault(a,[]).append(bb); nbr.setdefault(bb,[]).append(a)
    bv=np.array(list(nbr.keys())); 
    head=(np.hypot(Pw[bv,0],Pw[bv,2])<region)&(Pw[bv,1]>0.75); bv=bv[head]
    Q=Pw.copy()
    for k in range(smooth):
        for lam in (0.5,-0.53):
            Qn=Q.copy()
            for v in bv:
                ns=[n for n in nbr[v] if n in nbr]
                if len(ns)==2: Qn[v]=Q[v]+lam*(Q[ns].mean(0)-Q[v])
            Q=Qn
    moved=np.linalg.norm(Q-Pw,axis=1); print('boundary smoothing max move',moved.max())
    # build output arrays: positions of every original vertex copy -> Q[w]
    Pn=Q[w].astype(np.float32)
    Tn=T[keep]; used=np.unique(Tn); remap=-np.ones(len(P),np.int64); remap[used]=np.arange(len(used))
    Tn=remap[Tn].astype(np.uint32)
    # write GLB
    pos=Pn[used]; nor=N[used].astype(np.float32); uv=UV[used].astype(np.float32)
    imgs=[bin[j['bufferViews'][i]['byteOffset']:j['bufferViews'][i]['byteOffset']+j['bufferViews'][i]['byteLength']] for i in (4,5,6)]
    chunks=[Tn.tobytes(),pos.tobytes(),uv.tobytes(),nor.tobytes()]+imgs
    bvs=[];off=0;blob=b''
    for i,ch in enumerate(chunks):
        pad=(-len(ch))%4; bvd={'buffer':0,'byteOffset':off,'byteLength':len(ch)}
        if i==0: bvd['target']=34963
        elif i<4: bvd['target']=34962
        bvs.append(bvd); blob+=ch+b'\0'*pad; off+=len(ch)+pad
    J=json.loads(json.dumps(j)); J['bufferViews']=bvs; J['buffers']=[{'byteLength':len(blob)}]
    n=len(used)
    J['accessors'][0].update(count=n,min=pos.min(0).tolist(),max=pos.max(0).tolist())
    J['accessors'][1].update(count=n); J['accessors'][2].update(count=n); J['accessors'][3].update(count=len(Tn)*3)
    jb=json.dumps(J,separators=(',',':')).encode(); jb+=b' '*((-len(jb))%4)
    glb=struct.pack('<4sII','glTF'.encode(),2,12+8+len(jb)+8+len(blob))+struct.pack('<II',len(jb),0x4E4F534A)+jb+struct.pack('<II',len(blob),0x004E4942)+blob
    open(out,'wb').write(glb); print('wrote',out,len(glb),'tris',len(Tn),'verts',n)
if __name__=='__main__':
    run(sys.argv[1])
