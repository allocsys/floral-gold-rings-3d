# usage: python3 tools/vec/endfix.py IN.png OUT.png   (post-step AFTER petalsmooth.py, BEFORE ground_dots.py; then wire.py)
# D100: remove the soft ledge/dip just past the inner vein ends in the two upper petals (axes ~236 and ~302 deg) next to the bead.
# Masked Gaussian (ESIG) over the petal plateau only, in a sector (+-EAW deg) and radius band ER0..ER1 (soft ramps), excluding rim (e<EE),
# gap walls (angle) and bead ramp (r<RA). Strong vein pixels (|H-blur3|>EVT, comps>=40 px, dilated EVD, softened) keep their original height,
# so the hairlines stay and only the weak terrace/ledge around their inner ends is flattened.
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
AX = [float(a) for a in E('EAXES', '236,302').split(',')]
AW = float(E('EAW', 24)); R0 = float(E('ER0', 62)); R1 = float(E('ER1', 118)); RA = float(E('ERA', 66)); RB = float(E('ERB', 74))
SIG = float(E('ESIG', 7)); EE = float(E('EE', 6)); VT = float(E('EVT', .03)); VD = int(E('EVD', 2))
F = H > .45
lab, n = ndi.label(F)
ids = np.unique(lab[(np.abs(r - 100) < 3) & F]); ids = ids[ids > 0]
Fm = np.isin(lab, ids) & (r < 320)
e = ndi.distance_transform_edt(Fm)
sec = np.zeros_like(H)
for a in AX:
    d = np.abs((ang - a + 180) % 360 - 180)
    sec = np.maximum(sec, 1 - sm(np.clip((d - (AW - 6)) / 6, 0, 1)))
rad = sm(np.clip((r - RA) / (RB - RA), 0, 1)) * (1 - sm(np.clip((r - (R1 - 14)) / 14, 0, 1)))
okm = (Fm & (e > EE) & (r > RA * .8)).astype(float)
num = ndi.gaussian_filter(H * okm, SIG); den = ndi.gaussian_filter(okm, SIG)
Hs = np.where(den > 1e-3, num / np.maximum(den, 1e-3), H)
D = H - ndi.gaussian_filter(H, 3)
vm = (np.abs(D) > VT) & Fm & (e > 6) & (r > 60)
vl, vn = ndi.label(ndi.binary_dilation(vm, iterations=2)); vs = ndi.sum(vm, vl, range(1, vn + 1))
vm &= np.isin(vl, 1 + np.where(vs >= 40)[0])
vk = ndi.gaussian_filter(ndi.binary_dilation(vm, iterations=VD).astype(float), 1.5)
Hs = Hs + np.clip(vk * 1.6, 0, 1) * (H - Hs)
blend = sec * rad * sm(np.clip((e - EE) / 6, 0, 1)) * Fm
out = H + blend * (Hs - H)
print('changed >.002:', int((np.abs(out - H) > .002).sum()), 'max', float(np.abs(out - H).max()))
Image.fromarray(np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)).save(dst)
