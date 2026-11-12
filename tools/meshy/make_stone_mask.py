# usage: python3 -I make_stone_mask.py in.glb tex0.jpg out.bin
# Marks the gem triangles of a Meshy solitaire GLB: the stone is the blue-white patch in the base colour texture (gold is orange, blue-red < 0).
# A triangle is stone if its centroid UV or at least 2 of its 3 vertex UVs sample a pixel with blue-red > -5. Output = bitmask, bit i of byte i>>3 (LSB first) = triangle i (index-buffer order) is stone.
import sys,json,struct,numpy as np
from PIL import Image
def load(p):
    b=open(p,'rb').read(); jl,_=struct.unpack('<II',b[12:20]); return json.loads(b[20:20+jl]), b[20+jl+8:]
def acc(j,bn,i):
    a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]; n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]; dt={5126:'f4',5125:'u4',5123:'u2'}[a['componentType']]
    o=bv.get('byteOffset',0)+a.get('byteOffset',0); st=bv.get('byteStride'); sz=n*np.dtype(dt).itemsize
    if st and st!=sz: return np.frombuffer(bn,'u1',a['count']*st,o).reshape(-1,st)[:,:sz].copy().view(dt).reshape(-1,n)
    return np.frombuffer(bn,dt,a['count']*n,o).reshape(-1,n)
j,bn=load(sys.argv[1]); pr=j['meshes'][0]['primitives'][0]
P=acc(j,bn,pr['attributes']['POSITION']).astype('f8'); UV=acc(j,bn,pr['attributes']['TEXCOORD_0']).astype('f8'); I=acc(j,bn,pr['indices']).astype('i8').reshape(-1,3)
im=np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype('f4'); H,W,_=im.shape
def d(uv):
    x=np.clip((uv[:,0]%1)*(W-1),0,W-1).astype(int); y=np.clip((uv[:,1]%1)*(H-1),0,H-1).astype(int); c=im[y,x]; return c[:,2]-c[:,0]
vs=d(UV)>-5; cen=d(UV[I].mean(1))>-5
st=cen|(vs[I].sum(1)>=2)
Pt=P[I[st]].mean(1)
print('stone tris',st.sum(),'of',len(st),'centroid bbox',Pt.min(0).round(3),Pt.max(0).round(3))
open(sys.argv[3],'wb').write(np.packbits(st,bitorder='little').tobytes())
