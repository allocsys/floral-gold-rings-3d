# Wide band, jeweler export (no stone)

`wide_band_ring_nostone.stl` - binary STL, mm, ring axis Z, one watertight closed solid (genus 1, 1 body).

| | |
|---|---|
| Triangles | 857,832 |
| Volume | 324.949 mm3 |
| Inner / outer diameter | 19.000 / 22.019 mm |
| Width (z) | 4.634 mm (-2.323 .. 2.312) |
| Open / non-manifold edges | 0 / 0 |
| Weight, 18k (15.5 g/cm3) / 24k (19.3 g/cm3) | 5.04 g / 6.27 g |

Made by `tools/ring_export/` (exp_band.py -> repair.py -> repair3.py -> union8.py). 
Files: `wide_band_ring_nostone.stl` / `.obj` / `.glb` (same mesh, 857k tris).

Thickness scan (inward ray, 60k samples, report only, nothing changed): Wide band: min 0.002, p1 0.30, p5 0.54, median 1.20 mm; 2.2% of surface < 0.4 mm. Thin spots are mid-wall relief features repeating about every 60 deg (per tile), not the bore or outer skin. Jeweler minimum not yet known (0.4 mm used as a placeholder). Viewer: `site/export.html?ring=wide`.


Bore rebuilt 2026-11-25 (todo #14/#15/#16, `tools/ring_export/rebore.py`): the old zipper bore strip (396 tris, needles up to aspect 39,600) was replaced by a clean strip of 744 tris with matched rim stations (372 per rim, new stations placed ON the existing flange rim edges, so the flange is unchanged); 18 micro rim edges (0.6-3.2 um, tile-seam steps) collapsed; no zero-area triangles left; bore aspect max 805, min tri area 0.013 mm2. In the GLB the bore has its own rim vertices (hard edge), so shading no longer streaks (rim vertex normals now within 2.1 deg of radial on the bore and 4.3 deg of axial on the flange; before, 46-48 percent of rim vertices pointed the wrong way). STL/OBJ geometry: the bore is a polygon of chords, deepest chord 8 um inside the true radius (inner diameter at the chord midpoints 18.983 mm). Volume +0.027 percent.