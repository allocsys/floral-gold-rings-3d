import sys, numpy as np
d = np.load(sys.argv[1]); V, F = d['V'], d['F']; Ri = float(sys.argv[2]); name = sys.argv[3]
r = np.hypot(V[:,0], V[:,1]); th = np.degrees(np.arctan2(V[:,1], V[:,0])) % 360
print(name)
for sgn, nm in ((1,'z+'),(-1,'z-')):
    zs = np.median(V[(r<Ri+.01)&(V[:,2]*sgn>1),2])
    flat = (np.abs(V[:,2]-zs) < 0.02)
    ff = flat[F].all(1)
    fv = np.unique(F[ff])
    print(f' {nm}: plane z={zs:.4f}, flat faces {ff.sum()}, flat verts {len(fv)}, r {r[fv].min():.4f}..{r[fv].max():.4f}')
    # flange width profile: for each 1-deg bin, max r of flat verts within the connected band (r<Ri+1.5)
    band = fv[r[fv] < Ri+1.5]
    bins = np.floor(th[band]).astype(int)
    w = np.full(360, np.nan)
    for b in range(360):
        s = band[bins==b]
        if len(s): w[b] = r[s].max()-Ri
    print('  flange width (max r-Ri of flat verts, <1.5 band) per-deg: min %.3f med %.3f max %.3f' % (np.nanmin(w), np.nanmedian(w), np.nanmax(w)))
    t0 = w[:60]
    print('  tile 0 (deg 0..59):', ' '.join('%.2f' % x for x in t0))
    same = [np.nanmax(np.abs(w[k*60:(k+1)*60]-t0)) for k in range(1,6)]
    print('  max |diff| other tiles vs tile0:', ['%.3f'%x for x in same])
