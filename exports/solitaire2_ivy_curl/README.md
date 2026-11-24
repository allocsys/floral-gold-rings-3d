Solitaire 2, Ivy curl pillars (default ?pl=i3), exported from the live scene at 470f817.
Units mm, Y up, ring axis Z, inner diameter 17 mm.
- *_ring.stl / .obj: gold only (541,822 tris). 128 open edges + 3 non-manifold edges, overlapping shells. Wall thickness not checked.
- *_stone.stl / .obj: diamond, separate (110 tris), clean.

## ring_repaired (2026-11-24)
solitaire2_ivy_curl_ring_repaired.stl/.obj: 541,856 tris, 0 open edges, 0 non-manifold, consistent outward faces.
Still 8 separate closed overlapping parts (Meshy body, rim collar, hub sphere, cross bar, 4 ivy tubes); NOT one merged solid yet.
Changes vs ring.stl: welded 1e-4 mm, dropped 93 zero-area/duplicate faces, capped the 8 open tube ends, removed 9 sliver faces at (1.45, 8.80, -1.17) and patched the 2 tiny holes.
Ivy tubes taper from 0.35 mm dia (hub) to 0.10 mm dia (tip): below casting minimum, to be fixed.
scripts/: exp.py (extract from live page, needs headless chromium + three@0.160.0), a1.py (find holes), fix2.py + fix4.py (repair), mk.py (write STL/OBJ).
