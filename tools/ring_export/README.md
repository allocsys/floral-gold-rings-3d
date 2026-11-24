# ring_export (Wide band / Band, jeweler export)

Pipeline, run from a directory holding these scripts. All units mm, ring axis = z.

1. `exp_band.py TAB OUT.json` - headless Chromium opens `site/index.html` (served on :8765, three@0.160.0 served from /tmp/viewer/node_modules, chromium at /tmp/chromium), clicks tab TAB (1 = Wide band, 2 = Band), waits for the Meshy tiles and dumps each tile mesh in world coordinates (base64 float32 positions + uint32 indices).
2. `chk.py OUT.json` - report only: welds at 1e-4 mm and lists degenerate faces, open / non-manifold edges, components, signed volume, per tile and for the merged ring.
3. `repair.py OUT.json stage1.npz` - per tile: weld, drop degenerate faces, drop the separate bore sheet (smallest component); then zipper-stitch the 6 tile seams (greedy shortest diagonal, no vertex moved).
4. `repair3.py stage1.npz stage2.npz` - zips the two remaining rim loops (flange edges at z = +-half width, r = inner radius) into a clean bore strip, then checks open / non-manifold / directed-duplicate edges, signed volume, Euler characteristic. `repair3.py` reads `repair.py` for its helper functions, so keep them in the same directory.
5. `val2.py stage2.npz` - manifold3d validity (status, genus, volume) plus an independent z-slice volume integral.

Results (2026-11-24): both rings are one watertight genus-1 solid, 0 open / 0 non-manifold edges.

| ring | tris | volume | inner / outer diameter | width |
|---|---|---|---|---|
| Wide band | 857,136 | 324.86 mm3 | 19.000 / 22.019 mm | 4.634 mm |
| Band | 857,156 | 232.69 mm3 | 17.000 / 19.701 mm | 4.147 mm |

Known leftovers: 6 (Wide band) / 8 (Band) zero-area sliver triangles from the seam zipper; relief self-intersections not yet checked.
