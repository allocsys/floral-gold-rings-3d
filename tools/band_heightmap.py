#!/usr/bin/env python3
"""Build the Band relief height map from reference/rings_flat.png.
Usage: python3 tools/band_heightmap.py   (needs opencv-python, numpy, scipy)
Outputs: maps/band_height.png (16-bit, 0=recess, 65535=top) and maps/band_preview.png
"""
import cv2, numpy as np, os
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ref = cv2.imread(os.path.join(ROOT, 'reference/rings_flat.png'))
crop = ref[255:425, 25:760]                       # top-left ring
im = cv2.resize(crop, None, fx=2.2, fy=2.2, interpolation=cv2.INTER_CUBIC)
c = im[48:308, 66:1502]; H, W = c.shape[:2]       # engraved window

L = cv2.cvtColor(c, cv2.COLOR_BGR2LAB).astype(np.float32)[..., 0]
sd = np.sqrt(np.maximum(cv2.GaussianBlur(L*L, (0,0), 3) - cv2.GaussianBlur(L, (0,0), 3)**2, 0))
score = cv2.GaussianBlur(L, (0,0), 2.5) - 0.6*sd

def build(close_k, hole_max):
    m = (score > 104).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k,)*2))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5)))
    inv = 1 - m; l, n = ndi.label(inv); sz = ndi.sum(inv, l, range(1, n+1))
    for i, s in enumerate(sz):
        if s < hole_max: m[l == i+1] = 1
    return m

big, small = build(13, 1200), build(7, 120)
zone = np.zeros((H, W), np.float32)
for cx in (147, 746, 1341): cv2.ellipse(zone, (cx,130), (125,150), 0, 0, 360, 1, -1)
zone = cv2.GaussianBlur(zone, (0,0), 12)
m = np.where(zone > .5, small, big).astype(np.uint8)

g8 = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY).astype(np.float32)
bh = cv2.morphologyEx(cv2.GaussianBlur(g8, (0,0), 1.2), cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13,13)))
slit = ((bh > 38) & (zone > .5)).astype(np.uint8)
slit = cv2.morphologyEx(slit, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2,2)))
l, n = ndi.label(slit); sz = ndi.sum(slit, l, range(1, n+1))
for i, s in enumerate(sz):
    if s < 60: slit[l == i+1] = 0
m[slit > 0] = 0
l, n = ndi.label(m); sz = ndi.sum(m, l, range(1, n+1))
for i, s in enumerate(sz):
    if s < 250: m[l == i+1] = 0
m = (cv2.GaussianBlur(m.astype(np.float32), (0,0), 1.3) > .5).astype(np.uint8)

# beads (x, y, r) in window coordinates, placed by hand from the reference; flower centres separate
BEADS = [(95,38,22),(330,43,24),(365,165,22),(228,240,18),(510,238,26),(598,118,21),(890,115,22),
         (745,243,10),(975,235,26),(1115,165,26),(1255,240,20),(1390,35,24),(1215,75,22),(950,28,20),
         (1105,22,18),(1138,38,16),(278,78,16),(88,238,18)]
CENTRES = [(147,133,24),(746,128,26),(1341,133,24)]

d = cv2.distanceTransform(m, cv2.DIST_L2, 5)
loc = cv2.GaussianBlur(cv2.dilate(d, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31,31))), (0,0), 5)
x = np.clip(d / np.clip(loc, 6, 26), 0, 1)
h = cv2.GaussianBlur(np.sqrt(1 - (1-x)**2), (0,0), 1.6)
hs = cv2.GaussianBlur(np.where(m > 0, .25 + .75*h, 0).astype(np.float32), (0,0), 1.0)
yy, xx = np.mgrid[0:H, 0:W]
for lst, top in ((BEADS, 1.0), (CENTRES, .95)):
    for bx, by, r in lst:
        rr = np.sqrt((xx-bx)**2 + (yy-by)**2)
        dome = np.where(rr < r, .3 + (top-.3)*np.sqrt(np.clip(1-(rr/r)**2, 0, 1)), 0)
        hs = np.where(rr < r, np.maximum(hs, dome), hs)
hs = hs.astype(np.float32)

os.makedirs(os.path.join(ROOT, 'maps'), exist_ok=True)
cv2.imwrite(os.path.join(ROOT, 'maps/band_height.png'), (hs*65535).astype(np.uint16))
gg = hs*30
gx = cv2.Sobel(gg, cv2.CV_32F, 1, 0, ksize=3)/8; gy = cv2.Sobel(gg, cv2.CV_32F, 0, 1, ksize=3)/8
nn = np.dstack([-gx, -gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
Ld = np.array([-.4, -.6, .69]); Ld /= np.linalg.norm(Ld)
dif = np.clip(nn @ Ld, 0, 1)
spec = np.clip((2*(nn@Ld)[..., None]*nn - Ld)[..., 2], 0, 1)**25
col = dif[..., None]*np.array([60,170,240])/255.*.85 + spec[..., None]*.7 + .04
col = np.where(hs[..., None] > .05, col, np.array([18,30,45])/255.*(.6 + .4*dif[..., None]))
cv2.imwrite(os.path.join(ROOT, 'maps/band_preview.png'),
            np.vstack([c, cv2.applyColorMap((hs*255).astype(np.uint8), cv2.COLORMAP_VIRIDIS), (np.clip(col,0,1)*255).astype(np.uint8)]))
print('ok', hs.shape)
