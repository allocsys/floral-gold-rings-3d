# Build site/band_meshy_tile.glb from the Meshy strip (reference/meshy/model.glb).
# usage: python3 tools/meshy/make_tile.py reference/meshy/model.glb site/band_meshy_tile.glb   (needs trimesh, shapely, scipy, numpy)
# 1 crop ONE repeat at px 208..936 of 1904 (matched columns), blend z + weld normals across the cut
# 2 inside (back) faces: flatten to one radius and subdivide to ~0.01 units so it bends into a smooth cylinder (viewer gives it a polished plain material)
# 3 re-embed the ORIGINAL base/normal/metal-rough JPEG bytes unchanged
import sys,json,struct,numpy as np,trimesh
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
src,dst=sys.argv[1],sys.argv[2]
g=list(trimesh.load(src).geometry.values())[0]
v0=np.asarray(g.vertices); W,H=1904,304
x=((v0[:,0]+0.9519)/1.9038*(W-1)).astype(int).clip(0,W-1); y=((v0[:,1]+0.1522)/0.3045*(H-1)).astype(int).clip(0,H-1)
hh=np.full((H,W),-9.0); np.maximum.at(hh,(y,x),v0[:,2]); hf=np.where(hh>-9,hh,np.nan)
for _ in range(8):
    mx=ndi.maximum_filter(np.nan_to_num(hf,nan=-9),size=3); hf=np.where(np.isnan(hf),np.where(mx>-9,mx,np.nan),hf)
hf=np.nan_to_num(hf,nan=np.nanmin(hf))
L=1.9038; x0=-0.9519; X1,X2=208,936; x1=x0+X1/1903*L; x2=x0+X2/1903*L
m=g.copy().slice_plane([x1,0,0],[1,0,0],cap=False).slice_plane([x2,0,0],[-1,0,0],cap=False)
raw=hf[:,X2]-hf[:,X1]; ok=(hf[:,X1]>0)&(hf[:,X2]>0)&(np.abs(raw)<0.03)   # rail-edge rows can hold back-plane heights at the cut columns: ignore them, interpolate D across
D=np.interp(np.arange(H),np.where(ok)[0],raw[ok]); D=ndi.uniform_filter1d(ndi.median_filter(D,size=15),9).clip(-0.03,0.03)
v=np.array(m.vertices); uv=np.array(m.visual.uv); f=np.array(m.faces); d=0.03
row=((v[:,1]+0.1522)/0.3045*(H-1)).clip(0,H-1).round().astype(int)
sm=lambda t:(lambda u:u*u*(3-2*u))(np.clip(t,0,1))
v[:,2]+= -0.5*D[row]*sm(1-(x2-v[:,0])/d) + 0.5*D[row]*sm(1-(v[:,0]-x1)/d)
# ---- inside: everything within BAND of the back plane is flattened to one radius, those faces are dropped, and ONE regular grid patch (no holes, no baked relief) takes their place
fn=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]); fn/=np.linalg.norm(fn,axis=1,keepdims=True)+1e-12
flat=np.unique(f[fn[:,2]<-0.9]); backZ=np.median(v[flat,2]); BAND=0.010
inb=v[:,2]<backZ+BAND; v[inb,2]=backZ
dropf=inb[f].all(axis=1); yb=np.abs(v[inb,1]).max(); print('dropped faces',dropf.sum(),'of',len(f),'backZ',round(backZ,4),'yb',round(yb,4))
nx=int(np.ceil((x2-x1)/0.008)); ny=int(np.ceil(2*yb/0.008))
gx=np.linspace(x1,x2,nx+1); gy=np.linspace(-yb,yb,ny+1); GX,GY=np.meshgrid(gx,gy,indexing='ij')
pv=np.stack([GX.ravel(),GY.ravel(),np.full(GX.size,backZ)],1)
ii=np.arange((nx+1)*(ny+1)).reshape(nx+1,ny+1); q=np.stack([ii[:-1,:-1],ii[1:,:-1],ii[1:,1:],ii[:-1,1:]],-1).reshape(-1,4)
pf=np.vstack([q[:,[0,2,1]],q[:,[0,3,2]]]) # winding: normal -z
tri=np.cross(pv[pf[:,1]]-pv[pf[:,0]],pv[pf[:,2]]-pv[pf[:,0]])
if tri[:,2].mean()>0: pf=pf[:,[0,2,1]]
nv0=len(v); V=np.vstack([v,pv]); UV=np.vstack([uv,np.zeros((len(pv),2))]); F=np.vstack([f[~dropf],pf+nv0])
isback=np.zeros(len(V),bool); isback[nv0:]=True
# ---- smooth normals per unique position
fn2=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]])
key=np.round(V/1e-6).astype(np.int64); _,inv=np.unique(key,axis=0,return_inverse=True); inv=inv.ravel()
acc=np.zeros((inv.max()+1,3))
for k in range(3): np.add.at(acc,inv[F[:,k]],fn2)
n=acc[inv]; n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
n[isback]=[0,0,-1]
A=np.where(np.abs(V[:,0]-x1)<1e-5)[0]; B=np.where(np.abs(V[:,0]-x2)<1e-5)[0]
for S,T in ((A,B),(B,A)):
    _,j=cKDTree(V[T][:,1:]).query(V[S][:,1:]); a=n[S]+n[T][j]; a/=np.linalg.norm(a,axis=1,keepdims=True)+1e-12
    keep=~isback[S]; n[S[keep]]=a[keep]
