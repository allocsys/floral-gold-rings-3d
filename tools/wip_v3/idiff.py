"""Interior diff: dark lines inside the ref gold (petal edges, creases, veins) vs grooves in the map.
usage: CROPX=7 python3 tools/wip_v3/idiff.py [map.png] [outdir]
Region = ref gold mask (same as diff.py) eroded RIM px. Ref lines = black-tophat of Lab-L (kernel K) > TL.
Map grooves = black-tophat of H (kernel K) > TH. Tolerance TOL px. Writes idiff_<map>.png:
green = both, red = ref line missing in map (MISSL), blue = map groove the ref doesn't have (EXTRAL)."""
import sys, os, cv2, numpy as np
mp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/band_v3_out/band_period_v51.png'
Z = (sys.argv[2] if len(sys.argv) > 2 else '/tmp/band_v3_out').rstrip('/') + '/'
CROPX, S, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
RIM, K, TL, TH, TOL = 8, 21, 14, 0.12, 4
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H = (cv2.imread(mp, -1).astype(np.float32) / 65535)[:520]
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]], np.float32)
g = np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2), [1,3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3,3),np.uint8)), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
reg = cv2.erode(g, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*RIM+1,)*2)) > 0
# bead/dome interiors are smooth gold; ignore nothing else here, report everything in the region
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (K, K))
L = cv2.GaussianBlur(ref, (0,0), 1.0); L = cv2.cvtColor(L, cv2.COLOR_BGR2LAB)[:,:,0].astype(np.float32)
dl = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, k) > TL
dh = cv2.morphologyEx(H, cv2.MORPH_BLACKHAT, k) > TH
dl &= reg; dh &= reg
t = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*TOL+1,)*2)
near_h = cv2.dilate(dh.astype(np.uint8), t) > 0; near_l = cv2.dilate(dl.astype(np.uint8), t) > 0
both_l = dl & near_h; both_h = dh & near_l
rec = both_l.sum() / max(dl.sum(), 1); pre = both_h.sum() / max(dh.sum(), 1)
print('region %d px | ref dark-line px %d (%.1f%% of region) | map groove px %d (%.1f%%)' % (reg.sum(), dl.sum(), 100*dl.sum()/reg.sum(), dh.sum(), 100*dh.sum()/reg.sum()))
print('line recall %.3f (ref lines that have a map groove within %d px) | groove precision %.3f | MISSL %d EXTRAL %d' % (rec, TOL, pre, (dl & ~near_h).sum(), (dh & ~near_l).sum()))
vis = (ref * 0.35).astype(np.uint8); vis[~reg] = (vis[~reg] * 0.5).astype(np.uint8)
vis[both_l | both_h] = (0, 200, 0); vis[dl & ~near_h] = (0, 0, 255); vis[dh & ~near_l] = (255, 120, 0)
out = Z + 'idiff_' + os.path.splitext(os.path.basename(mp))[0] + '.png'
cv2.imwrite(out, cv2.resize(vis, (1198, 260), interpolation=cv2.INTER_AREA)); print('wrote', out)
