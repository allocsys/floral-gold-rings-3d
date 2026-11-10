"""stage60 (D30): iso-line (tangential) smoothing of H on steep walls -> removes stair-step hatching / jagged rims without softening the wall profile.
usage: python3 tools/wip_v3/stage60.py [in.png] -> /tmp/band_v3_out/c60.png ; env SIGT (3.0 px smoothing sigma ALONG the iso-line), SIGG (1.5 gradient-direction scale), GLO (.02) / GHI (.06) wall-weight ramp on smoothed |grad H|, ZMIN (0): only where H > ZMIN is touched (ground untouched via ground weight).
Direction = tangent of the smoothed gradient (perpendicular), taps every .75 px over +-3 SIGT, gaussian weights. Output blended by the wall weight w(|grad|). Periodic in x (wrap pad), replicate in y."""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
Z = '/tmp/band_v3_out/'; PAD = 40
SIGT = float(os.environ.get('SIGT', 3.0)); SIGG = float(os.environ.get('SIGG', 1.5)); GLO = float(os.environ.get('GLO', .02)); GHI = float(os.environ.get('GHI', .06))
inp = sys.argv[1] if len(sys.argv) > 1 else Z + 'c59.png'
raw = cv2.imread(inp, -1); H = (raw.astype(np.float32) / 65535)[:520]
Hp = np.pad(H, ((PAD, PAD), (0, 0)), mode='edge'); Hp = np.pad(Hp, ((0, 0), (PAD, PAD)), mode='wrap')
hh, ww = Hp.shape
Gs = cv2.GaussianBlur(Hp, (0, 0), SIGG)
gy, gx = np.gradient(Gs); mag = np.hypot(gx, gy) + 1e-9
# smooth the orientation (structure tensor) so the tangent field is stable on noisy walls
Jxx = cv2.GaussianBlur(gx*gx, (0,0), 2); Jyy = cv2.GaussianBlur(gy*gy, (0,0), 2); Jxy = cv2.GaussianBlur(gx*gy, (0,0), 2)
th = .5*np.arctan2(2*Jxy, Jxx - Jyy)        # dominant gradient angle
tx, ty = -np.sin(th), np.cos(th)            # tangent = perpendicular to gradient
X, Y = np.meshgrid(np.arange(ww, dtype=np.float32), np.arange(hh, dtype=np.float32))
acc = np.zeros_like(Hp); wsum = 0
for k in np.arange(-3*SIGT, 3*SIGT + .01, .75):
    wk = np.exp(-.5*(k/SIGT)**2)
    acc += wk * cv2.remap(Hp, (X + k*tx).astype(np.float32), (Y + k*ty).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    wsum += wk
sm = acc / wsum
w = np.clip((cv2.GaussianBlur(mag, (0,0), 1.0) - GLO) / (GHI - GLO), 0, 1)
w = cv2.GaussianBlur(w, (0,0), 1.0)
out = (Hp + w*(sm - Hp))[PAD:PAD+520, PAD:PAD+2396]
print('wall px (w>.5) %d  mean|dH| on walls %.4f  max |dH| %.3f' % ((w[PAD:PAD+520, PAD:PAD+2396] > .5).sum(), np.abs(out-H)[w[PAD:PAD+520, PAD:PAD+2396] > .5].mean(), np.abs(out-H).max()))
res = raw.copy(); res[:520] = np.clip(out*65535 + .5, 0, 65535).astype(np.uint16)
cv2.imwrite(Z + 'c60.png', res)
