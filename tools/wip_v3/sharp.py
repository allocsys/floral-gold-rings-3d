"""Sharp-edge probe (D24). usage: python3 tools/wip_v3/sharp.py [map.png] [outdir]   (needs T2.png in outdir, default /tmp/band_v3_out)
Prints (1) rim profile: mean H and ref-L vs signed distance to the ref gold silhouette (+ inside),
(2) |grad H| and |lap H| percentiles for ground / rim +-3px / interior, (3) interior hotspots |grad|>THR (env, default .06).
Writes sharp_vis_a.png / sharp_vis_b.png in outdir: red = interior hotspots, orange = rim px with |grad|>.08.
Site-scale finding (v59): 0.4 mm relief, mesh step .04 mm = 2.1 map px of the 1198-wide site map; median rim wall .086 mm = 2.1 cells, 47% of rim px <2 cells, median wall angle 73 deg (p99 84) -> staircase hatching in the 3D view."""
import sys, os, cv2, numpy as np
mp = sys.argv[1] if len(sys.argv) > 1 else 'maps/band_period.png'
Z = (sys.argv[2] if len(sys.argv) > 2 else '/tmp/band_v3_out').rstrip('/') + '/'; S = Z
CROPX, SS, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX*SS:CROPX*SS+520, PW2:2*PW2]
H = (cv2.imread(mp, -1).astype(np.float32) / 65535)[:520]
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]], np.float32)
g = np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2), [1,3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3,3),np.uint8)), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
L = cv2.cvtColor(cv2.GaussianBlur(ref, (0,0), 1.0), cv2.COLOR_BGR2LAB)[:,:,0].astype(np.float32)
din = cv2.distanceTransform(g, cv2.DIST_L2, 5)          # px inside gold
dout = cv2.distanceTransform(1-g, cv2.DIST_L2, 5)       # px outside
sd = np.where(g > 0, din, -dout)                        # signed distance, + inside
# 1. rim profile: mean H and mean L vs signed distance
print('rim profile (signed px, + inside gold): d | H | L(norm)')
Ln = (L - L[g==0].mean()) / (L[g>0].mean() - L[g==0].mean())
for lo in [-8,-6,-4,-3,-2,-1,0,1,2,3,4,6,8,12,16]:
    m = (sd >= lo) & (sd < lo+1) if lo < 8 else (sd >= lo) & (sd < lo+4)
    print('%4d  H %.3f  L %.3f' % (lo, H[m].mean(), Ln[m].mean()))
# 2. gradient (unsmoothed light blur) hotspots
Hb = cv2.GaussianBlur(H, (0,0), 1.0)
gx = cv2.Sobel(Hb, cv2.CV_32F, 1, 0, ksize=3)/8; gy = cv2.Sobel(Hb, cv2.CV_32F, 0, 1, ksize=3)/8
mag = np.hypot(gx, gy)
lap = np.abs(cv2.Laplacian(Hb, cv2.CV_32F, ksize=3))
for name, a in [('|grad|', mag), ('|lap|', lap)]:
    for lo, hi, tag in [(-99,-3,'ground>3px out'),(-3,3,'rim +-3px'),(3,99,'interior >3px')]:
        m = (sd>=lo)&(sd<hi)
        print('%-7s %-15s n=%7d  p50 %.4f p99 %.4f p99.9 %.4f max %.4f' % (name, tag, m.sum(), np.percentile(a[m],50), np.percentile(a[m],99), np.percentile(a[m],99.9), a[m].max()))
# hotspots interior: |grad| > thr
thr = float(os.environ.get('THR', 0.06))
hot = ((mag > thr) & (sd > 3)).astype(np.uint8)
hot = cv2.morphologyEx(hot, cv2.MORPH_OPEN, np.ones((2,2),np.uint8))
n, lab_, st, cen = cv2.connectedComponentsWithStats(hot, connectivity=8)
big = [(st[i,4], cen[i], mag[lab_==i].max()) for i in range(1,n) if st[i,4] >= 12]
big.sort(key=lambda t: -t[0])
print('interior |grad|>%.3f comps(>=12px): %d, total px %d (%.2f%% of gold interior)' % (thr, len(big), sum(b[0] for b in big), 100*sum(b[0] for b in big)/(sd>3).sum()))
for a,c,mx in big[:12]: print('  area %4d at (x%4d,y%3d) max|g| %.3f' % (a, c[0], c[1], mx))
vis = cv2.cvtColor((H*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
vis[(lab_>0)&np.isin(lab_, [i for i in range(1,n) if st[i,4]>=12])] = (0,0,255)
rim = (np.abs(sd)<2)&(mag>0.08); vis[rim] = (0,200,255)
cv2.imwrite(S+'sharp_vis_a.png', vis[:, :1200]); cv2.imwrite(S+'sharp_vis_b.png', vis[:, 1200:])
