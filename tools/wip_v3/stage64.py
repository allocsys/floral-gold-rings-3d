"""stage64 (D56+D57): map fixes found on the phone (skull-like flower centres, seam spike, star speck). Runs last in chain.sh.
 1. main flower centre bead (x1199.5,y240,r~46): hole + bump -> fitted dome  H = a + b r^2  (annulus r 30..42, applied r<26, blended to 32)
 2. seam flower (map x=0/2396, centre ~(0,258)): skull-shaped centre blob (comp H>20000, rolled coords (1199,258)) -> dome bead e=40000, P=61000
    (sqrt-profile over the distance transform); bottom seam spike (rolled box x1182-1218,y473-506) -> ground
 3. ragged 'star speck' (comp H>8000 at (2012,295)) -> ground
usage: python3 tools/wip_v3/stage64.py [in.png] -> /tmp/band_v3_out/c64.png   (in = 16-bit 520x2396 band map; stage1-63 output)"""
import sys, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'chain_final.png'
H = cv2.imread(inp, -1).astype(np.float64)
assert H.shape == (520, 2396), H.shape
yy, xx = np.mgrid[0:520, 0:2396]
# 1. main centre bead
cy, cx = 240.0, 1199.5
r = np.hypot(yy - cy, xx - cx)
ann = (r >= 30) & (r <= 42)
co = np.linalg.lstsq(np.c_[np.ones(ann.sum()), r[ann] ** 2], H[ann], rcond=None)[0]
w = np.clip((32 - r) / 6, 0, 1)
H = np.round(H * (1 - w) + (co[0] + co[1] * r ** 2) * w).astype(np.uint16).astype(np.float64)   # uint16 round-trip as committed build

def comp(A, thr, pt):
    lab, _ = ndi.label(A > thr, structure=np.ones((3, 3)))
    l = lab[pt[1], pt[0]]; assert l > 0, ('no component at', pt)
    return lab == l
# 2. seam flower centre + spike (roll so the seam flower sits at x=1198)
R = np.roll(H, 1198, axis=1)
m = comp(R, 20000, (1199, 258)); assert m.sum() < 12000, m.sum()
d = ndi.distance_transform_edt(m); t = np.clip(d / d.max(), 0, 1)
R = np.where(m, 40000. + 21000. * np.sqrt(1 - (1 - t) ** 2), R)
box = (xx >= 1182) & (xx <= 1218) & (yy >= 473) & (yy <= 506)
g = np.median(R[(xx >= 1150) & (xx <= 1250) & (yy >= 510) & (yy <= 519)])
wb = ndi.gaussian_filter(box.astype(float), 1.2)
R = R * (1 - wb) + np.minimum(R, g) * wb
H = np.roll(R, -1198, axis=1)
# 3. star speck
m2 = comp(H, 8000, (2012, 295)); assert m2.sum() < 8000, m2.sum()
w2 = ndi.gaussian_filter(ndi.binary_dilation(m2, iterations=3).astype(float), 1.5)
gl = float(np.median(H[(~ndi.binary_dilation(m2, iterations=10)) & ndi.binary_dilation(m2, iterations=16)]))
H = H * (1 - w2) + np.minimum(H, gl) * w2
out = np.round(np.clip(H, 0, 65535)).astype(np.uint16)
print('stage64: seam blob %d px, star %d px, px changed vs input %d' % (m.sum(), m2.sum(), int((out != cv2.imread(inp, -1)).sum())))
cv2.imwrite(Z + 'c64.png', out)
