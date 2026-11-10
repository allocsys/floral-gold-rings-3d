# usage: python3 tools/vec/veins.py IN.png OUT.png   (post-step AFTER centre_fill.py, BEFORE ground_dots.py; then wire.py)
# D96: clean petal veins on the MAIN (centre) flower. The raster-derived detail, build_map VEIN grooves and centre_fill
# hairlines overlap into 2-3 crowded, stair-stepped lines. Per petal (axis = bead -> tip): flatten a corridor |d|<C by
# interpolating across it from the petal surface on both sides, then carve ONE clean vein = low central rib + 2 smooth
# hairline grooves (even depth, soft ends). Only touches pixels inside the petal interior (bevel + gaps untouched).
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import find_peaks
src, dst = sys.argv[1], sys.argv[2]
E = os.environ.get
CX, CY = [float(v) for v in E('CEN', '1199.5,240').split(',')]
R0 = float(E('R0', 46)); C = float(E('NVC', 34)); SF = float(E('NVSF', .93)); VO = float(E('NVO', 4.5)); VHW = float(E('NVHW', 1.4))
VD = float(E('NVD', .07)); VR = float(E('NVR', .03)); S0 = float(E('NVS0', .12)); S1 = float(E('NVS1', .86)); ER = float(E('NVER', 5)); SG = float(E('NVSG', 6))
H = np.array(Image.open(src)).astype(float) / 65535
h, w = H.shape
yy, xx = np.mgrid[0:h, 0:w]; dx, dy = xx - CX, yy - CY
r = np.hypot(dx, dy); a = np.degrees(np.arctan2(dy, dx)) % 360
# flower component (petals), interior mask = eroded
lab, _ = ndi.label((H > .5) & (r < 320))
ids = np.unique(lab[(np.abs(r - 100) < 3) & (H > .5)]); ids = ids[ids > 0]
fl = np.isin(lab, ids)
print('flower comp px', int(fl.sum()), 'max r', round(float(r[fl].max()), 1))
inner = ndi.binary_erosion(fl, iterations=int(ER))
# petal tips = peaks of max radius per degree
rm = np.array([r[fl & (a >= k) & (a < k + 1)].max() if (fl & (a >= k) & (a < k + 1)).any() else 0 for k in range(360)])
rs = ndi.gaussian_filter1d(rm, 3, mode='wrap')
pk, _ = find_peaks(np.r_[rs, rs[:40]], height=150, distance=20, prominence=6)
tips = sorted({int(p % 360) for p in pk})
print('petal tip angles', tips, [round(float(rs[t])) for t in tips])
def smooth(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
inr = inner.astype(float)
def nconv(A, sg): return ndi.gaussian_filter(A * inr, sg) / np.maximum(ndi.gaussian_filter(inr, sg), 1e-3)
Hn = np.where(inner, nconv(nconv(H, SG), SG), H)       # lines/grooves averaged away, dome kept (edges excluded by the mask)
petals = []
# axis = middle of the petal's angular extent on circles r = 120..170 (H>.5 segments, wedge gaps separate them); L = tip radius
ang = np.linspace(0, 360, 1440, endpoint=False)
def segs(rad):
    v = ndi.map_coordinates(H, [CY + rad * np.sin(np.radians(ang)), CX + rad * np.cos(np.radians(ang))], order=1, mode='wrap') > .5
    return v
for k in tips:
    mids = []
    for rad in (120, 140, 160):
        v = segs(rad); i0 = int(round(k * 4)) % 1440
        if not v[i0]: continue
        lo = i0; hi = i0
        while v[(lo - 1) % 1440] and i0 - lo < 700: lo -= 1
        while v[(hi + 1) % 1440] and hi - i0 < 700: hi += 1
        mids.append(((lo + hi) / 2 % 1440) / 4)
    th = np.radians(float(np.median(mids))) if mids else np.radians(k)
    print('petal tip', k, 'axis', round(float(np.degrees(th)) % 360, 1), 'segment mids', mids)
    petals.append((th, float(rs[k])))
CW = np.zeros(H.shape)
edtw = smooth(ndi.distance_transform_edt(inner) / 7)   # no blend step at the petal-interior edge (stops stair-step bands beside the gap wedges)
for th, L in petals:
    s = dx * np.cos(th) + dy * np.sin(th); d = -dx * np.sin(th) + dy * np.cos(th)
    cw = smooth((C - np.abs(d)) / 16 + .5) * edtw * smooth((SF * L + 10 - s) / 16) * smooth((s - R0 - 6) / 8) * (s > R0 + 4)
    CW = np.maximum(CW, cw)
out = np.where(inner, H * (1 - CW) + Hn * CW, H)
for th, L in petals:
    s = dx * np.cos(th) + dy * np.sin(th); d = -dx * np.sin(th) + dy * np.cos(th)
    s_a, s_b = R0 + 10, S1 * L
    t = (s - s_a) / (s_b - s_a)
    tap = smooth(t / .12) * smooth((1 - t) / .30) * (s > R0)
    off = 1.6 + (VO - 1.6) * smooth(t / .35)
    ad = np.abs(d)
    groove = np.exp(-((ad - off) / VHW) ** 2)
    rib = np.exp(-(d / (VO * .9)) ** 2) * (ad < off + 2)
    m = inner & (s > R0) & (s < s_b + 2) & (ad < VO + 6)
    out = np.where(m, out - VD * tap * groove + VR * tap * rib * (1 - groove), out)
Image.fromarray(np.clip(out * 65535 + .5, 0, 65535).astype(np.uint16)).save(dst)
print('changed px', int((np.abs(out - H) > .004).sum()), 'max', float(np.abs(out - H).max()))
