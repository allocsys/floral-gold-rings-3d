# Band, jeweler export (no stone)

`band_ring_nostone.stl` - binary STL, mm, ring axis Z, one watertight closed solid (genus 1, 1 body).

| | |
|---|---|
| Triangles | 857,848 |
| Volume | 232.756 mm3 |
| Inner / outer diameter | 17.000 / 19.701 mm |
| Width (z) | 4.147 mm (-2.078 .. 2.068) |
| Open / non-manifold edges | 0 / 0 |
| Weight, 18k (15.5 g/cm3) / 24k (19.3 g/cm3) | 3.61 g / 4.49 g |

Made by `tools/ring_export/` (exp_band.py -> repair.py -> repair3.py -> union8.py). 
Files: `band_ring_nostone.stl` / `.obj` / `.glb` (same mesh, 857k tris).

Thickness scan (inward ray, 60k samples, report only, nothing changed): Band: min 0.001, p1 0.27, p5 0.48, median 1.07 mm; 3.0% of surface < 0.4 mm. Thin spots are mid-wall relief features repeating about every 60 deg (per tile), not the bore or outer skin. Jeweler minimum not yet known (0.4 mm used as a placeholder). Viewer: `site/export.html?ring=band`.


Bore rebuilt 2026-11-25 (todo #14/#15/#16, `tools/ring_export/rebore.py`): the old zipper bore strip (396 tris, needles up to aspect 39,600) was replaced by a clean strip of 744 tris with matched rim stations (372 per rim, new stations placed ON the existing flange rim edges, so the flange is unchanged); 18 micro rim edges (0.6-3.2 um, tile-seam steps) collapsed; no zero-area triangles left; bore aspect max 805, min tri area 0.013 mm2. In the GLB the bore has its own rim vertices (hard edge), so shading no longer streaks (rim vertex normals now within 2.1 deg of radial on the bore and 4.3 deg of axial on the flange; before, 46-48 percent of rim vertices pointed the wrong way). STL/OBJ geometry: the bore is a polygon of chords, deepest chord 8 um inside the true radius (inner diameter at the chord midpoints 16.985 mm). Volume +0.027 percent.