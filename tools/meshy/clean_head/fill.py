import sys,json,struct; sys.path.insert(0,'/tmp/w')
from prep import *
SRC=sys.argv[1]; OUT=sys.argv[2]; RINGS=int(sys.argv[3]) if len(sys.argv)>3 else 24; FAIR=int(sys.argv[4]) if len(sys.argv)>4 else 300
d=open(SRC,'rb').read(); jl,_=struct.unpack('<II',d[12:20]); j=json.loads(d[20:20+jl]); off=20+jl+8; bin=d[off:]
P,N,T=load(SRC); T=T.astype(np.int64)
UV=np.frombuffer(bin,np.float32,len(P)*2,j['bufferViews'][2]['byteOffset']).reshape(-1,2)
w=weld(P); nw=w.max()+1; first=np.zeros(nw,int); first[w[::-1]]=np.arange(len(P))[::-1]
Pw=P[first].astype(np.float64); Tw=w[T]
# directed boundary edges
e=np.concatenate([Tw[:,[0,1]],Tw[:,[1,2]],Tw[:,[2,0]]]); es=np.sort(e,1)
u,inv,c=np.unique(es,axis=0,return_inverse=True,return_counts=True); inv=inv.ravel()
bmask=c[inv]==1; dirs={}
for a,b in e[bmask]: dirs[a]=b
seen=set(); loops=[]
for s in list(dirs):
    if s in seen: continue
    cyc=[s]; seen.add(s); v=dirs[s]
    while v!=s and v not in seen: cyc.append(v); seen.add(v); v=dirs[v]
    loops.append(cyc)
print('loops',[len(l) for l in loops])
newP=[];newN=[];newUV=[];newT=[]; base=len(P)
for cyc in loops:
    n=len(cyc); q0=Pw[cyc]; cen=q0.mean(0); ucen=UV[first[cyc]].mean(0)
    rings=[]  # vertex index arrays (global original-vertex index space)
    rings.append(first[cyc].copy())
    for r in range(1,RINGS):
        t=r/RINGS; pos=q0*(1-t)+cen*t
        idx=np.arange(base,base+n); base+=n
        newP.append(pos); newUV.append(UV[first[cyc]]*(1-t)+ucen*t); rings.append(idx)
    cidx=base; base+=1; newP.append(cen[None]); newUV.append(ucen[None])
    # tris (existing has q_j->q_j+1, patch reversed)
    for r in range(RINGS-1):
        A=rings[r]; B=rings[r+1]; A1=np.roll(A,-1); B1=np.roll(B,-1)
        newT.append(np.stack([A1,A,B],1)); newT.append(np.stack([A1,B,B1],1))
    A=rings[RINGS-1]; A1=np.roll(A,-1); newT.append(np.stack([A1,A,np.full(n,cidx)],1))
    cyc_info=(rings,cidx)
    loops_info=globals().setdefault('LI',[]); loops_info.append((rings,cidx,n))
NP=np.concatenate(newP); NT=np.concatenate(newT); NUV=np.concatenate(newUV)
# working positions for all verts (original index space)
Pall=np.concatenate([P.astype(np.float64),NP])
# fairing: Laplacian on new verts only, over patch adjacency
nv=len(Pall); nb=[set() for _ in range(nv)]
for t in NT:
    for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): nb[a].add(b); nb[b].add(a)
free=np.arange(len(P),nv)
from scipy.sparse import coo_matrix
rr=[];cc=[]
for v in range(nv):
    for n_ in nb[v]: rr.append(v); cc.append(n_)
A=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(nv,nv)).tocsr(); deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
fm=np.zeros(nv,bool); fm[free]=True
for it in range(FAIR):
    Pn=(A@Pall)/deg[:,None]
    Pall[fm]=Pall[fm]+0.8*(Pn[fm]-Pall[fm])
# normals for new verts
fn=np.cross(Pall[NT[:,1]]-Pall[NT[:,0]],Pall[NT[:,2]]-Pall[NT[:,0]])
Nacc=np.zeros((nv,3))
for k in range(3): np.add.at(Nacc,NT[:,k],fn)
Nacc/=np.linalg.norm(Nacc,axis=1,keepdims=True)+1e-15
Nall=np.concatenate([N.astype(np.float64),Nacc[len(P):]])
# orientation sanity: patch normal vs boundary normal
for rings,cidx,n in LI:
    r1=rings[1]; print('patch normal dot boundary normal (mean):',float((Nall[r1]*N[rings[0]]).sum(1).mean()))
Tall=np.concatenate([T,NT]).astype(np.int64)
used=np.unique(Tall); remap=-np.ones(nv,np.int64); remap[used]=np.arange(len(used)); Tn=remap[Tall].astype(np.uint32)
pos=Pall[used].astype(np.float32); nor=Nall[used].astype(np.float32); UVall=np.concatenate([UV,NUV]); uv=UVall[used].astype(np.float32)
imgs=[bin[j['bufferViews'][i]['byteOffset']:j['bufferViews'][i]['byteOffset']+j['bufferViews'][i]['byteLength']] for i in (4,5,6)]
chunks=[Tn.tobytes(),pos.tobytes(),uv.tobytes(),nor.tobytes()]+imgs
bvs=[];o=0;blob=b''
for i,ch in enumerate(chunks):
    pad=(-len(ch))%4; bvd={'buffer':0,'byteOffset':o,'byteLength':len(ch)}
    if i==0: bvd['target']=34963
    elif i<4: bvd['target']=34962
    bvs.append(bvd); blob+=ch+b'\0'*pad; o+=len(ch)+pad
J=json.loads(json.dumps(j)); J['bufferViews']=bvs; J['buffers']=[{'byteLength':len(blob)}]
n=len(used); J['accessors'][0].update(count=n,min=pos.min(0).tolist(),max=pos.max(0).tolist())
J['accessors'][1].update(count=n); J['accessors'][2].update(count=n); J['accessors'][3].update(count=len(Tn)*3)
jb=json.dumps(J,separators=(',',':')).encode(); jb+=b' '*((-len(jb))%4)
glb=struct.pack('<4sII',b'glTF',2,12+8+len(jb)+8+len(blob))+struct.pack('<II',len(jb),0x4E4F534A)+jb+struct.pack('<II',len(blob),0x004E4942)+blob
open(OUT,'wb').write(glb); print('wrote',OUT,len(glb),'tris',len(Tn)//3,'verts',n)
