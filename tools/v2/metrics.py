"""T2+T3 per-class metrics. usage: [MAP=..] [BASE=tools/v2/baseline.json] python3 tools/v2/metrics.py [--save]
Classes from the ref-gold components (R): flower (centre within r<340 of 820,234), bead (area<9000, circularity>.8, outside flower), scroll (rest), ground (outside R dilated 6 px).
Per class: IoU, boundary F1 at 1 px and 2 px tolerance (silhouette edge vs ref edge), gradient-magnitude correlation GC inside gold (|grad ref V| vs |grad H|, lighting independent),
ground GC (ref ground texture vs map ground relief). Prints a table and deltas vs the saved baseline, flagging any metric that drops > .002 (F1/IoU) or > .01 (GC). --save writes the baseline."""
import os, sys, json, cv2, numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(__file__)); from common import *
d = load(os.environ.get('MAP', 'maps/v2/band_period_v2.png')); R, M, H, rc = d['R'], d['M'], d['H'], d['rc']
yy, xx = np.mgrid[:TH, :TW]
lab, n = ndi.label(R); cls = np.zeros((TH, TW), np.uint8)  # 1 flower 2 bead 3 scroll
for i in range(1, n + 1):
    m = lab == i; a = m.sum()
    if a < 150: continue
    cy, cx = ndi.center_of_mass(m); per = (m ^ ndi.binary_erosion(m)).sum()
    circ = 4 * np.pi * a / max(per, 1) ** 2 * 3.0  # crude: perimeter in px counts, scale so a disc ~1
    if np.hypot(cx - 820, cy - 233.7) < 340: cls[m] = 1
    elif a < 9000 and circ > .8: cls[m] = 2
    else: cls[m] = 3
# periodic wrap: flower mask also by disc so merged comps stay flower
cls[(np.hypot(xx - 820, yy - 233.7) < 330) & R] = 1
masks = {'flower': cls == 1, 'bead': cls == 2, 'scroll': cls == 3}
edge = lambda m: m ^ ndi.binary_erosion(m)
def f1(a, b, w, tol):
    ea, eb = edge(a) & w, edge(b) & w
    if ea.sum() == 0 or eb.sum() == 0: return float('nan')
    da, db = ndi.distance_transform_edt(~edge(a)), ndi.distance_transform_edt(~edge(b))
    p = (db[ea] <= tol).mean(); r = (da[eb] <= tol).mean(); return 2 * p * r / max(p + r, 1e-9)
V = cv2.GaussianBlur(cv2.cvtColor(np.clip(rc, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.2)
Hs = cv2.GaussianBlur(H, (0, 0), 1.2)
gm = lambda a: np.hypot(*np.gradient(a)[::-1])
gV, gH = gm(V), gm(Hs)
def corr(a, b, w):
    a, b = a[w], b[w]
    if len(a) < 50: return float('nan')
    a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-9))
res = {}
near = {k: ndi.binary_dilation(m, iterations=8) for k, m in masks.items()}
for k, m in masks.items():
    w = near[k]; a, b = R & w, M & w; u = (a | b).sum()
    inner = ndi.binary_erosion(m, iterations=4)
    res[k] = dict(IoU=float((a & b).sum() / max(u, 1)), F1_1px=f1(R & w, M & w, w, 1.0), F1_2px=f1(R & w, M & w, w, 2.0), GC_gold=corr(gV, gH, inner & M))
gnd = ~ndi.binary_dilation(R | M, iterations=6)
res['ground'] = dict(IoU=float('nan'), F1_1px=float('nan'), F1_2px=float('nan'), GC_gold=corr(gV, gH, gnd))
A = np.ones((TH, TW), bool)
res['all'] = dict(IoU=float((R & M).sum() / (R | M).sum()), F1_1px=f1(R, M, A, 1.0), F1_2px=f1(R, M, A, 2.0), GC_gold=corr(gV, gH, ndi.binary_erosion(R, iterations=4) & M))
base = {}; bp = os.environ.get('BASE', 'tools/v2/baseline.json')
if os.path.exists(bp) and '--save' not in sys.argv: base = json.load(open(bp))
print('%-8s %7s %7s %7s %7s' % ('class', 'IoU', 'F1@1', 'F1@2', 'GCgold')); flags = []
for k, v in res.items():
    row = '%-8s' % k
    for m, tol in (('IoU', .002), ('F1_1px', .002), ('F1_2px', .002), ('GC_gold', .01)):
        x = v[m]; s = '   n/a  ' if x != x else '%7.4f' % x
        if k in base and base[k].get(m) == base[k].get(m) and x == x:
            dd = x - base[k][m]; s += '%+.3f' % dd if abs(dd) >= .0005 else '      '
            if dd < -tol: flags.append('%s.%s %+.4f' % (k, m, dd))
        row += ' ' + s
    print(row)
print('REGRESSIONS: ' + (', '.join(flags) if flags else 'none') if base else 'no baseline (run with --save)')
print('class px: ' + ', '.join('%s %d' % (k, m.sum()) for k, m in masks.items()))
if '--save' in sys.argv: json.dump(res, open(bp, 'w'), indent=1); print('saved', bp)
