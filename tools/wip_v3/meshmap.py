"""meshmap (D25): site/mesh-side height map = v59-chain map (ref-truth, untouched) -> 260x1198 8-bit with RIM WALLS WIDENED to >= WCELLS mesh cells.
usage: python3 tools/wip_v3/meshmap.py [map.png] [--out meshmap.png]    (also imported by wire.py when MESH=1)
Why: relief .4 mm, mesh step .04 mm, site px ~.0175 mm => a wall must span >= ~3 mesh cells (.12 mm = 7 site px) to be sampled without staircase/crumpled facets.
Method (wall-only, NOT a uniform blur): site map = INTER_AREA 2x down of the 16-bit map; steep mask = |grad| > GT (H per site px, default .143 = 7px for a full 0..1 step) dilated DIL px, feathered;
inside the mask H -> Gaussian(SIG px, default 2.2) of H; plateaus/ground/gentle shading untouched (mask 0 there). u wraps (periodic).
env: CONE (.16 slope cap per site px; 0 = wall-blur variant) GT (.143) DIL (3) SIG (2.2) FEATH (1.5). Prints wall metrics: fraction of px with |grad|>GT, rim-band |grad| p50/p90/p99, binary (H>.5) IoU vs unmodified, mean|dH|, px changed.
"""
import sys, os, cv2, numpy as np
from scipy import ndimage as ndi
GT = float(os.environ.get('GT', .143)); DIL = int(os.environ.get('DIL', 3)); SIG = float(os.environ.get('SIG', 2.2)); FEATH = float(os.environ.get('FEATH', 1.5))


def site_map(png):
    H = cv2.imread(png, -1); assert H is not None and H.dtype == np.uint16 and H.shape == (520, 2396), (png, None if H is None else H.shape)
    return cv2.resize(H.astype(np.float32) / 65535, (1198, 260), interpolation=cv2.INTER_AREA)


def wrapblur(a, s, pad=24):  # periodic in x (u), reflect in y (v)
    p = np.concatenate([a[:, -pad:], a, a[:, :pad]], 1)
    return cv2.GaussianBlur(p, (0, 0), s, borderType=cv2.BORDER_REFLECT)[:, pad:-pad]


def grad(a, pad=4):
    p = np.concatenate([a[:, -pad:], a, a[:, :pad]], 1)
    gy, gx = np.gradient(p)
    return np.hypot(gx, gy)[:, pad:-pad]


def cone(H, s):  # Lipschitz envelopes: L = max(H - s d) (low side ramps), U = min(H + s d) (high side ramps); (L+U)/2 keeps the .5 contour of an edge, caps every slope at s
    r = int(np.ceil(1 / s)) + 1; y, x = np.mgrid[-r:r + 1, -r:r + 1]; st = (-s * np.hypot(x, y)).astype(np.float32)
    P = np.pad(np.concatenate([H[:, -r:], H, H[:, :r]], 1), ((r, r), (0, 0)), mode='reflect')
    fp = np.ones(st.shape, bool); L = ndi.grey_dilation(P, footprint=fp, structure=st, mode='nearest'); U = ndi.grey_erosion(P, footprint=fp, structure=st, mode='nearest')
    return np.clip(((L + U) / 2)[r:-r, r:-r], 0, 1)


def widen(H):
    if os.environ.get('CONE') != '0': return cone(H, float(os.environ.get('CONE', .16)))   # default: slope cap .16 per site px (CONE=0 -> old wall-blur variant)
    g = grad(H)
    m = (g > GT).astype(np.float32)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * DIL + 1,) * 2))
    w = np.clip(wrapblur(m, FEATH) * 1.5, 0, 1) if FEATH > 0 else m
    return np.clip(H * (1 - w) + wrapblur(H, SIG) * w, 0, 1)


def metrics(tag, H, ref=None):
    g = grad(H); rim = (H > .08) & (H < .92) & (g > .03)
    s = '%s: |grad|>GT %.4f of px | rim-band |grad| p50 %.3f p90 %.3f p99 %.3f' % (tag, (g > GT).mean(), *np.percentile(g[rim], [50, 90, 99]))
    if ref is not None:
        a, b = ref > .5, H > .5
        s += ' | IoU(H>.5) %.4f | mean|dH| %.4f | px |dH|>.02: %d' % ((a & b).sum() / (a | b).sum(), np.abs(H - ref).mean(), int((np.abs(H - ref) > .02).sum()))
    print(s)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    png = a[0] if a else '/tmp/band_v3_out/chain_final.png'
    H = site_map(png); H2 = widen(H)
    metrics('site map     ', H); metrics('mesh map     ', H2, H)
    if '--out' in sys.argv:
        o = sys.argv[sys.argv.index('--out') + 1]; cv2.imwrite(o, np.round(H2 * 255).astype(np.uint8)); print('wrote', o)


if __name__ == '__main__':
    main()
