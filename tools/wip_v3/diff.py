"""Silhouette IoU of a heightmap vs the reference (valid method, not err.py).

usage: python3 tools/wip_v3/diff.py [map.png] [outdir]
  map.png  16-bit period map from a stageNN.py run (default /tmp/band_v3_out/band_period_v50.png)
  outdir   where T2.png lives and where diff_<map>.png is written (default /tmp/band_v3_out)

Ref gold mask: k=4 Lab k-means centres (fixed), gold = nearest of clusters 1 and 3, then 3x3 open+close.
Relief mask: map > 0.3. Writes a diff image: grey = both, red = MISS (gold in ref, not in relief),
blue/orange (BGR 255,160,0) = EXTRA (relief the ref does not have). Prints IoU and the pixel counts.
"""
import sys, os, cv2, numpy as np
mp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/band_v3_out/band_period_v50.png'
Z = (sys.argv[2] if len(sys.argv) > 2 else '/tmp/band_v3_out').rstrip('/') + '/'
CROPX, S, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
TOPCUT = CROPX * S
T2 = cv2.imread(Z + 'T2.png'); ref = T2[TOPCUT:TOPCUT + 520, PW2:2 * PW2]
H = cv2.imread(mp, -1).astype(np.float32) / 65535
H = H[:520]
if H.shape[0] < 520: H = np.vstack([H, np.zeros((520 - H.shape[0], H.shape[1]), np.float32)])
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69, 143, 159], [211, 132, 175], [13, 134, 135], [147, 143, 178]], np.float32)
g = np.isin(((lab[:, :, None, :] - C[None, None]) ** 2).sum(3).argmin(2), [1, 3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
h = H > 0.3
miss, extra = g & ~h, h & ~g
print('IoU %.3f | ref gold %.1f%% relief gold %.1f%% | MISS %d EXTRA %d' % ((g & h).sum() / (g | h).sum(), 100 * g.mean(), 100 * h.mean(), miss.sum(), extra.sum()))
vis = np.zeros(g.shape + (3,), np.uint8); vis[g & h] = (90, 90, 90); vis[miss] = (0, 0, 255); vis[extra] = (255, 160, 0)
out = Z + 'diff_' + os.path.splitext(os.path.basename(mp))[0] + '.png'
cv2.imwrite(out, cv2.resize(vis, (1198, 260), interpolation=cv2.INTER_AREA)); print('wrote', out)
