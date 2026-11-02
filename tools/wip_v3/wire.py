#!/usr/bin/env python3
"""Wire a finished band map into the site.

  python3 tools/wip_v3/wire.py --check            # verify the committed b64 in site/relief_band.js == maps/band_period.png
  python3 tools/wip_v3/wire.py MAP.png            # copy MAP -> maps/band_period.png, regenerate b64, bump ?v=reliefN, run site test
  python3 tools/wip_v3/wire.py MAP.png --no-test  # same, skip `node site/test.mjs`

b64 recipe: H/65535 -> cv2.resize to (1198,260) INTER_AREA -> *255 rounded -> raw uint8 row-major -> base64.
Nothing is committed or pushed here; do that afterwards (see tools/wip_v3/push.sh).
"""
import base64, os, re, shutil, subprocess, sys
import cv2, numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAPDST = os.path.join(REPO, 'maps', 'band_period.png')
JS = os.path.join(REPO, 'site', 'relief_band.js')
HTML = os.path.join(REPO, 'site', 'index.html')
B64_RE = re.compile(r"b64:\s*'[^']*'")


def b64_of(png):
    H = cv2.imread(png, -1)
    assert H is not None and H.dtype == np.uint16 and H.shape == (520, 2396), f'{png}: expected 16-bit 520x2396, got {None if H is None else (H.dtype, H.shape)}'
    s = cv2.resize(H.astype(np.float32) / 65535, (1198, 260), interpolation=cv2.INTER_AREA)
    if os.environ.get('MESH') != '0':  # D25 default ON: slope-limited mesh-side map (meshmap.py; CONE env = slope cap per site px; MESH=0 = plain downsample); maps/band_period.png stays ref-truth
        sys.path.insert(0, os.path.dirname(__file__)); import meshmap; s = meshmap.widen(s)
    return base64.b64encode(np.round(s * 255).astype(np.uint8).tobytes()).decode()


def current_b64():
    m = B64_RE.findall(open(JS).read())
    assert len(m) == 1, f'expected exactly 1 b64 entry in relief_band.js, found {len(m)}'
    return m[0].split("'")[1]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = {a for a in sys.argv[1:] if a.startswith('--')}
    if '--check' in flags:
        new, old = b64_of(MAPDST), current_b64()
        if new == old:
            print('OK: relief_band.js b64 matches maps/band_period.png'); return 0
        a, b = np.frombuffer(base64.b64decode(new), np.uint8), np.frombuffer(base64.b64decode(old), np.uint8)
        print(f'MISMATCH: {int((a != b).sum())} of {a.size} bytes differ (max abs {int(np.abs(a.astype(int) - b).max())})'); return 1
    if len(args) != 1:
        print(__doc__); return 2
    src = os.path.abspath(args[0])
    new = b64_of(src)                                  # validate before touching anything
    if src != MAPDST:
        shutil.copyfile(src, MAPDST)
    js = open(JS).read()
    open(JS, 'w').write(B64_RE.sub(lambda _m: "b64: '" + new + "'", js, count=1))
    html = open(HTML).read()
    ver = re.findall(r'\?v=relief(\d+)', html)
    assert ver, 'no ?v=reliefN in site/index.html'
    nxt = max(map(int, ver)) + 1
    open(HTML, 'w').write(re.sub(r'\?v=relief\d+', f'?v=relief{nxt}', html))
    print(f'wired {src} -> maps/band_period.png, relief_band.js b64 updated, ?v=relief{nxt}')
    if '--no-test' not in flags:
        r = subprocess.run(['node', 'site/test.mjs'], cwd=REPO, capture_output=True, text=True)
        print(r.stdout.strip()[-600:], r.stderr.strip()[-300:])
        return r.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
