"""Zonal outline smoothing that keeps sharp features (D80).
Smooths gold outlines ONLY in the vine/oval-frame zone, and only where the outline is smooth-ish AND wide:
  - tips / corners (high curvature of the signed distance field) are protected,
  - thin veins, ridges and slits (local feature width < RW map px) are protected,
  - the flower comps and the seam zone (|x-seam| < SZ) are not touched.
Method: phi = sub-pixel SDF of the H>.3 mask; phi_s = gaussian(phi, S); H_new(x) = H(x + (phi_s-phi)*n) (level-set warp of the
bevel profile, so wall shape is kept), blended by the protect weight. Interior/ground are flat so the warp is a no-op there.
usage: python3 tools/vec/zonal.py IN.png OUT.png   (run after build_map.py + add_berries.py, before wire.py)"""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
IN, OUT = sys.argv[1], sys.argv[2]
S = float(os.environ.get('ZS', 7))        # outline smoothing sigma (map px)
KC = float(os.environ.get('ZKC', 0.14))     # curvature (1/px) above which the outline is a tip/corner -> protected
RW = float(os.environ.get('ZRW', 9.0))      # min local feature half-width (map px) to be smoothed; thinner = vein/slit -> protected
SZ = float(os.environ.get('ZSZ', 330))      # seam exclusion half-width
ZA = int(os.environ.get('ZA', 12000))       # min comp area for the zone
FLOW = [tuple(float(v) for v in c.split(',')) for c in os.environ.get('ZFLOWERS', '1199.5,240').split(';') if c.strip()]
PAD, UP = 40, 3
H0 = cv2.imread(IN, -1).astype(np.float32)[:520] / 65535
Hw = np.pad(np.pad(H0, ((0, 0), (PAD, PAD)), mode='wrap'), ((PAD, PAD), (0, 0)), mode='edge')
sh = Hw.shape
sm = ndi.gaussian_filter
m = Hw > .3
# --- zone: big comps, not the flowers, not near the seam
lab, n = ndi.label(m); ar = np.bincount(lab.ravel(), minlength=n + 1)
keep = (ar > ZA) & (np.arange(n + 1) > 0)
for fx, fy in FLOW:
    l = lab[int(fy + PAD), int(fx + PAD)]
    if l > 0:
        # flower comp: only exclude it if it is NOT the vine (vine comp is the biggest one); exclude by radius instead
        pass
Y, X = np.mgrid[:sh[0], :sh[1]]
zone = keep[lab]
for fx, fy in FLOW:
    zone &= np.hypot(X - (fx + PAD), Y - (fy + PAD)) > float(os.environ.get('ZFR', 230))   # flower petals + centre excluded
cm = (X - PAD) % 2396.0; dseam = np.minimum(cm, 2396.0 - cm)
zone &= dseam > SZ
zone_d = sm(ndi.binary_dilation(zone, iterations=14).astype(np.float32), 4)   # smooth spatial weight (also covers the ground next to the comp edge)
_, ind = ndi.distance_transform_edt(lab == 0, return_indices=True)
near_lab = lab[ind[0], ind[1]]
zone_d *= zone[ind[0], ind[1]]     # only pixels whose NEAREST gold comp is a zone comp (berries/beads next to the vine stay untouched)
# --- sub-pixel SDF of the gold mask
B = cv2.resize(sm(Hw, .6), None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC) > .3
phi = cv2.resize(((ndi.distance_transform_edt(B) - ndi.distance_transform_edt(~B)) / UP).astype(np.float32), (sh[1], sh[0]), interpolation=cv2.INTER_AREA)
phi = sm(phi, 1.0)
phis = sm(phi, S)
# --- curvature of phi (smoothed 1.5): kappa = div(grad/|grad|)
p1 = sm(phi, 1.5); gy, gx = np.gradient(p1); g = np.maximum(np.hypot(gx, gy), 1e-3)
kap = np.abs(np.gradient(gx / g, axis=1) + np.gradient(gy / g, axis=0))
tip = ndi.maximum_filter(kap * (np.abs(phi) < 6), size=9) > KC          # any pixel within ~4 px of a high-curvature edge point
tipw = sm(tip.astype(np.float32), 3); tipw = np.clip(tipw * 2.5, 0, 1)
# --- feature width: gold half-width (max phi nearby) and ground half-width (max -phi nearby); thin on either side -> protect
wg = ndi.maximum_filter(np.maximum(phi, 0), size=int(2 * RW + 1)); wb = ndi.maximum_filter(np.maximum(-phi, 0), size=int(2 * RW + 1))
thin = (np.minimum(wg, wb) < RW * 0.55) | (wg < RW * 0.8)
thinw = sm(thin.astype(np.float32), 2.5); thinw = np.clip(thinw * 1.5, 0, 1)
protect = np.maximum(tipw, thinw)
wgt = np.clip(zone_d, 0, 1) * (1 - protect)
# --- level-set warp
n_x, n_y = gx / g, gy / g
wgt = sm(wgt, float(os.environ.get('ZWS', 2.0)))
dlt = sm((phis - phi) * wgt, float(os.environ.get('ZDS', 1.5)))
dlt = np.clip(dlt, -S * 1.2, S * 1.2)
mx = (X + dlt * n_x).astype(np.float32); my = (Y + dlt * n_y).astype(np.float32)
Hn = cv2.remap(Hw, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
Hn = np.where(wgt > 1e-3, Hn, Hw)
new = np.clip(Hn[PAD:-PAD, PAD:-PAD], 0, 1)
cv2.imwrite(OUT, np.round(new * 65535).astype(np.uint16))
ch = np.abs(new - H0)
print('zone px %d  warped(wgt>.5) %d  protected tip %d thin %d | changed>.02: %d  max|d| %.3f' % (zone.sum(), (wgt > .5).sum(), (tipw > .5).sum(), (thinw > .5).sum(), (ch > .02).sum(), ch.max()))
# debug maps
if os.environ.get('ZDBG'):
    dbg = np.dstack([protect, wgt, zone_d])[PAD:-PAD, PAD:-PAD]
    cv2.imwrite(os.environ['ZDBG'], (dbg * 255).astype(np.uint8))
