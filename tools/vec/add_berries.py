#!/usr/bin/env python3
"""D75 (I4): add glossy berries in free ground gaps of the band map (ref has ~20+ berries, map had ~8).
Greedy: biggest free ground disc (periodic in x) -> round dome, until no gap >= DMIN. Deterministic.
usage: python3 tools/vec/add_berries.py IN.png OUT.png   (env DMIN 30, RMAX 38, RMIN 22, NMAX 14, PEAK .75, MARGIN 55, GAP 6)
"""
import os, sys
import numpy as np
import scipy.ndimage as ndi
from PIL import Image

E = lambda k, d: float(os.environ.get(k, d))
DMIN, RMAX, RMIN, NMAX, PEAK, MARGIN, GAP = E('DMIN', 30), E('RMAX', 38), E('RMIN', 22), int(E('NMAX', 14)), E('PEAK', .75), E("MARGIN", 55), E('GAP', 6)
PAD = 100


def main(src, dst):
    m16 = np.array(Image.open(src)).astype(np.float64)
    m = m16 / 65535.0
    H, W = m.shape
    ground = np.pad(m < 0.05, ((0, 0), (PAD, PAD)), mode='wrap')
    yy, xx = np.mgrid[0:H, 0:W + 2 * PAD]
    placed = []
    for _ in range(NMAX):
        d = ndi.distance_transform_edt(ground)
        d[:int(MARGIN + RMIN)] = 0
        d[H - int(MARGIN + RMIN):] = 0
        d[:, :PAD] = 0          # candidates only in the real columns; the padding just supplies the wrap
        d[:, W + PAD:] = 0
        cy, cx = np.unravel_index(np.argmax(d), d.shape)
        dm = d[cy, cx]
        if dm < DMIN:
            break
        r = float(np.clip(dm - GAP, RMIN, RMAX))
        r = min(r, cy - MARGIN, H - 1 - cy - MARGIN)
        rho = np.hypot(xx - cx, yy - cy)
        ground[rho < r + GAP] = False
        placed.append(((cx - PAD) % W, cy, r))
        # dome: sqrt-ish cap with a short wall, like the existing berries
        t = np.clip(rho / r, 0, 1.2)
        cap = PEAK * np.clip(1 - t ** 2, 0, 1) ** 0.55
        wall = np.clip((1.0 - t) / 0.06, 0, 1)   # ~3 px wall so the rim is steep but not a cliff
        h = cap * wall
        # fold the padded canvas back onto the map (periodic)
        hp = h[:, PAD:PAD + W].copy()
        hp[:, :PAD] = np.maximum(hp[:, :PAD], h[:, PAD + W:PAD + W + PAD])
        hp[:, W - PAD:] = np.maximum(hp[:, W - PAD:], h[:, :PAD])
        m = np.maximum(m, hp)
    out = np.clip(np.round(m * 65535.0), 0, 65535).astype(np.uint16)
    Image.fromarray(out).save(dst)
    for x, y, r in placed:
        print('berry x%4d y%3d r%4.1f' % (x, y, r))
    print(len(placed), 'berries; px changed', int((out != m16).sum()))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
