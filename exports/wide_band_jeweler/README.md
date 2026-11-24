# Wide band, jeweler export (no stone)

`wide_band_ring_nostone.stl` - binary STL, mm, ring axis Z, one watertight closed solid (genus 1, 1 body).

| | |
|---|---|
| Triangles | 857,136 |
| Volume | 324.861 mm3 (z-slice check 324.776) |
| Inner / outer diameter | 19.000 / 22.019 mm |
| Width (z) | 4.634 mm (-2.323 .. 2.312) |
| Open / non-manifold edges | 0 / 0 |
| Weight, 18k (15.5 g/cm3) / 24k (19.3 g/cm3) | 5.04 g / 6.27 g |

Made by `tools/ring_export/` (exp_band.py -> repair.py -> repair3.py -> union8.py). 
Files: `wide_band_ring_nostone.stl` / `.obj` / `.glb` (same mesh, 857k tris).

Thickness scan (inward ray, 60k samples, report only, nothing changed): Wide band: min 0.002, p1 0.30, p5 0.54, median 1.20 mm; 2.2% of surface < 0.4 mm. Thin spots are mid-wall relief features repeating about every 60 deg (per tile), not the bore or outer skin. Jeweler minimum not yet known (0.4 mm used as a placeholder). Viewer: `site/export.html?ring=wide`.
