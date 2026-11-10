"""T5 validation: synthetic 'phone screenshots' from the map (different light than the matcher uses + gold tint, perspective warp, rotation, scale, blur, noise, gamma), red circles at KNOWN map points,
run locate.py, report the error in map px. usage: python3 tools/v2/test_locate.py [N=6]"""
import os, sys, subprocess, json, re, cv2, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import *
N = int(sys.argv[1]) if len(sys.argv) > 1 else 6; d = load(); H = d['H']; rng = np.random.default_rng(7)
gy, gx = np.gradient(H * 40); nn = np.dstack([-gx, -gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
L = np.array([1, -.6, 1.4]); L /= np.linalg.norm(L); a = np.clip(nn @ L, 0, 1); a = (a / a.max()) ** .8
gold = np.dstack([a * .35, a * .72, a * 1.0]); gold = (np.clip(gold, 0, 1) * 255).astype(np.uint8)   # BGR tint
errs = []
for t in range(N):
    x0 = int(rng.integers(0, 500)); w = int(rng.integers(900, 1140)); crop = gold[:, x0:x0 + w]
    ang = rng.uniform(-4, 4); sc = rng.uniform(.5, .8); jit = rng.uniform(-.06, .06, (4, 2)) * np.array([w, TH])
    src = np.float32([[0, 0], [w, 0], [w, TH], [0, TH]]); M0 = cv2.getRotationMatrix2D((w / 2, TH / 2), ang, sc); M0 = np.vstack([M0, [0, 0, 1]])
    dst = (cv2.perspectiveTransform(src[None], M0)[0] + jit + [60, 120]).astype(np.float32); Hm = cv2.getPerspectiveTransform(src, dst)
    W, Hh = 1170, 780; img = cv2.warpPerspective(crop, Hm, (W, Hh), borderValue=(20, 20, 20)); img = cv2.GaussianBlur(img, (0, 0), 1.1)
    img = np.clip(img.astype(np.float32) * rng.uniform(.8, 1.1) + rng.normal(0, 6, img.shape), 0, 255).astype(np.uint8)
    pts = []
    while len(pts) < 3:
        c_ = (int(rng.integers(x0 + 120, x0 + w - 120)), int(rng.integers(80, TH - 80)))
        if all(np.hypot(c_[0] - q[0], c_[1] - q[1]) > 200 for q in pts): pts.append(c_)
    for (mx, my) in pts:
        q = cv2.perspectiveTransform(np.float32([[[mx - x0, my]]]), Hm)[0, 0]; cv2.circle(img, (int(q[0]), int(q[1])), 28, (0, 0, 255), 4)
    cv2.imwrite('/tmp/syn.png', img)
    r = subprocess.run(['python3', 'tools/v2/locate.py', '/tmp/syn.png', '/tmp/syn_out.png'], capture_output=True, text=True, env=dict(os.environ, JSON='/tmp/syn.json'))
    if r.returncode != 0: print('run %d: FAILED  %s' % (t, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:])); continue
    rows = json.load(open('/tmp/syn.json')); got = [(q['x'], q['y']) for q in rows]; e = []
    for (mx, my) in pts:
        dd = [min(abs(gx_ - mx), abs(gx_ - mx + TW), abs(gx_ - mx - TW)) ** 2 + (gy_ - my) ** 2 for gx_, gy_ in got]
        if dd: e.append(np.sqrt(min(dd)))
    errs += e; print('run %d: found %d/3, errors map px: %s  (%s)' % (t, len(rows), ', '.join('%.1f' % v for v in e), ' '.join(l for l in r.stdout.splitlines() if l.startswith('chosen'))))
if errs: print('ALL: n=%d median %.1f px  mean %.1f  max %.1f  (map px; 1 map px ~ 0.5 ref px; bead radius ~45)' % (len(errs), np.median(errs), np.mean(errs), np.max(errs)))
