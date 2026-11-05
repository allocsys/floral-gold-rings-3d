# usage: python3 tools/vec/petalsmooth.py IN.png OUT.png   (post-step AFTER notches.py, BEFORE ground_dots.py; then wire.py)
# D99: remove faint straight crease/ledge/box facets inside the 7 centre petals (left by the zonal ramp + notch corridor fills).
# Masked (normalised) Gaussian blur PSIG px over the petal plateau only: veins (hysteresis |H-blur3| > PVT strong / PVW weak, comps >= 40 px,
# dilated PVD, faded PVF) and the outer rim bevel (e < PE0..PE1 from the petal edge; near the gap walls r<170 only EI px) are excluded,
# inner bead ramp r < PRA..PRB untouched. Nothing outside the flower plateau changes. Not idempotent-critical (a 2nd run only smooths a bit more).
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, dst = sys.argv[1], sys.argv[2]
E = os.environ.get
CX, CY = 1199.5, 240.0
SIG = float(E('PSIG', 4)); E0 = float(E('PE0', 9)); E1 = float(E('PE1', 16))
RA = float(E('PRA', 48)); RB = float(E('PRB', 66)); VT = float(E('PVT', .03)); VD = int(E('PVD', 3)); EI = float(E('PEI', 3))
H = np.array(Image.open(src)).astype(float) / 65535
h, w = H.shape
yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot(xx - CX, yy - CY)
sm = lambda x: x * x * (3 - 2 * x)
# flower petal plateau = connected H>.45 region touching r~100 on the main flower
F = H > .45
lab, n = ndi.label(F)
ids = np.unique(lab[(np.abs(r - 100) < 3) & F]); ids = ids[ids > 0]
Fm = np.isin(lab, ids) & (r < 320)
e = ndi.distance_transform_edt(Fm)
D = H - ndi.gaussian_filter(H, 3)
vm = (np.abs(D) > VT) & Fm & (e > 6) & (r > 60)
vl, vn = ndi.label(ndi.binary_dilation(vm, iterations=2)); vs = ndi.sum(vm, vl, range(1, vn + 1))
vm &= np.isin(vl, 1 + np.where(vs >= 40)[0])
weak = (np.abs(D) > float(E('PVW', .008))) & Fm & (e > 6) & (r > 60)
vm = ndi.binary_propagation(vm, mask=weak | vm)
veins = ndi.binary_dilation(vm, iterations=VD)
okm = Fm & (e > 2) & ~veins & (r > RA * .7)
wgt = okm.astype(float)
num = ndi.gaussian_filter(H * wgt, SIG); den = ndi.gaussian_filter(wgt, SIG)
Hs = np.where(den > 1e-3, num / np.maximum(den, 1e-3), H)
E0r = EI + (E0 - EI) * sm(np.clip((r - 170) / 40, 0, 1)); E1r = E0r + (E1 - E0)
blend = sm(np.clip((e - E0r) / (E1r - E0r), 0, 1)) * sm(np.clip((r - RA) / (RB - RA), 0, 1))
# do not touch pixels near veins (soft): distance from veins
dv = ndi.distance_transform_edt(~veins)
blend *= sm(np.clip(dv / float(E('PVF', 7)), 0, 1)) * Fm
out = H + blend * (Hs - H)
print('veins px', int(veins[Fm].sum()), 'changed >.002:', int((np.abs(out - H) > .002).sum()), 'max', float(np.abs(out - H).max()))
Image.fromarray(np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)).save(dst)
