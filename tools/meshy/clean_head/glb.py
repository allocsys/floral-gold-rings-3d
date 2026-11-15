import json,struct,numpy as np
def load(p):
    d=open(p,'rb').read(); jl,_=struct.unpack('<II',d[12:20]); j=json.loads(d[20:20+jl]); off=20+jl+8; bin=d[off:]
    pr=j['meshes'][0]['primitives'][0]
    def acc(i):
        a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]
        dt={5126:np.float32,5125:np.uint32,5123:np.uint16}[a['componentType']]; n={'SCALAR':1,'VEC3':3,'VEC2':2}[a['type']]
        o=bv.get('byteOffset',0)+a.get('byteOffset',0)
        return np.frombuffer(bin,dt,a['count']*n,o).reshape(-1,n)
    return acc(pr['attributes']['POSITION']),acc(pr['attributes']['NORMAL']),acc(pr['indices']).reshape(-1,3)
