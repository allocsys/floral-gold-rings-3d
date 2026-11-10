"""Grain/pit probe: ref (T2 crop, Lab-L) vs map (H) at the same px grid.
usage: CROPX=7 python3 tools/wip_v3/grain.py [map.png]
Ground: std of (X - gauss(X,s)) over ref-ground eroded, for s=1.5,4 and the share of px with |X-gauss|>thr.
Bead pits: dips (gauss3(X)-X) inside gold eroded 6px; counts per 100k px, ref uses L (scaled 1/255), map uses H."""
import sys, os, cv2, numpy as np
mp = sys.argv[1] if len(sys.argv) > 1 else 'maps/band_period.png'
Z = '/tmp/band_v3_out/'; CROPX, S, PW2 = int(os.environ.get('CROPX', 7)), 2, 2396
T2 = cv2.imread(Z + 'T2.png'); ref = T2[CROPX*S:CROPX*S+520, PW2:2*PW2]
H = (cv2.imread(mp, -1).astype(np.float32) / 65535)[:520]
lab = cv2.cvtColor(cv2.GaussianBlur(ref, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(np.float32)
C = np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]], np.float32)
g = np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2), [1,3]).astype(np.uint8)
g = cv2.morphologyEx(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((3,3),np.uint8)), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
el = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*r+1,)*2)
L = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB)[:,:,0].astype(np.float32) / 255
gr = (cv2.erode((1-g).astype(np.uint8), el(8)) > 0)
au = (cv2.erode(g, el(6)) > 0)
def hp(X, s): return X - cv2.GaussianBlur(X, (0,0), s)
print('region ground %d  gold %d' % (gr.sum(), au.sum()))
for nm, X, gm in (('ref L', L, gr), ('map H', H, gr & (H < .05))):
    print('%-6s ground  std(hp1.5) %.4f  std(hp4) %.4f' % (nm, hp(X,1.5)[gm].std(), hp(X,4)[gm].std()))
for nm, X in (('ref L', L), ('map H', H)):
    d = cv2.GaussianBlur(X, (0,0), 3) - X
    for thr in (.05, .10):
        n = (d[au] > thr).sum(); print('%-6s gold dips>%.2f: %6d px = %.0f / 100k' % (nm, thr, n, 1e5*n/au.sum()))
# unmatched map dips (no ref dip within TOL px) -> components
TOL = 4
dm = (cv2.GaussianBlur(H,(0,0),3) - H > .10) & au
dr = (cv2.GaussianBlur(L,(0,0),3) - L > .05) & au
nr = cv2.dilate(dr.astype(np.uint8), el(TOL)) > 0
ex = dm & ~nr
n, lab_, st, cen = cv2.connectedComponentsWithStats(ex.astype(np.uint8), connectivity=8)
a = st[1:, 4]
print('map dips>.10 %d px; unmatched %d px (%.0f%%); comps %d; area p50/p90/max %s' % (dm.sum(), ex.sum(), 100*ex.sum()/max(dm.sum(),1), n-1, [int(np.percentile(a,q)) for q in (50,90,100)] if n>1 else 0))
big = [i+1 for i in np.argsort(-a)[:8]]
for i in big: print('  comp', i, 'area', st[i,4], 'bbox x%d y%d w%d h%d' % tuple(st[i,:4]), 'Hmed %.2f' % np.median(H[lab_==i]))
vis = cv2.cvtColor((np.clip(H,0,1)*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
vis[ex] = (0,0,255); vis[dr & ~(cv2.dilate(dm.astype(np.uint8), el(TOL))>0)] = (255,128,0)
cv2.imwrite('/tmp/band_v3_out/grain_dbg.png', vis)
