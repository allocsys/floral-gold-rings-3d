"""T1 zoom compare sheet. usage: WIN=x,y,r [Z=4] [MAP=maps/v2/band_period_v2.png] python3 tools/v2/zoom.py out.png
Rows: ref crop | map hillshade | ref gold edge (green) vs map edge (magenta) on ref | |H - ref| none. All at Z x, same crop, labelled with map coords."""
import os, sys, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import *
out = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/zoom.png'
x, y, r = [float(v) for v in os.environ.get('WIN', '820,234,120').split(',')]; Z = int(os.environ.get('Z', 4))
d = load(os.environ.get('MAP', 'maps/v2/band_period_v2.png'))
x0, y0, x1, y1 = max(0, int(x - r)), max(0, int(y - r)), min(TW, int(x + r)), min(TH, int(y + r))
c = lambda a: a[y0:y1, x0:x1]
big = lambda a, i=cv2.INTER_CUBIC: cv2.resize(a, None, fx=Z, fy=Z, interpolation=i)
ref = big(np.clip(c(d['rc']), 0, 255).astype(np.uint8))
hs = d['HS'] if d['HS'] is not None else (np.clip(d['H'], 0, 1) * 255).astype(np.uint8)
hsb = cv2.cvtColor(big(c(hs)), cv2.COLOR_GRAY2BGR)
def edge(m): m = m.astype(np.uint8); return m - cv2.erode(m, np.ones((3, 3), np.uint8))
ov = ref.copy() // 2
for m, col in ((d['R'], (0, 255, 0)), (d['M'], (255, 0, 255))):
    e = big(c(edge(m)).astype(np.uint8), cv2.INTER_NEAREST) > 0; ov[e] = col
Ht = cv2.cvtColor(big((np.clip(c(d['H']) / max(d['H'].max(), 1e-6), 0, 1) * 255).astype(np.uint8)), cv2.COLOR_GRAY2BGR)
def lab(a, t): a = a.copy(); cv2.putText(a, t, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 255), 2); return a
sheet = np.vstack([np.hstack([lab(ref, 'ref %d,%d..%d,%d x%d' % (x0, y0, x1, y1, Z)), lab(hsb, 'map hillshade')]),
                   np.hstack([lab(ov, 'ref edge GREEN / map edge MAGENTA'), lab(Ht, 'map height')])])
cv2.imwrite(out, sheet); print(out, sheet.shape)
