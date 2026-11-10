# sol4 (D47, B3): one-shot post-process of site/relief_sol.js (1614 = 3 repeats). The ref strip is 538x134 px (4.0:1) but 3 repeats over the half circle give mm/px_u .0191 vs mm/px_v .0221 = aspect .86 (features 13% narrow along the ring). Need 2.6 repeats: cut the last repeat at the flower-centre bead (A col 389, row 57; mirror-symmetric axis, err min) so the bottom mirror axis runs through that flower. Result 538|538|390 = 1466 cols -> aspect .95. (sol1-3 are NOT bit-reproducible in a fresh sandbox: library drift, mean |d| 13/255, so this works on the committed map.)
import re,base64,numpy as np,os
s=open('site/relief_sol.js').read(); m=re.search(r"W: (\d+), H: (\d+), b64: '([^']+)'",s); W,H=int(m.group(1)),int(m.group(2))
if W!=1614: raise SystemExit('expected the 3-repeat map (W=1614), got %d'%W)
u=np.frombuffer(base64.b64decode(m.group(3)),np.uint8).reshape(H,W); CUT=int(os.environ.get('CUT',389))
n=np.ascontiguousarray(np.hstack([u[:,:1076],u[:,1076:1076+CUT+1]])); Hh,Wn=n.shape
open('site/relief_sol.js','w').write(s.split('export')[0]+"export const RELIEF_SOL = { W: %d, H: %d, b64: '%s' };\n"%(Wn,Hh,base64.b64encode(n.tobytes()).decode()))
print('map',n.shape)
