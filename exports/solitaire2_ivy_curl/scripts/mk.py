import json,base64,numpy as np,struct,os
r=json.load(open('/tmp/export.json')); os.makedirs('/mnt/user-data/outputs/solitaire2_ivy_curl',exist_ok=True); D='/mnt/user-data/outputs/solitaire2_ivy_curl/'
def get(k):
    p=np.frombuffer(base64.b64decode(r[k]['p']),np.float32).reshape(-1,3).astype(np.float64); i=np.frombuffer(base64.b64decode(r[k]['i']),np.uint32).reshape(-1,3); return p,i
def stl(path,p,i):
    t=p[i]; n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]); l=np.linalg.norm(n,axis=1,keepdims=True); n=np.divide(n,l,out=np.zeros_like(n),where=l>0)
    a=np.zeros(len(i),dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]); a['n']=n; a['v']=t; open(path,'wb').write(b'solitaire2 ivy curl mm'.ljust(80,b' ')+struct.pack('<I',len(i))+a.tobytes())
def obj(path,parts):
    with open(path,'w') as f:
        f.write('# Solitaire 2 ivy curl, units mm, Y up, ring axis Z\n'); off=0
        for name,p,i in parts:
            f.write('o %s\n'%name); f.write(''.join('v %.5f %.5f %.5f\n'%tuple(v) for v in p)); f.write(''.join('f %d %d %d\n'%(a+1+off,b+1+off,c+1+off) for a,b,c in i)); off+=len(p)
def check(name,p,i):
    q=np.round(p,4); _,inv=np.unique(q,axis=0,return_inverse=True); inv=inv.ravel(); f=inv[i]
    f=f[(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2])]
    e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]); es=np.sort(e,axis=1); u,c=np.unique(es,axis=0,return_counts=True)
    t=p[i]; vol=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
    print(name,'tris',len(i),'bbox mm',np.round(p.max(0)-p.min(0),3),'min',np.round(p.min(0),3),'| boundary edges',int((c==1).sum()),'non-manifold',int((c>2).sum()),'| signed volume mm3',round(vol,2))
gp,gi=get('gold'); sp,si=get('stone')
check('ring',gp,gi); check('stone',sp,si)
stl(D+'solitaire2_ivy_curl_ring.stl',gp,gi); stl(D+'solitaire2_ivy_curl_stone.stl',sp,si)
obj(D+'solitaire2_ivy_curl_ring.obj',[('ring',gp,gi)]); obj(D+'solitaire2_ivy_curl_stone.obj',[('stone',sp,si)])
for f in sorted(os.listdir(D)): print(f,round(os.path.getsize(D+f)/1e6,1),'MB')
