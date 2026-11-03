"""meshq (D26): mesh-side quality probe. Replicates site/geometry.js (mip choice, bilinear, periodic u, vertex grid, fade) for one band and measures what the 3D surface sees.
usage: python3 tools/wip_v3/meshq.py [--band band1|band2] [--float]   (--float = same pipeline but un-quantised map: maps/band_period.png -> 2x INTER_AREA -> cone, no 8-bit rounding)
Prints: (1) seam: |dH| across the u wrap vs adjacent-column stats, slope jump; (2) normal roughness |slope - gauss(slope, 2 cells)| on the real vertex grid (mm/mm ~ rad), split by region
(rim = |grad hv|>.06 per cell, gold = hv>.6 and >3 cells from a rim, ground = hv<.1) and by component (u = along ring, v = across band); (3) fraction of gold cells whose 8-bit level steps (quantisation terracing).
"""
import sys, os, re, base64, math, cv2, numpy as np
from scipy import ndimage as ndi
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
BANDS = {'band1': dict(ID=19, w=4.5, t=1.5), 'band2': dict(ID=17, w=4.0, t=1.4)}
REL, REPEATS, FADE, RF = .4, 3, .3, .32
STEP = float(os.environ.get('STEP', .04))  # mesh step in mm (site: fine .04, draft .12)
TAU = 2 * math.pi


def load_site():
    js = open(os.path.join(ROOT, 'site/relief_band.js')).read()
    W, H = (int(re.search(k + r':\s*(\d+)', js).group(1)) for k in ('W', 'H'))
    return (np.frombuffer(base64.b64decode(re.search(r"b64:\s*'([^']*)'", js).group(1)), np.uint8).reshape(H, W).astype(np.float32) / 255)


def float_site():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import meshmap
    return meshmap.widen(meshmap.site_map(os.path.join(ROOT, 'maps/band_period.png')))


def mips(a):
    m = [a]
    while True:
        b = m[-1]; H, W = b.shape[0] >> 1, b.shape[1] >> 1
        if W < 8 or H < 4: break
        m.append(b[:2 * H, :2 * W].reshape(H, 2, W, 2).mean((1, 3)))
    return m


def sample(L, u, v):  # bilinear, periodic u, clamped v (as sampleRelief)
    H, W = L.shape; x = u * W - .5; y = np.clip(v * H - .5, 0, H - 1)
    x0 = np.floor(x).astype(int); y0 = np.minimum(np.floor(y).astype(int), H - 2); fx = x - x0; fy = y - y0
    X0, X1 = x0 % W, (x0 + 1) % W
    return (L[y0, X0] * (1 - fx) + L[y0, X1] * fx) * (1 - fy) + (L[y0 + 1, X0] * (1 - fx) + L[y0 + 1, X1] * fx) * fy


def sample_cubic(L, u, v, P=6):  # cubic B-spline interpolation (C2), periodic u via wrap padding, clamped v via edge padding; same pixel-centre convention as sample()
    from scipy.ndimage import map_coordinates
    u, v = np.broadcast_arrays(u, v); H, W = L.shape; Lp = np.pad(np.concatenate([L[:, -P:], L, L[:, :P]], 1), ((P, P), (0, 0)), mode='edge')
    x = u * W - .5 + P; y = np.clip(v * H - .5, 0, H - 1) + P
    return map_coordinates(Lp, [y, x], order=3, mode='nearest')


def gwrap(a, s):
    return ndi.gaussian_filter(a, s, mode=('nearest', 'wrap'))


def seam(a, tag):
    d = np.abs(np.diff(a, axis=1)); s = np.abs(a[:, 0] - a[:, -1]); j = np.abs((a[:, 0] - a[:, -1]) - (a[:, 1] - a[:, 0]))
    jin = np.abs(np.diff(a, 2, axis=1))
    cur = np.abs(np.diff(a, 2, axis=1)); col = np.percentile(cur, 99, axis=0); w = np.percentile(j, 99)
    print('seam %-6s: curvature p99 per column: wrap %.4f | column median %.4f p90 %.4f max %.4f | wrap rank %.1f%% | mean|dH| wrap %.4f vs per-column p90 %.4f' % (tag, w, np.median(col), np.percentile(col, 90), col.max(), 100 * (col < w).mean(), s.mean(), np.percentile(d.mean(0), 90)))
    print('seam %-6s: |dH| across wrap mean %.4f p99 %.4f max %.4f | adjacent cols mean %.4f p99 %.4f max %.4f | curvature at wrap p99 %.4f vs interior p99 %.4f'
          % (tag, s.mean(), np.percentile(s, 99), s.max(), d.mean(), np.percentile(d, 99), d.max(), np.percentile(j, 99), np.percentile(jin, 99)))


