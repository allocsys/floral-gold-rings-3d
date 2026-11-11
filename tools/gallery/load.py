import trimesh, numpy as np, sys
sc = trimesh.load('../r/site/solitaire_meshy2.glb', process=False)
g = list(sc.geometry.values())
print(len(g), [ (x.vertices.shape, x.faces.shape) for x in g])
m = g[0]
np.save('V.npy', np.asarray(m.vertices, dtype=np.float32)); np.save('F.npy', np.asarray(m.faces, dtype=np.int32))
uv = getattr(m.visual,'uv',None)
if uv is not None: np.save('UV.npy', np.asarray(uv,dtype=np.float32))
print(m.bounds)
