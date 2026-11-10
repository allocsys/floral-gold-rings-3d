# Make a mirror-symmetric copy of a Meshy ring GLB: keep one half (x<=0 by default), mirror it across x=0 onto the other side.
# usage: python3 tools/meshy/make_sym.py IN.glb OUT.glb [neg|pos]   (neg = keep x<=0 and mirror it to x>=0; pos = the other way round)
# 1 keep triangles whose centroid is on the kept side; 2 clamp the kept vertices onto the plane (x -> 0 for those past it) and snap the cut-boundary vertices to x=0 (normal x -> 0)
# 3 mirror copy (x and normal x negated, same UVs so the textures mirror too, triangle winding reversed); both halves share the x=0 seam vertices
# 4 re-embed the ORIGINAL base/normal/metal-rough JPEG bytes unchanged (no re-encode). Pure numpy.
import sys, json, struct, numpy as np
src, dst = sys.argv[1], sys.argv[2]; keep = sys.argv[3] if len(sys.argv) > 3 else 'neg'
b = open(src, 'rb').read()
jl, _ = struct.unpack('<II', b[12:20]); j = json.loads(b[20:20 + jl]); bo = 20 + jl + 8; BIN = b[bo:]
def acc(i):
    a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]; o = v['byteOffset'] + a.get('byteOffset', 0)
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a['type']]; dt = np.float32 if a['componentType'] == 5126 else np.uint32
    return np.frombuffer(BIN, dt, a['count'] * n, o).reshape(-1, n)
p = j['meshes'][0]['primitives'][0]; at = p['attributes']
P, UV, N, F = acc(at['POSITION']).astype(np.float64), acc(at['TEXCOORD_0']).copy(), acc(at['NORMAL']).astype(np.float64), acc(p['indices']).reshape(-1, 3)
s = -1.0 if keep == 'neg' else 1.0                      # kept side: s*x >= 0 after the flip below
X = P[:, 0] * -s                                         # X <= 0 is the kept side in this working frame
cen = X[F].mean(axis=1); kf = F[cen <= 0]
# welded ids (positions rounded) to find the boundary of the kept set
_, wid = np.unique(np.round(P, 5), axis=0, return_inverse=True); wid = wid.ravel()
W = wid[kf]; e = np.sort(np.r_[W[:, [0, 1]], W[:, [1, 2]], W[:, [2, 0]]], axis=1); u, c = np.unique(e, axis=0, return_counts=True)
bw = np.unique(u[c == 1].ravel()); print('kept faces', len(kf), 'of', len(F), 'boundary welded verts', len(bw))
used = np.unique(kf.ravel()); remap = -np.ones(len(P), int); remap[used] = np.arange(len(used)); kf = remap[kf]
P2, UV2, N2, X2 = P[used].copy(), UV[used], N[used].copy(), X[used]
bd = np.isin(wid[used], bw); moved = np.abs(X2[bd]).max() if bd.any() else 0
P2[:, 0] = np.where(bd | (X2 > 0), 0.0, P2[:, 0]); N2[bd, 0] = 0; N2[bd] /= np.linalg.norm(N2[bd], axis=1, keepdims=True)
print('max snap distance of the seam (model units)', round(float(moved), 5), 'verts clamped past the plane', int((X2 > 0).sum() - 0))
# drop triangles that collapsed onto the plane (all 3 verts at x=0: they would double up with their mirror) or became degenerate (zero area / repeated welded position)
wk = wid[used]; Pw = P2
flat = (P2[kf][:, :, 0] == 0).all(axis=1); a2 = np.linalg.norm(np.cross(P2[kf[:, 1]] - P2[kf[:, 0]], P2[kf[:, 2]] - P2[kf[:, 0]]), axis=1) * 0.5
rep = (wk[kf[:, 0]] == wk[kf[:, 1]]) | (wk[kf[:, 1]] == wk[kf[:, 2]]) | (wk[kf[:, 0]] == wk[kf[:, 2]])
rep2 = (np.round(P2[kf[:, 0]], 5) == np.round(P2[kf[:, 1]], 5)).all(1) | (np.round(P2[kf[:, 1]], 5) == np.round(P2[kf[:, 2]], 5)).all(1) | (np.round(P2[kf[:, 0]], 5) == np.round(P2[kf[:, 2]], 5)).all(1)
drop = flat | (a2 < 1e-9) | rep | rep2; print('dropped on-plane/degenerate faces', int(drop.sum()), '(flat', int(flat.sum()), ')'); kf = kf[~drop]
# mirrored copy
Pm, Nm = P2.copy(), N2.copy(); Pm[:, 0] *= -1; Nm[:, 0] *= -1
nv = len(P2); PO = np.vstack([P2, Pm]).astype(np.float32); NO = np.vstack([N2, Nm]).astype(np.float32); UO = np.vstack([UV2, UV2]).astype(np.float32)
FO = np.vstack([kf, kf[:, [0, 2, 1]] + nv]).astype(np.uint32)
# write GLB: geometry first (aligned 4), then the 3 original image byte ranges
parts = []; views = []; off = 0
def add(buf, target=None):
    global off
    pad = (-off) % 4; parts.append(b'\0' * pad); off += pad
    v = {'buffer': 0, 'byteOffset': off, 'byteLength': len(buf)}
    if target: v['target'] = target
    views.append(v); parts.append(buf); off += len(buf)
    return len(views) - 1
vi = add(PO.tobytes(), 34962); vu = add(UO.tobytes(), 34962); vn = add(NO.tobytes(), 34962); vx = add(FO.tobytes(), 34963)
old_img = [j['bufferViews'][im['bufferView']] for im in j['images']]
for k, im in enumerate(j['images']): im['bufferView'] = add(BIN[old_img[k]['byteOffset']:old_img[k]['byteOffset'] + old_img[k]['byteLength']])
j['bufferViews'] = views
j['accessors'] = [
    {'bufferView': vi, 'byteOffset': 0, 'componentType': 5126, 'normalized': False, 'count': len(PO), 'type': 'VEC3', 'max': PO.max(0).tolist(), 'min': PO.min(0).tolist()},
    {'bufferView': vu, 'byteOffset': 0, 'componentType': 5126, 'normalized': False, 'count': len(UO), 'type': 'VEC2', 'max': UO.max(0).tolist(), 'min': UO.min(0).tolist()},
    {'bufferView': vn, 'byteOffset': 0, 'componentType': 5126, 'normalized': False, 'count': len(NO), 'type': 'VEC3', 'max': NO.max(0).tolist(), 'min': NO.min(0).tolist()},
    {'bufferView': vx, 'byteOffset': 0, 'componentType': 5125, 'normalized': False, 'count': int(FO.size), 'type': 'SCALAR'}]
p['attributes'] = {'POSITION': 0, 'NORMAL': 2, 'TEXCOORD_0': 1}; p['indices'] = 3
binb = b''.join(parts); binb += b'\0' * ((-len(binb)) % 4); j['buffers'] = [{'byteLength': len(binb)}]
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binb)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(binb), 0x004E4942) + binb
open(dst, 'wb').write(out); print('wrote', dst, len(out), 'verts', len(PO), 'faces', len(FO))
