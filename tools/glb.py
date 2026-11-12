"""Minimal GLB reader/writer (numpy only). Single mesh/primitive; vertex-edit in place (topology unchanged)."""
import struct, json, numpy as np

class GLB:
    def __init__(s, path):
        b = open(path, 'rb').read(); s.raw = bytearray(b)
        cl, _ = struct.unpack('<II', b[12:20]); s.j = json.loads(b[20:20 + cl]); s.bo = 20 + cl + 8  # BIN data offset
        p = s.j['meshes'][0]['primitives'][0]; s.prim = p; a = s.j['accessors']
        s.pos = s._acc(p['attributes']['POSITION'], np.float32, 3).copy()
        s.nor = s._acc(p['attributes']['NORMAL'], np.float32, 3).copy()
        ia = a[p['indices']]; dt = {5123: np.uint16, 5125: np.uint32}[ia['componentType']]
        s.idx = s._acc(p['indices'], dt, 1).astype(np.int64).reshape(-1, 3)
    def _acc(s, i, dt, nc):
        a = s.j['accessors'][i]; bv = s.j['bufferViews'][a['bufferView']]; o = s.bo + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(s.raw, dt, a['count'] * nc, o).reshape(-1, nc) if nc > 1 else np.frombuffer(s.raw, dt, a['count'], o)
    def save(s, path, pos=None, nor=None):
        """write new POSITION (and NORMAL) bytes in place, update min/max."""
        raw = bytearray(s.raw); j = json.loads(json.dumps(s.j))
        for name, arr in (('POSITION', pos), ('NORMAL', nor)):
            if arr is None: continue
            ai = s.prim['attributes'][name]; a = j['accessors'][ai]; bv = j['bufferViews'][a['bufferView']]
            o = s.bo + bv.get('byteOffset', 0) + a.get('byteOffset', 0); raw[o:o + arr.size * 4] = np.ascontiguousarray(arr, np.float32).tobytes()
            if name == 'POSITION': a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        # json chunk length is unchanged only if padded identically -> rebuild json chunk with space padding to the same length
        cl, _ = struct.unpack('<II', bytes(raw[12:20])); js = json.dumps(j, separators=(',', ':')).encode()
        old = bytes(raw[20:20 + cl]); assert len(js) <= len(old), 'json grew'; raw[20:20 + cl] = js + b' ' * (len(old) - len(js))
        open(path, 'wb').write(raw)
