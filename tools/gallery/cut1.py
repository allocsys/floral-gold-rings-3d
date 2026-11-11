import numpy as np
from scipy import ndimage as ndi
from rast import X0, X1, Y0, Y1, H
V = np.load('V.npy'); F = np.load('F.npy'); P = V[F]; C = P.mean(1)
zhi = np.load('zb_hi.npy')
mask = ~np.isnan(zhi)
mask = ndi.binary_closing(mask, iterations=6)
mask = ndi.binary_fill_holes(mask)
MARG = 0.004  # metres of margin so the hole edge lands at the foot of the step, not on top
mask = ndi.binary_dilation(mask, iterations=int(round(MARG / H)))
np.save('mask.npy', mask)
def inmask(x, y):
    ix = np.floor((x - X0) / H).astype(int); iy = np.floor((y - Y0) / H).astype(int)
    ok = (ix >= 0) & (ix < mask.shape[1]) & (iy >= 0) & (iy < mask.shape[0])
    r = np.zeros(len(x), bool); r[ok] = mask[iy[ok], ix[ok]]; return r
# triangle removed if all three vertices are inside the mask and it is on the +z face
vin = np.stack([inmask(P[:, k, 0], P[:, k, 1]) for k in range(3)], 1)
rm = vin.all(1) & (C[:, 2] > 0)
print('removed tris', rm.sum(), 'of', len(F), ' bbox', P[rm].reshape(-1, 3).min(0).round(4), P[rm].reshape(-1, 3).max(0).round(4))
np.save('rm.npy', rm)
keep = F[~rm]
# boundary edges of the hole: edges used by exactly one kept triangle that also border a removed triangle
def edges(f): return np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1)
ek = edges(keep); er = edges(F[rm])
ku, kc = np.unique(ek, axis=0, return_counts=True)
rmset = set(map(tuple, np.unique(er, axis=0)))
bnd = np.array([e for e in ku[kc == 1] if tuple(e) in rmset])
print('hole boundary edges', len(bnd))
bz = V[np.unique(bnd)][:, 2]
print('boundary z: min %.3f median %.3f max %.3f' % (bz.min(), np.median(bz), bz.max()))
np.save('bnd.npy', bnd)
from rast import raster
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
box = (C[:, 0] > -0.16) & (C[:, 0] < 0.16) & (C[:, 1] > 0.57) & (C[:, 1] < 0.77) & (C[:, 2] > 0) & ~rm
zb = raster(P[box])
fig, ax = plt.subplots(1, 1, figsize=(8, 5))
im = ax.imshow(zb, origin='lower', extent=[X0, X1, Y0, Y1], cmap='viridis', vmin=0, vmax=0.22)
ax.set_title('+z after deleting block (white = hole)'); plt.colorbar(im)
plt.savefig('cut1.png', dpi=80)
