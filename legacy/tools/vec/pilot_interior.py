"""Vector rebuild PILOT step 2 (interior): per-shape interior denoise on top of the potrace outline (imports pilot_outline).
Per connected shape: interior level = median(MED) + gaussian(LP) of the CURRENT map normalised inside the shape core (no leakage across shapes,
edge slopes excluded); edge bevel from the sub-pixel SDF. Defaults MED=5 LP=1 ER=3 keep veins, slit grooves and bead rings.
REJECTED variants: LP=5 (erases veins/grooves/bead rings), BEAD=1 (parabolic dome on round shapes, flattens bead rings).
Known: dotted marks on diagonal petal edges sit at the 400 px window borders (petal cut by the window) -> need windowless periodic whole-map run.
usage: python3 tools/vec/pilot_interior.py -> /tmp/vec/pilot2_pair.png (left step 1, right step 2)"""
import sys; sys.path.insert(0, 'tools/vec')
import io, os, contextlib, cv2, numpy as np
from scipy import ndimage as ndi
with contextlib.redirect_stdout(io.StringIO()): import pilot_outline as P
Hw, vec, sdf, W = P.Hw, P.vec, P.sdf, P.W
LP, ER = float(os.environ.get('LP', 1.0)), int(os.environ.get('ER', 3))   # interior denoise sigma (px), core erosion (px)
MED = int(os.environ.get('MED', 5))   # median size: removes speckle, keeps veins/grooves (wider than the noise, narrower than a vein)
sm = ndi.gaussian_filter
lab, n = ndi.label(vec > .5)
m_old = Hw > .3
Hm = cv2.medianBlur((np.clip(Hw, 0, 1) * 65535).astype(np.uint16), MED).astype(np.float32) / 65535 if MED > 1 else Hw
level = np.zeros_like(Hw); beads = 0
for i in range(1, n + 1):
    reg = lab == i; area = reg.sum()
    if area < 30: continue
    core = ndi.binary_erosion(reg & m_old, iterations=ER)
    if core.sum() < 10: core = ndi.binary_erosion(reg & m_old, iterations=2)
    if core.sum() < 5: core = reg & m_old
    w = core.astype(np.float32)
    if w.sum() < 5: continue
    f = sm(Hm * w, LP) / np.maximum(sm(w, LP), 1e-3)
    reg_d = ndi.binary_dilation(reg, iterations=2)
    level[reg_d] = f[reg_d]
    per = max(cv2.arcLength(max(cv2.findContours(reg.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=len), True), 1)
    circ = 4 * np.pi * area / per ** 2
    if os.environ.get('BEAD', '0') == '1' and area < 2500 and circ > .8:   # bead: parabolic dome from SDF (t=1 at centre) - REJECTED
        t = np.clip(sdf / max(sdf[reg].max(), 1e-3), 0, 1)
        level[reg] = (f[reg].mean() * (1 - (1 - t[reg]) ** 2 * .35)); beads += 1
level = np.maximum(level, .35)
bev = np.clip(sdf / W, 0, 1); bev = bev * bev * (3 - 2 * bev)
new = np.clip(level * bev, 0, 1) * np.clip(vec + (sdf > -.3), 0, 1)
def hf(A):
    s = (np.abs(sdf) > 6) & (vec > .5)
    return np.abs(A - sm(A, 3))[s].mean()
print('shapes %d beads %d' % (n, beads))
print('interior HF energy (veins count too): current %.5f  step1 %.5f  step2 %.5f' % (hf(Hw), hf(P.new), hf(new)))
cv2.imwrite('/tmp/vec/pilot2_pair.png', np.hstack([P.shade(P.new), P.shade(new)]))
np.save('/tmp/vec/pilot2.npy', new)