out=trimesh.Trimesh(V,F,process=False); out.visual=trimesh.visual.TextureVisuals(uv=UV,material=g.visual.material); out._cache['vertex_normals']=n
out.export('/tmp/_t.glb')
# ---- re-embed original JPEG bytes
def parse(p):
    b=open(p,'rb').read(); nn=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+nn]); o=20+nn; mm=struct.unpack('<I',b[o:o+4])[0]; return j,b[o+8:o+8+mm]
oj,ob=parse(src); tj,tb=parse('/tmp/_t.glb')
def tex(j,key):
    mt=j['materials'][0]; t=mt['pbrMetallicRoughness'].get('baseColorTexture') if key=='base' else mt['pbrMetallicRoughness'].get('metallicRoughnessTexture') if key=='mr' else mt.get('normalTexture')
    return None if t is None else j['textures'][t['index']]['source']
rep={}
for key in ('base','normal','mr'):
    oi=tex(oj,key); ti=tex(tj,key); ov=oj['bufferViews'][oj['images'][oi]['bufferView']]
    data=ob[ov['byteOffset']:ov['byteOffset']+ov['byteLength']]
    if ti is None: # add the image/texture (trimesh drops the MR map on this material)
        tj['images'].append({'bufferView':len(tj['bufferViews']),'mimeType':'image/jpeg'}); tj['bufferViews'].append({'buffer':0,'byteOffset':0,'byteLength':len(data)})
        tj['textures'].append({'source':len(tj['images'])-1}); tj['materials'][0]['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':len(tj['textures'])-1}
        tj['materials'][0]['pbrMetallicRoughness']['metallicFactor']=1.0; tj['materials'][0]['pbrMetallicRoughness']['roughnessFactor']=1.0
        rep[len(tj['bufferViews'])-1]=data
    else:
        rep[tj['images'][ti]['bufferView']]=data; tj['images'][ti]['mimeType']='image/jpeg'
nb=bytearray()
for i,bv in enumerate(tj['bufferViews']):
    dd=rep.get(i,tb[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])
    while len(nb)%4: nb.append(0)
    bv['byteOffset']=len(nb); bv['byteLength']=len(dd); nb+=dd
while len(nb)%4: nb.append(0)
tj['buffers'][0]['byteLength']=len(nb)
js=json.dumps(tj,separators=(',',':')).encode(); js+=b' '*((4-len(js)%4)%4)
open(dst,'wb').write(struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(nb))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(nb),0x004E4942)+bytes(nb))
print('wrote',dst,round((len(js)+len(nb))/1e6,1),'MB; verts',len(V),'faces',len(F))
