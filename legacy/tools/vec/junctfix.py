# usage: python3 tools/vec/junctfix.py IN.png OUT.png   (post-step AFTER endfix.py, BEFORE ground_dots.py; then wire.py)
# D101: remove tiny bright/dark specks and streaks where the 7 gap slits meet the bead moat (r JR0..JR1, +-JAW deg of each gap axis).
# Measured: the flecks are not height outliers (median-7 deviation < .006) but stair-steps on the steep slit/moat walls. Fix = light Gaussian (JS px) on that window only, soft-blended; bead dome and far slit walls untouched.
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, dst = sys.argv[1], sys.argv[2]
E = os.environ.get
CX, CY = 1199.5, 240.0
H = np.array(Image.open(src)).astype(float) / 65535
h, w = H.shape
yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot(xx - CX, yy - CY)
ang = np.degrees(np.arctan2(yy - CY, xx - CX)) % 360
sm = lambda x: x * x * (3 - 2 * x)
GAPS = [float(a) for a in E('JGAPS', '28,89,150,213,250,288,325').split(',')]
AW = float(E('JAW', 16)); R0 = float(E('JR0', 44)); R1 = float(E('JR1', 70)); RA = float(E('JRA', 40))
JS = float(E('JS', 1.2)); JK = float(E('JK', 1.0))
sec = np.zeros_like(H)
for a in GAPS:
    d = np.abs((ang - a + 180) % 360 - 180)
    sec = np.maximum(sec, 1 - sm(np.clip((d - (AW - 3)) / 3, 0, 1)))
rad = sm(np.clip((r - RA) / (R0 - RA), 0, 1)) * (1 - sm(np.clip((r - (R1 - 6)) / 6, 0, 1)))
win = sec * rad * JK
M = ndi.gaussian_filter(H, JS)
out = H + win * (M - H)
print('changed >.002:', int((np.abs(out - H) > .002).sum()), 'max', float(np.abs(out - H).max()))
Image.fromarray(np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)).save(dst)
