"""Breakdown of diff.py MISS/EXTRA: usage: CROPX=7 python3 tools/wip_v3/missstats.py [map.png] [outdir]
Same masks as diff.py. Splits MISS into rim (<=R px from relief edge) and interior components."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
mp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/band_v3_out/band_period_v50.png'
Z = (sys.argv[2] if len(sys.argv) > 2 else '/tmp/band_v3_out').rstrip('/') + '/'
CROPX, S, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H = cv2.imread(mp, -1).astype(np.float32)/65535; H = H[:520]
lab = cv2.cvtColor(cv2.GaussianBlur(ref,(0,0),1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]], np.float32)
g = np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2), [1,3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3,3),np.uint8)), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8)) > 0
h = H > 0.3; miss = g & ~h; extra = h & ~g
d = ndi.distance_transform_edt(~h)           # px (S=2 grid) from relief
print('grid 2396x520 (S=2). MISS %d EXTRA %d' % (miss.sum(), extra.sum()))
for lo, hi in [(0,2),(2,4),(4,8),(8,16),(16,999)]:
    m = miss & (d > lo) & (d <= hi) if lo else miss & (d <= hi)
    print('MISS dist-to-relief (%g,%g] px: %d' % (lo, hi, m.sum()))
core = ndi.binary_opening(miss, np.ones((9,9),bool))      # blobs wider than ~8px = real gaps, not rim
n, lbl, st, cen = cv2.connectedComponentsWithStats(core.astype(np.uint8), 8)
print('MISS core (open 9x9): %d px in %d blobs' % (core.sum(), n-1))
for i in np.argsort(-st[1:,4])[:15]+1:
    print('  blob %d area %d bbox x%d y%d w%d h%d' % (i, st[i,4], st[i,0], st[i,1], st[i,2], st[i,3]))