def main():
    band = sys.argv[sys.argv.index('--band') + 1] if '--band' in sys.argv else 'band1'; p = BANDS[band]
    a = float_site() if '--float' in sys.argv else load_site()
    seam(a, '8bit' if '--float' not in sys.argv else 'float')
    ms = mips(a); Hh, Ww = a.shape
    Ro = p['ID'] / 2 + p['t']; NT = max(240, math.ceil(TAU * Ro / STEP)); hwid = p['w'] / 2
    Mo = max(24, math.ceil((p['w'] - 2 * RF) / STEP)); zt = (hwid - RF) / hwid
    pxU = (TAU * Ro / REPEATS) / Ww; pxV = p['w'] / Hh
    k = min(len(ms) - 1, max(0, int(math.floor(math.log2(max(TAU * Ro / NT / pxU, (2 * (hwid - RF)) / (Mo - 1) / pxV))))))
    L = ms[k]; print('%s: NT %d Mo %d mip %d (%dx%d) cell u %.4f mm v %.4f mm' % (band, NT, Mo, k, L.shape[1], L.shape[0], TAU * Ro / NT, 2 * zt * hwid / (Mo - 1)))
    i = np.arange(NT); j = np.arange(Mo); zn = (-1 + 2 * j / (Mo - 1)) * zt
    hv = (sample_cubic if '--cubic' in sys.argv else sample)(L, ((i / NT * REPEATS) % 1)[None, :], ((zn / zt + 1) / 2)[:, None] * np.ones((1, NT)))
    zf = np.minimum(1, (hwid - RF - np.abs(zn * hwid)) / FADE); fade = (zf * zf * (3 - 2 * zf))[:, None]
    R = -REL * fade * (1 - hv)
    du, dv = TAU * Ro / NT, 2 * zt * hwid / (Mo - 1)
    gu = (np.roll(R, -1, 1) - np.roll(R, 1, 1)) / (2 * du); gv = np.gradient(R, dv, axis=0)
    ru = gu - gwrap(gu, 2); rv = gv - gwrap(gv, 2); rough = np.hypot(ru, rv)
    ghv = np.hypot((np.roll(hv, -1, 1) - np.roll(hv, 1, 1)) / 2, np.gradient(hv, axis=0))
    rim = ghv > .06; dist = ndi.distance_transform_edt(~rim); ok = np.repeat(fade > .99, NT, 1)  # dist = cells to the nearest rim cell
    zones = [('rim (|grad hv|>.06)', rim), ('gold 3-6 cells off rim', (hv > .6) & (dist > 3) & (dist <= 6) & ok), ('gold 6-10 cells off rim', (hv > .6) & (dist > 6) & (dist <= 10) & ok), ('gold >10 cells off rim', (hv > .6) & (dist > 10) & ok), ('ground >3 cells off rim', (hv < .1) & (dist > 3) & ok)]
    print('region                    cells   rough p50  p90   p99  | u-comp p90 | v-comp p90 | |slope| p50')
    for n, m in zones:
        if m.sum() < 50: print('%-24s %6d   (too few)' % (n, m.sum())); continue
        print('%-24s %6d   %.4f %.4f %.4f | %.4f | %.4f | %.4f' % (n, m.sum(), *np.percentile(rough[m], [50, 90, 99]), np.percentile(np.abs(ru[m]), 90), np.percentile(np.abs(rv[m]), 90), np.percentile(np.hypot(gu, gv)[m], 50)))
    m = zones[4][1] | zones[1][1]; rowe = np.array([np.abs(rv[r][m[r]]).mean() if m[r].sum() > 200 else np.nan for r in range(Mo)]); rowe = rowe[~np.isnan(rowe)]
    f = np.abs(np.fft.rfft(rowe - rowe.mean())); print('row stripes: mean|rv| per mesh row (ground+gold) mean %.4f std %.4f | strongest periodic component %.4f at period %.2f rows' % (rowe.mean(), rowe.std(), 2 * f[1:].max() / len(rowe), len(rowe) / (1 + f[1:].argmax())))
    # facet angle: angle between the normals of adjacent quads (u and v neighbours), on steep quads (slope > .5 mm/mm, step-independent definition of 'wall') and on the rest
    qu = (R[:-1, 1:] + R[1:, 1:] - R[:-1, :-1] - R[1:, :-1]) / (2 * du); qv = (R[1:, :-1] + R[1:, 1:] - R[:-1, :-1] - R[:-1, 1:]) / (2 * dv)
    nn = np.stack([-qu, -qv, np.ones_like(qu)], -1); nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
    au = np.degrees(np.arccos(np.clip((nn[:, :-1] * nn[:, 1:]).sum(-1), -1, 1)))[:-1, :]; av = np.degrees(np.arccos(np.clip((nn[:-1] * nn[1:]).sum(-1), -1, 1)))[:, :-1]
    h = min(au.shape[0], av.shape[0]); w = min(au.shape[1], av.shape[1]); fa = np.maximum(au[:h, :w], av[:h, :w]); sl = np.hypot(qu, qv)[:h, :w]; okq = ok[:h, :w]
    for n, m in (('wall quads (slope>.5)', (sl > .5) & okq), ('other quads', (sl <= .5) & okq)):
        print('facet angle %-22s n %6d  p50 %.1f  p90 %.1f  p99 %.1f deg | share of quads >10 deg: %.3f' % (n, m.sum(), *np.percentile(fa[m], [50, 90, 99]), (fa[m] > 10).mean()))
    print('wall width in cells at CONE .16 (6.25 site px): %.1f' % (6.25 * (TAU * Ro / REPEATS / Ww) / du))
    import cv2 as _c; v = np.zeros((Mo, NT, 3), np.uint8); v[..., 2] = np.clip(np.abs(ru) * 800, 0, 255); v[..., 1] = np.clip(np.abs(rv) * 800, 0, 255); v[rim] //= 3; _c.imwrite('/tmp/meshq_rough_%s.png' % band, _c.resize(v[:, :NT // 3], None, fx=2, fy=2, interpolation=_c.INTER_NEAREST))
    np.save('/tmp/meshq_rough_%s.npy' % band, rough)


if __name__ == '__main__':
    main()
