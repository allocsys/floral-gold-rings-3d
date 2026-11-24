# Band, jeweler export (no stone)

`band_ring_nostone.stl` - binary STL, mm, ring axis Z, one watertight closed solid (genus 1, 1 body).

| | |
|---|---|
| Triangles | 857,152 |
| Volume | 232.693 mm3 (z-slice check 232.632) |
| Inner / outer diameter | 17.000 / 19.701 mm |
| Width (z) | 4.147 mm (-2.078 .. 2.068) |
| Open / non-manifold edges | 0 / 0 |
| Weight, 18k (15.5 g/cm3) / 24k (19.3 g/cm3) | 3.61 g / 4.49 g |

Made by `tools/ring_export/` (exp_band.py -> repair.py -> repair3.py -> union8.py). 
Files: `band_ring_nostone.stl` / `.obj` / `.glb` (same mesh, 857k tris).

Thickness scan (inward ray, 60k samples, report only, nothing changed): Band: min 0.001, p1 0.27, p5 0.48, median 1.07 mm; 3.0% of surface < 0.4 mm. Thin spots are mid-wall relief features repeating about every 60 deg (per tile), not the bore or outer skin. Jeweler minimum not yet known (0.4 mm used as a placeholder). Viewer: `site/export.html?ring=band`.
