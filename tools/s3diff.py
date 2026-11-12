#!/usr/bin/env python3
"""Diff two same-topology ring GLBs (base = Solitaire 2, edit = Solitaire 3) per region.
Usage: s3diff.py base.glb edit.glb [out.png]  -> table (by semantic / theta sector / top cells) + heat-map PNG."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from glb import GLB; import s2map as M
a, b = GLB(sys.argv[1]), GLB(sys.argv[2]); out = sys.argv[3] if len(sys.argv) > 3 else 's3diff.png'
assert a.pos.shape == b.pos.shape, 'topology differs (vertex count) - diff needs same vertex order'
L = M.label(a); d = b.pos - a.pos; dm = np.linalg.norm(d, axis=1); th, rel, z = M.coords(a.pos)
dx, dy = a.pos[:, 0] - M.C['cx'], a.pos[:, 1] - M.C['cy']; rr = np.hypot(dx, dy); dr = (d[:, 0] * dx + d[:, 1] * dy) / rr   # radial component
mv = dm > 1e-6; print(f'moved {mv.sum()} / {len(dm)} verts | max {dm.max():.4f} mean(moved) {dm[mv].mean() if mv.any() else 0:.4f} (1 unit = bore radius {M.C["R"]})')
if not mv.any(): print('IDENTICAL to base'); 
else:
    print('by semantic:'); [print(f'  {n:5s} moved {(mv&(L["sem"]==s)).sum():6d} max {dm[L["sem"]==s].max():.4f}') for s, n in enumerate(['gold', 'gem', 'bore'])]
    print('by theta sector (moved | max | mean dz | mean d_rho):')
    for t in range(360 // M.TB):
        m = mv & (L['theta'] == t)
        if m.any(): print(f'  {t*M.TB-180:+4d}..{t*M.TB-180+M.TB:+4d} {m.sum():6d} | {dm[m].max():.4f} | {d[m,2].mean():+.4f} | {dr[m].mean():+.4f}')
    names = np.array([M.name(L, i) for i in np.flatnonzero(mv)]); u, c = np.unique(names, return_counts=True); mx = {n: dm[np.flatnonzero(mv)][names == n].max() for n in u}
    print('top cells (sector.shell.zside: moved, max):'); [print(f'  {n:22s} {k:6d} {mx[n]:.4f}') for n, k in sorted(zip(u, c), key=lambda x: -mx[x[0]])[:10]]
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
f, ax = plt.subplots(1, 3, figsize=(18, 6), dpi=80); v = max(dm.max(), 1e-6); o = np.argsort(dm)
s0 = ax[0].scatter(a.pos[o, 0], a.pos[o, 1], s=.2, c=dm[o], cmap='inferno', vmin=0, vmax=v); ax[0].set_aspect('equal'); ax[0].set_title('front: |displacement|'); plt.colorbar(s0, ax=ax[0], shrink=.7)
ax[1].scatter(th[o], rel[o], s=.2, c=dm[o], cmap='inferno', vmin=0, vmax=v); ax[1].set_title('unrolled theta x rho/R'); ax[1].set_xticks(range(-180, 181, 30)); ax[1].grid(alpha=.3)
ax[2].scatter(th[o], z[o], s=.2, c=dm[o], cmap='inferno', vmin=0, vmax=v); ax[2].set_title('unrolled theta x z'); ax[2].set_xticks(range(-180, 181, 30)); ax[2].grid(alpha=.3)
plt.tight_layout(); plt.savefig(out); print('wrote', out)
