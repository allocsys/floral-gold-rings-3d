import sys,json,struct; sys.path.insert(0,'/tmp/w')
from prep import *
from scipy.sparse import coo_matrix
SRC=sys.argv[1]; OUT=sys.argv[2]
d=bytearray(open(SRC,'rb').read()); jl,_=struct.unpack('<II',d[12:20]); j=json.loads(d[20:20+jl]); off=20+jl+8
P,N,T=load(SRC); T=T.astype(np.int64)
w=weld(P); nw=w.max()+1; first=np.zeros(nw,int); first[w[::-1]]=np.arange(len(P))[::-1]
Pw=P[first].astype(np.float64); Tw=w[T]
rr=np.r_[Tw[:,0],Tw[:,1],Tw[:,2],Tw[:,1],Tw[:,2],Tw[:,0]]; cc=np.r_[Tw[:,1],Tw[:,2],Tw[:,0],Tw[:,0],Tw[:,1],Tw[:,2]]
A=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(nw,nw)).tocsr(); A.data[:]=1; deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
# squash lumps inward to a cylinder under the ring tube
import os
RT=float(os.environ.get('RT',0.188)); W0=float(os.environ.get('W0',0.075)); W1=float(os.environ.get('W1',0.115)); Y0=float(os.environ.get('Y0',0.85))
wt=np.zeros(nw)
for k in K:
    dd=np.hypot(Pw[:,0]-k[0],Pw[:,2]-k[2]); wt=np.maximum(wt,np.clip((W1-dd)/(W1-W0),0,1))
wt*=np.clip((Pw[:,1]-Y0)/0.02,0,1)
r=np.hypot(Pw[:,0],Pw[:,2]); rt=np.minimum(r,RT); rnew=r-wt*(r-rt); sc=np.where(r>1e-9,rnew/np.maximum(r,1e-9),1)
Q=Pw.copy(); Q[:,0]*=sc; Q[:,2]*=sc
print('squashed verts',(wt>0).sum())
SM=int(os.environ.get('SM',20)); sw=np.minimum(1,wt*2+ (A@(wt>0).astype(float)>0)*0.5*(wt==0))
for k in range(SM):
    for lam in (0.5,-0.53):
        Qn=(A@Q)/deg[:,None]; Q=Q+lam*sw[:,None]*(Qn-Q)

print('max move',np.linalg.norm(Q-Pw,axis=1).max())
# normals: recompute for verts with wt>0 (and neighbours)
fn=np.cross(Q[Tw[:,1]]-Q[Tw[:,0]],Q[Tw[:,2]]-Q[Tw[:,0]])
acc=np.zeros((nw,3))
for k in range(3): np.add.at(acc,Tw[:,k],fn)
acc/=np.linalg.norm(acc,axis=1,keepdims=True)+1e-15
Pn=Q[w].astype(np.float32); Nn=N.astype(np.float64).copy()
upd=wt[w]>0
# blend new normal by weight, keep original orientation sense
newn=acc[w]; Nn[upd]=(1-wt[w][upd,None])*Nn[upd]+wt[w][upd,None]*newn[upd]
Nn/=np.linalg.norm(Nn,axis=1,keepdims=True)+1e-15
Nn=Nn.astype(np.float32)
pa=j['accessors'][j['meshes'][0]['primitives'][0]['attributes']['POSITION']]; na=j['accessors'][j['meshes'][0]['primitives'][0]['attributes']['NORMAL']]
for a,arr in ((pa,Pn),(na,Nn)):
    bv=j['bufferViews'][a['bufferView']]; o=off+bv.get('byteOffset',0)+a.get('byteOffset',0); d[o:o+arr.nbytes]=arr.tobytes()
# patch min/max in JSON (same size: rewrite JSON in place only if length unchanged)
pa['min']=Pn.min(0).tolist(); pa['max']=Pn.max(0).tolist()
jb=json.dumps(j,separators=(',',':')).encode(); jb+=b' '*(jl-len(jb)) if len(jb)<=jl else b''
assert len(jb)==jl, (len(jb),jl)
d[20:20+jl]=jb; open(OUT,'wb').write(d); print('wrote',OUT)
