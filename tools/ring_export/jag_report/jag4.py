import sys, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
d = np.load(sys.argv[1]); V, F = d['V'], d['F']; Ri = float(sys.argv[2]); name = sys.argv[3]; out = sys.argv[4]
r = np.hypot(V[:,0], V[:,1]); th = np.degrees(np.arctan2(V[:,1], V[:,0])) % 360
bore = np.abs(r-Ri) < 2e-3
fig, ax = plt.subplots(2, 2, figsize=(13, 9))
for j,(sgn,nm) in enumerate(((1,'z+'),(-1,'z-'))):
    zs = np.median(V[bore & (V[:,2]*sgn>1), 2])
    # plan view: faces fully near the flange plane, tile 0..60 deg, r<Ri+1.6
    near = (np.abs(V[:,2]-zs) < 0.03) & (r < Ri+1.6)
    ff = near[F].all(1)
    tri = F[ff]
    cth = th[tri].mean(1)
    # wrap-safe: keep faces with all verts th in [0,62] (tile 0)
    ok = (th[tri] <= 62).all(1)
    tri = tri[ok]
    segs = np.concatenate([np.stack([V[tri[:,a],:2], V[tri[:,(a+1)%3],:2]], 1) for a in range(3)])
    a = ax[0,j]; a.add_collection(LineCollection(segs, colors='k', linewidths=.4))
    a.set_xlim(Ri*0.99*np.cos(np.radians(62))-.2, Ri+1.7); a.set_ylim(-.2, (Ri+1.7)*np.sin(np.radians(62)))
    a.set_aspect('equal'); a.set_title(f'{name} {nm} flange face, plan view, tile 0..60 deg (z={zs:.4f})')
    # unrolled rim profile
    sel = np.where(bore & (V[:,2]*sgn > 1.0))[0]; o = sel[np.argsort(th[sel])]
    gaps = np.diff(np.concatenate([th[o], [th[o][0]+360]]))
    print(f'{name} {nm}: rim verts {len(o)}, angular gap deg min {gaps.min():.3f} med {np.median(gaps):.3f} max {gaps.max():.3f}; chord mm med {np.radians(np.median(gaps))*Ri:.3f}')
    b = ax[1,j]; b.plot(th[o], (V[o,2]-np.median(V[o,2]))*1000, '.-', ms=3, lw=.6)
    b.set_xlim(0, 125); b.set_xlabel('theta deg (2 tiles shown)'); b.set_ylabel('rim z - median, micrometres')
    for s in (0,60,120): b.axvline(s, c='r', lw=.6)
    b.set_title(f'{name} {nm} rim edge height (red = tile seams)')
plt.tight_layout(); plt.savefig(out, dpi=110)
