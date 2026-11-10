#!/usr/bin/env python3
"""Side-by-side metrics for two maps (A = baseline, B = candidate) with deltas and regression flags.

  python3 tools/wip_v3/compare.py [A.png] [B.png]
    A default = maps/band_period.png (committed)      B default = $BAND_OUT/chain_final.png
  python3 tools/wip_v3/compare.py --one MAP.png       # metrics of one map only

Runs diff/idiff/tdiff/cdiff on each map (same environment, so library drift cancels out) and parses their output.
Env: BAND_OUT (default /tmp/band_v3_out, needs T2.png from stage1), CROPX (default 7).
Flag '<<' = B worse than A by more than the tolerance in TOL. Exit code 1 if any flag.
"""
import os, re, subprocess, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.environ.get('BAND_OUT', '/tmp/band_v3_out')
ENV = dict(os.environ, CROPX=os.environ.get('CROPX', '7'))

# key: (script, regex, higher_is_better, tolerance)  tolerance=None -> informational only
M = {
 'IoU':             ('diff',  r'IoU ([\d.]+)', 1, .002),
 'MISS px':         ('diff',  r'MISS (\d+)', 0, None),
 'EXTRA px':        ('diff',  r'EXTRA (\d+)', 0, None),
 'line recall':     ('idiff', r'line recall ([\d.]+)', 1, .005),
 'groove prec':     ('idiff', r'groove precision ([\d.]+)', 1, .005),
 'ridge recall':    ('tdiff', r'ridge recall ([\d.]+)', 1, .005),
 'ridge prec':      ('tdiff', r'ridge precision ([\d.]+)', 1, .005),
 'EXTRAR px':       ('tdiff', r'EXTRAR (\d+)', 0, None),
 'plateau >.95':    ('tdiff', r'plateau frac \(gold H>\.95\): ([\d.]+)', 0, .01),
 'gold H median':   ('tdiff', r'gold H median ([\d.]+)', 1, None),
 'clipped':         ('tdiff', r'clipped frac \(gold H>=\.995\): ([\d.]+)', 0, .005),
 'lowfreq corr':    ('tdiff', r'lowfreq corr\(H,L\) sigma8 in region: ([\d.]+)', 1, .01),
 'ground rough':    ('tdiff', r'ground roughness \(std of H - gauss4\): ([\d.]+)', 0, .002),
 'slope corr':      ('cdiff', r'slope corr\(L,-\|gradH\|\) ([\d.]+)', 1, .01),
 'corr(L,H)':       ('cdiff', r'corr\(L,H\) ([\d.]+)', 1, .01),
 'R2(L~H,|g|)':     ('cdiff', r'R2\(L ~ H, \|gradH\|\) ([\d.]+)', 1, .01),
 'narrow RMSE':     ('cdiff', r'halfwidth 24-40 px[^\n]*?RMSE ([\d.]+)', 0, .01),
 'narrow lead':     ('cdiff', r'halfwidth 24-40 px[^\n]*?lead ([+-][\d.]+)', None, None),
 'wide RMSE':       ('cdiff', r'halfwidth 40-70 px[^\n]*?RMSE ([\d.]+)', 0, .01),
 'slit rag (map)': ('rdiff', r'map\s+slits\s+\d+ \| area\s+\d+ \| rag mean [\d.]+ \(area-wtd ([\d.]+)\)', 0, .02),
 'slit rim err px': ('rdiff', r'on ref slit rim ([\d.]+) px', 0, .3),
 'wide lead':       ('cdiff', r'halfwidth 40-70 px[^\n]*?lead ([+-][\d.]+)', None, None),
}

def measure(path):
    txt = {}
    for t in ('diff', 'idiff', 'tdiff', 'cdiff', 'rdiff'):
        r = subprocess.run([sys.executable, f'tools/wip_v3/{t}.py', path, OUT], cwd=REPO, env=ENV,
                           capture_output=True, text=True)
        txt[t] = r.stdout + r.stderr
    res = {}
    for k, (t, rx, *_ ) in M.items():
        m = re.search(rx, txt[t])
        res[k] = float(m.group(1)) if m else None
    return res

def fmt(v):
    if v is None: return '   n/a'
    return f'{v:8.0f}' if abs(v) >= 100 else f'{v:8.3f}'

def main():
    a = sys.argv[1:]
    if not os.path.exists(os.path.join(OUT, 'T2.png')):
        sys.exit(f'missing {OUT}/T2.png - run tools/wip_v3/chain.sh (or setup.sh) first')
    if a and a[0] == '--one':
        r = measure(a[1])
        for k, v in r.items(): print(f'{k:15s}{fmt(v)}')
        return 0
    A = a[0] if len(a) > 0 else os.path.join(REPO, 'maps', 'band_period.png')
    B = a[1] if len(a) > 1 else os.path.join(OUT, 'chain_final.png')
    ra, rb = measure(A), measure(B)
    print(f'A = {A}\nB = {B}\n{"metric":15s}{"A":>8s}{"B":>9s}{"delta":>9s}')
    bad = 0
    for k, (t, rx, hib, tol) in M.items():
        va, vb = ra[k], rb[k]
        if va is None or vb is None:
            print(f'{k:15s}{fmt(va)} {fmt(vb)}   (parse failed)'); continue
        d = vb - va
        flag = ''
        if hib is not None and tol is not None:
            worse = -d if hib else d
            if worse > tol: flag, bad = '  <<', bad + 1
        print(f'{k:15s}{fmt(va)} {fmt(vb)} {d:+9.3f}{flag}')
    print(f'\n{bad} regression flag(s)' if bad else '\nno regressions beyond tolerance')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
