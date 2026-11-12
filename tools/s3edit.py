#!/usr/bin/env python3
"""Apply gradual vertex edits to the Solitaire 2 mesh -> Solitaire 3 GLB (topology/UVs/textures unchanged).
Usage: s3edit.py edits.json [base.glb] [out.glb]     edits.json = list of ops, applied in order:
 {"name":"..", "sel":{"sem":[0],"th":[lo,hi],"rel":[lo,hi],"z":[lo,hi]}, "feather":{"th":8,"rel":.03,"z":.02},
  "op":"scale_z"|"radial"|"move", "amount":a | "d":[dx,dy,dz], "mirror":true}
 th = deg from the stone (+x positive), rel = rho/R (bore radius = 1), sem 0 gold / 1 gem / 2 bore. mirror=true also applies th -> -th.
 scale_z: z *= 1+a*w   radial: rho += a*R*w (away from axis)   move: p += d*w. w = smooth 0..1 weight from sel + feather."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from glb import GLB; import s2map as M
def ss(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
def weight(L, pos, sel, fe):
    t, r, z = M.coords(pos); w = np.isin(L['sem'], sel.get('sem', [0])).astype(np.float64)
    for key, v in (('th', t), ('rel', r), ('z', z)):
        if key in sel:
            lo, hi = sel[key]; f = max(fe.get(key, 1e-9), 1e-9); w *= ss((v - lo) / f + .5) * ss((hi - v) / f + .5)
    return w
def prong_scale(L, p, o):
    """Thicken the 4 prongs: scale (x,z) about each prong axis by 1+amount*w. Params: cx,cz (axis offsets), rad (xz reach), y:[lo,hi], feather_y."""
    cx, cz, rad = o.get('cx', .15), o.get('cz', .13), o.get('rad', .09); lo, hi = o['y']; fy = max(o.get('feather_y', .03), 1e-9)
    wy = ss((p[:, 1] - lo) / fy + .5) * ss((hi - p[:, 1]) / fy + .5) * (L['sem'] == 0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            ax, az = sx * cx, sz * cz; d = np.hypot(p[:, 0] - ax, p[:, 2] - az); w = wy * ss((rad - d) / (rad * .4) + .5)
            p[:, 0] = ax + (p[:, 0] - ax) * (1 + o['amount'] * w); p[:, 2] = az + (p[:, 2] - az) * (1 + o['amount'] * w)
    return p
def apply(g, L, ops):
    p = g.pos.astype(np.float64).copy()
    for o in ops:
        if o['op'] == 'prong_scale': p = prong_scale(L, p, o); continue
        sels = [o['sel']]
        if o.get('mirror') and 'th' in o['sel']: lo, hi = o['sel']['th']; sels.append({**o['sel'], 'th': [-hi, -lo]})
        for s in sels:
            w = weight(L, p, s, o.get('feather', {})); a = o.get('amount', 0)
            if o['op'] == 'scale_z': p[:, 2] *= 1 + a * w
            elif o['op'] == 'radial':
                dx, dy = p[:, 0] - M.C['cx'], p[:, 1] - M.C['cy']; rr = np.hypot(dx, dy); k = a * M.C['R'] * w / rr; p[:, 0] += dx * k; p[:, 1] += dy * k
            elif o['op'] == 'move': p += np.outer(w, o['d'])
            elif o['op'] == 'prong_scale': pass
            else: raise SystemExit('unknown op ' + o['op'])
    return p.astype(np.float32)
if __name__ == '__main__':
    ops = json.load(open(sys.argv[1])); base = sys.argv[2] if len(sys.argv) > 2 else os.path.join(M.SITE, 'solitaire_6.glb'); out = sys.argv[3] if len(sys.argv) > 3 else 'solitaire3.glb'
    g = GLB(base); L = M.label(g); p = apply(g, L, ops); g.save(out, pos=p)
    print('wrote', out, '| ops', len(ops), '| verts moved', int((np.abs(p - g.pos).max(1) > 1e-7).sum()))
