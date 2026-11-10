"""v2 rebuild step 1: cut ONE period (flower-centred) of the panel out of reference/band_face.png (2172x724 new ref)
and make a first-pass gold mask. Measured: panel rows 215..472 (258 px), period 813 px (autocorr), flower-centre beads at x~282/1085/1900, y 331.
usage: python3 tools/v2/extract_tile.py  -> maps/v2/tile_ref.png (colour tile 258x814, flower at x=407), maps/v2/tile_mask0.png (first-pass mask, needs hand-fixing: shaded scroll parts are lost)"""
import cv2, numpy as np
im = cv2.imread('reference/band_face.png'); y0, y1, cx, P = 215, 473, 1085, 813
tile = im[y0:y1, cx - P // 2: cx - P // 2 + P + 1]
b = cv2.GaussianBlur(cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY), (0, 0), 1.5)
t, _ = cv2.threshold(b, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
m = cv2.morphologyEx((b > t * .85).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m); keep = np.zeros_like(m)
for i in range(1, n):
    if st[i, 4] >= 60: keep[lab == i] = 1
cv2.imwrite('maps/v2/tile_ref.png', tile); cv2.imwrite('maps/v2/tile_mask0.png', keep * 255)
