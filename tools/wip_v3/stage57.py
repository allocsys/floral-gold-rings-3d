"""stage57 (D23): remove flat mid-height terraces (artefact patches beside grooves/slits).
usage: CROPX=7 python3 tools/wip_v3/stage57.py [in.png] -> /tmp/band_v3_out/band_period_v57.png ; env HMAX (.65), GMAX (.004), MINA (100), SIG (10), DIL (8 px dilation of the replaced area), FEATH (4 px feather), LMIN (170).
Only patches whose REF luminance (Lab L, T2.png, as cdiff) is bright (mean >= LMIN) are fixed: a terrace under a dark ref region is a real groove/shade (D23: the (159,478) patch, ref L 125, was kept - removing it cost groove prec -.005, ridge prec -.013).
Terrace = connected gold area with H in (.3,HMAX), smoothed |grad H| < GMAX (flat), opened 3x3, area >= MINA. Replaced by normalized-convolution
(gaussian SIG) of the surrounding gold with H>.6, feathered 2px. Everything else untouched (silhouette H>.3 only changes where the patch was <.65 and is raised).
Chain (v59): ... -> stage55 RIB=.22 COMP=1 (c55b) -> stage57 = chain_final.png.
"""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'
HMAX = float(os.environ.get('HMAX', .65)); GMAX = float(os.environ.get('GMAX', .004)); MINA = int(os.environ.get('MINA', 100)); SIG = float(os.environ.get("SIG", 10))
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'c55b.png'
raw = cv2.imread(inp, -1); H = (raw.astype(np.float32) / 65535)[:520]
h = H > .3
g = np.hypot(*np.gradient(ndi.gaussian_filter(H, 1.5)))
m = ndi.binary_opening(h & (H < HMAX) & (g < GMAX), np.ones((3, 3)))
lb, n = ndi.label(m); ar = ndi.sum(m, lb, range(1, n + 1))
CROPX = int(os.environ.get('CROPX', 7)); T2 = cv2.imread(Z + 'T2.png')
ref = T2[CROPX * 2:CROPX * 2 + 520, 2396:2 * 2396]
L = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32)
LMIN = float(os.environ.get('LMIN', 170))
keep = [i for i, a in enumerate(ar, 1) if a >= MINA and L[lb == i].mean() >= LMIN]
print('candidates %d, kept (ref bright) %d' % (int((ar >= MINA).sum()), len(keep)))
patch = np.isin(lb, keep)
print('terraces: %d comps, %d px' % (len(set(lb[patch])), patch.sum()))
pd = ndi.binary_dilation(patch, iterations=int(os.environ.get("DIL", 8)))
valid = (h & ~pd & (H > .6)).astype(np.float32)
num = cv2.GaussianBlur(H * valid, (0, 0), SIG); den = cv2.GaussianBlur(valid, (0, 0), SIG)
fill = np.where(den > 1e-3, num / np.maximum(den, 1e-3), H)
w = cv2.GaussianBlur(pd.astype(np.float32), (0, 0), float(os.environ.get("FEATH", 4))) * pd
H2 = np.where((patch | pd) & h, np.clip(H * (1 - w) + np.maximum(fill, H) * w, 0, 1), H)
H2 = np.where(h, np.maximum(H2, .3001), H2)
out = np.vstack([np.round(H2 * 65535).astype(np.uint16), raw[520:]]) if raw.shape[0] > 520 else np.round(H2 * 65535).astype(np.uint16)
print('px changed %d, H mean in patch %.2f -> %.2f' % (int((np.abs(H2 - H) > 1e-4).sum()), H[patch].mean() if patch.any() else 0, H2[patch].mean() if patch.any() else 0))
cv2.imwrite(Z + 'band_period_v57.png', out); print('wrote v57 (stage57)')
