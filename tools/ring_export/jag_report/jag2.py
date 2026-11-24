import sys, numpy as np, trimesh
from scipy.ndimage import median_filter
path, Ri, name = sys.argv[1], float(sys.argv[2]), sys.argv[3]
m = trimesh.load(path, process=False)
m.merge_vertices(merge_tex=True, merge_norm=True)
V = np.asarray(m.vertices); F = np.asarray(m.faces)
print(name, 'welded verts', len(V), 'faces', len(F))
r = np.hypot(V[:,0], V[:,1]); th = np.degrees(np.arctan2(V[:,1], V[:,0])) % 360
bore = np.abs(r-Ri) < 2e-3
np.savez(sys.argv[4], V=V, F=F)
out = {}
for sgn, nm in ((1,'z+'),(-1,'z-')):
    sel = np.where(bore & (V[:,2]*sgn > 1.0))[0]
    o = sel[np.argsort(th[sel])]
    t, z = th[o], V[o,2]
    # smooth reference along the loop (circular median)
    k = 15
    zp = np.concatenate([z[-k:], z, z[:k]])
    ref = median_filter(zp, size=2*k+1)[k:-k]
    dev = z - ref
    print(f'\n{nm}: {len(o)} rim verts, z range {z.min():.4f}..{z.max():.4f}, median {np.median(z):.4f}')
    print('  |dev| p50 %.5f p95 %.5f p99 %.5f max %.5f' % tuple(np.percentile(np.abs(dev),[50,95,99,100])))
    # clusters of jags: |dev| > thr
    thr = 0.003
    idx = np.where(np.abs(dev) > thr)[0]
    print(f'  verts with |dev|>{thr}: {len(idx)}')
    # group by angular proximity (<0.5 deg)
    groups = []
    for i in idx:
        if groups and t[i]-groups[-1][-1][0] < 0.5: groups[-1].append((t[i], z[i], dev[i]))
        else: groups.append([(t[i], z[i], dev[i])])
    print('  clusters:', len(groups))
    for g in groups[:60]:
        a = np.array(g)
        c = a[:,0].mean(); seam = min(c%60, 60-c%60)
        print('   theta %.2f (%.2f from 60deg seam)  n=%d  z %.4f  dev %+.4f' % (c, seam, len(g), a[:,1].mean(), a[np.argmax(np.abs(a[:,2])),2]))
