"""T4 fast relief shader (numpy, ~1 s, no 3D render). usage: [WIN=x,y,r] [Z=2] [S=40] [MAP=..] python3 tools/v2/shade.py out.png
Sheet = ref | hillshade lit from NW (identical to the *_hillshade.png) | NE | SW | top-down spec (Blinn-Phong, grey) | ambient-occlusion-lite (H minus its 12 px blur, signed).
Greyscale only (colour only if asked). S = height scale in the normal (make_map_v2.py uses 40). Without WIN: full map at 1/2 scale, 3 rows of 2."""
import os, sys, time, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import *
t0 = time.time()
out = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/shade.png'
S = float(os.environ.get('S', 40)); Z = float(os.environ.get('Z', 2)); d = load(os.environ.get('MAP', 'maps/v2/band_period_v2.png')); H = d['H']
gy, gx = np.gradient(H * S); nn = np.dstack([-gx, -gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
def lam(L): L = np.array(L, float); L /= np.linalg.norm(L); a = np.clip(nn @ L, 0, 1); return a / max(a.max(), 1e-6)
def spec(L=(0, 0, 1), V=(0, 0, 1), k=40):
    L, V = np.array(L, float), np.array(V, float); Hh = L / np.linalg.norm(L) + V / np.linalg.norm(V); Hh /= np.linalg.norm(Hh)
    return np.clip(nn @ Hh, 0, 1) ** k
ao = cv2.GaussianBlur(H, (0, 0), 12) - H
u8 = lambda a: np.clip(a * 255, 0, 255).astype(np.uint8)
tiles = [('ref', cv2.cvtColor(np.clip(d['rc'], 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)), ('light NW', u8(lam((-1, -1, 1.2)))), ('light NE', u8(lam((1, -1, 1.2)))),
         ('light SW', u8(lam((-1, 1, 1.2)))), ('spec top', u8(spec() * .9 + lam((-1, -1, 1.2)) * .25)), ('AO-lite', u8(.5 + np.clip(ao * 6, -.5, .5)))]
if os.environ.get('WIN'):
    x, y, r = [float(v) for v in os.environ['WIN'].split(',')]; x0, y0, x1, y1 = max(0, int(x - r)), max(0, int(y - r)), min(TW, int(x + r)), min(TH, int(y + r))
    tiles = [(n, a[y0:y1, x0:x1]) for n, a in tiles]
else: Z = min(Z, .5) if Z > .5 and not os.environ.get('Z') else Z; tiles = [(n, a) for n, a in tiles]
def prep(n, a):
    f = Z if os.environ.get('WIN') else .5; a = cv2.cvtColor(cv2.resize(a, None, fx=f, fy=f, interpolation=cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC), cv2.COLOR_GRAY2BGR)
    cv2.putText(a, n, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 255, 255), 2); return a
T = [prep(n, a) for n, a in tiles]; sheet = np.vstack([np.hstack(T[i:i + 2]) for i in range(0, 6, 2)])
cv2.imwrite(out, sheet); print(out, sheet.shape, '%.2fs' % (time.time() - t0))
