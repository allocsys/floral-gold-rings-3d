"""Silhouette jaggedness probe: gold mask (H>.3) signed distance field; roughness = |SDF - gauss(SDF,SIG)| sampled ON the boundary (px, map px; 1 map px = .0167mm..). Also boundary length and sharp-turn count.
usage: python3 tools/wip_v3/jag.py [map.png] [SIG=3]  -> prints mean/p95 boundary deviation, boundary px, contour vertices turning >60deg over 3px (corner count)."""
import sys, cv2, numpy as np
from scipy import ndimage as ndi
mp = sys.argv[1] if len(sys.argv) > 1 else 'maps/band_period.png'; SIG = float(sys.argv[2]) if len(sys.argv) > 2 else 3
H = (cv2.imread(mp, -1).astype(np.float32) / 65535)[:520]
m = H > .3
sdf = ndi.distance_transform_edt(~m) - ndi.distance_transform_edt(m)
sm = ndi.gaussian_filter(sdf, SIG, mode=('nearest', 'wrap'))
b = (np.abs(sdf) <= 1.0)
dev = np.abs(sdf - sm)[b]
cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
corners = 0; tot = 0
for c in cs:
    c = c[:, 0, :].astype(np.float32)
    if len(c) < 12: continue
    p = np.roll(c, -3, 0) - c; q = c - np.roll(c, 3, 0)
    ang = np.degrees(np.abs(np.arctan2(p[:,0]*q[:,1]-p[:,1]*q[:,0], (p*q).sum(1))))
    corners += int((ang > 60).sum()); tot += len(c)
print('boundary px %d | dev vs gauss%.0f: mean %.2f p95 %.2f p99 %.2f | contour px %d, sharp turns(>60deg/3px) %d (%.1f per 1000 px)' % (b.sum(), SIG, dev.mean(), np.percentile(dev, 95), np.percentile(dev, 99), tot, corners, 1000*corners/max(tot,1)))
