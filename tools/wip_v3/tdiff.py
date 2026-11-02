"""Topography diff: raised ribs/veins/highlights in the ref gold vs ridges in the map, + map-only flatness stats, clipped fraction, ridge recall on plateau, lowfreq H-L corr.
usage: CROPX=7 python3 tools/wip_v3/tdiff.py [map.png] [outdir]   (needs T2.png in outdir, default /tmp/band_v3_out)
Region = ref gold mask (as diff.py) eroded RIM px. Ref ridges = white-tophat of Lab-L (kernel K) > TB (bright thin features).
Map ridges = white-tophat of H (kernel K) > TR. Tolerance TOL px. Writes tdiff_<map>.png:
green = both, red = ref ridge missing in map (MISSR), blue = map ridge the ref doesn't have (EXTRAR).
Map-only stats: plateau fraction (gold H > .95), ground roughness (std of H - gauss(H,4) where H < .05, region = ref ground eroded)."""
import sys, os, cv2, numpy as np
mp = sys.argv[1] if len(sys.argv) > 1 else 'maps/band_period.png'
Z = (sys.argv[2] if len(sys.argv) > 2 else '/tmp/band_v3_out').rstrip('/') + '/'
CROPX, S, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
RIM, K, TB, TR, TOL = 8, 15, 10, 0.03, 4
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H = (cv2.imread(mp, -1).astype(np.float32) / 65535)[:520]
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]], np.float32)
g = np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2), [1,3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3,3),np.uint8)), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
el = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1,)*2)
reg = cv2.erode(g, el(RIM)) > 0
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (K, K))
L = cv2.cvtColor(cv2.GaussianBlur(ref, (0,0), 1.0), cv2.COLOR_BGR2LAB)[:,:,0].astype(np.float32)
rl = (cv2.morphologyEx(L, cv2.MORPH_TOPHAT, k) > TB) & reg
Hs = cv2.GaussianBlur(H, (0,0), 1.0)
rh = (cv2.morphologyEx(Hs, cv2.MORPH_TOPHAT, k) > TR) & reg
t = el(TOL)
near_h = cv2.dilate(rh.astype(np.uint8), t) > 0; near_l = cv2.dilate(rl.astype(np.uint8), t) > 0
bl = rl & near_h; bh = rh & near_l
rec = bl.sum() / max(rl.sum(), 1); pre = bh.sum() / max(rh.sum(), 1)
print('region %d px | ref ridge px %d (%.1f%%) | map ridge px %d (%.1f%%)' % (reg.sum(), rl.sum(), 100*rl.sum()/reg.sum(), rh.sum(), 100*rh.sum()/reg.sum()))
print('ridge recall %.3f | ridge precision %.3f | MISSR %d EXTRAR %d' % (rec, pre, (rl & ~near_h).sum(), (rh & ~near_l).sum()))
gold = H > 0.05
print('plateau frac (gold H>.95): %.3f | gold H median %.3f' % ((H[gold] > .95).mean(), np.median(H[gold])))
cl=(H[gold]>=.995).mean(); print('clipped frac (gold H>=.995): %.3f' % cl)
pr=rl&(Hs>.9); print('ridge recall on plateau (map H>.9): %.3f over %d ref ridge px' % ((pr & near_h).sum()/max(pr.sum(),1), pr.sum()))
Lg=cv2.GaussianBlur(L,(0,0),8); Hg=cv2.GaussianBlur(H,(0,0),8); mi=reg
print('lowfreq corr(H,L) sigma8 in region: %.3f' % np.corrcoef(Hg[mi], Lg[mi])[0,1])
gr = cv2.erode((1 - g).astype(np.uint8), el(RIM)) > 0
gr &= H < 0.05
print('ground roughness (std of H - gauss4): %.4f over %d px' % ((H - cv2.GaussianBlur(H, (0,0), 4))[gr].std(), gr.sum()))
vis = (ref * 0.35).astype(np.uint8); vis[~reg] = (vis[~reg] * 0.5).astype(np.uint8)
vis[bl | bh] = (0, 200, 0); vis[rl & ~near_h] = (0, 0, 255); vis[rh & ~near_l] = (255, 120, 0)
out = Z + 'tdiff_' + os.path.splitext(os.path.basename(mp))[0] + '.png'
cv2.imwrite(out, cv2.resize(vis, (1198, 260), interpolation=cv2.INTER_AREA)); print('wrote', out)
