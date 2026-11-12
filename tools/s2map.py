#!/usr/bin/env python3
"""Map a ring GLB (Solitaire 2) into addressable regions. Ring axis z, stone +y.
Per vertex: sem (0 metal, 1 gem, 2 bore), theta bin (15 deg, 0 = stone, +x positive), shell (rho/R bins), zside (back/mid/front).
Usage: s2map.py [glb] [out_prefix]   -> out.npz (labels) + out.png (map) + table on stdout."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from glb import GLB
SITE = os.path.join(os.path.dirname(__file__), '..', 'site')
C = dict(cx=-0.0004, cy=-0.0739, R=0.7366)           # bore centre + radius (index.html SOLS.solitaire2)
SHELL = [0, 1.05, 1.15, 1.25, 9]; SHELLN = ['in', 'mid', 'out', 'top']; ZB = [-9, -0.06, 0.06, 9]; ZN = ['back', 'mid', 'front']; TB = 15
def coords(p):
    dx, dy = p[:, 0] - C['cx'], p[:, 1] - C['cy']
    return np.degrees(np.arctan2(dx, dy)), np.hypot(dx, dy) / C['R'], p[:, 2]
def label(g, mask_path=os.path.join(SITE, 'solitaire_6_stone.bin')):
    p, n, idx = g.pos, g.nor, g.idx; th, rel, z = coords(p)
    mk = np.unpackbits(np.frombuffer(open(mask_path, 'rb').read(), np.uint8), bitorder='little')[:len(idx)].astype(bool)
    dx, dy = p[:, 0] - C['cx'], p[:, 1] - C['cy']; rr = np.hypot(dx, dy)
    inb = (abs(rel - 1) < 0.04) & ((n[:, 0] * dx + n[:, 1] * dy) / rr < -0.9)       # same test as index.html loadSol
    bt = inb[idx].all(1) & ~mk; sem = np.zeros(len(p), np.uint8)
    sem[idx[bt].ravel()] = 2; sem[idx[mk].ravel()] = 1                               # gem wins on shared verts
    tb = np.clip(np.floor((th + 180) / TB), 0, 360 // TB - 1).astype(np.uint8)
    sh = (np.digitize(rel, SHELL) - 1).clip(0, 3).astype(np.uint8); zs = (np.digitize(z, ZB) - 1).clip(0, 2).astype(np.uint8)
    return dict(sem=sem, theta=tb, shell=sh, zside=zs)
def name(L, i): return f"t{int(L['theta'][i]) * TB - 180 + TB // 2:+04d}.{SHELLN[L['shell'][i]]}.{ZN[L['zside'][i]]}"
def select(L, sem=None, th=None, rel=None, z=None, pos=None):
    """boolean vertex selection: sem in {0,1,2}, th=(lo,hi) deg, rel=(lo,hi) rho/R, z=(lo,hi)."""
    p = pos; t, r, zz = coords(p); m = np.ones(len(p), bool)
    if sem is not None: m &= np.isin(L['sem'], sem)
    if th is not None: m &= (t >= th[0]) & (t <= th[1])
    if rel is not None: m &= (r >= rel[0]) & (r <= rel[1])
    if z is not None: m &= (zz >= z[0]) & (zz <= z[1])
    return m
if __name__ == '__main__':
    glb = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, 'solitaire_6.glb'); out = sys.argv[2] if len(sys.argv) > 2 else 's2map'
    g = GLB(glb); L = label(g); np.savez_compressed(out + '.npz', **L); th, rel, z = coords(g.pos)
    print('verts', len(g.pos), 'tris', len(g.idx), 'gem', (L['sem'] == 1).sum(), 'bore', (L['sem'] == 2).sum(), 'metal', (L['sem'] == 0).sum())
    print('theta sector (deg from stone) | metal verts | rho/R min..max | z span | y max'); 
    for b in range(360 // TB):
        m = (L['theta'] == b) & (L['sem'] == 0)
        if m.any(): print(f"{b*TB-180:+4d}..{b*TB-180+TB:+4d} | {m.sum():6d} | {rel[m].min():.2f}..{rel[m].max():.2f} | {z[m].min():+.3f}..{z[m].max():+.3f} | {g.pos[m,1].max():+.3f}")
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    col = np.array([[.8, .65, .2], [.3, .6, 1], [.6, .6, .6]]); f, ax = plt.subplots(1, 3, figsize=(18, 6), dpi=80)
    ax[0].scatter(g.pos[:, 0], g.pos[:, 1], s=.1, c=col[L['sem']]); ax[0].set_aspect('equal'); ax[0].set_title('semantic: gold / gem / bore')
    ax[1].scatter(th, rel, s=.1, c=L['shell'], cmap='tab10', vmin=0, vmax=9); ax[1].set_title('unrolled theta (deg) x rho/R, colour = shell'); ax[1].set_xticks(range(-180, 181, 30)); ax[1].grid(alpha=.3)
    ax[2].scatter(th, z, s=.1, c=L['zside'], cmap='tab10', vmin=0, vmax=9); ax[2].set_title('unrolled theta x z, colour = z side'); ax[2].set_xticks(range(-180, 181, 30)); ax[2].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(out + '.png'); print('wrote', out + '.npz', out + '.png')
