# Jag report (todo #12, report only)

Scripts measure the flange/bore edge of the exported Wide band / Band STL (welded). Run from a folder with the STL:
`jag2.py STL Ri name out.npz` (rim loop z deviation per angle), `jag3.py out.npz Ri name` (flat flange width per angle), `jag4.py out.npz Ri name out.png` (plan view + rim profile); `jag1.py STL Ri name` = quick check. Ri = 9.5 (Wide band), 8.5 (Band).

Findings (2026-11-25): rim edge height deviation <= 6.6 um (Wide z+), 2.3 um (z-); Band 5.7 / 2.0 um. Same pattern in every 60 deg tile. Rim loops have 168 (z+) and 228 (z-) verts, so the bore strip is an unequal zipper. Flat flange ~1.2 mm (Wide) / 1.1 mm (Band) wide, coarse triangulation. The edge is geometrically straight; the visible zigzag is most likely shading. PNGs: wide_rim.png, band_rim.png (matplotlib, not shaded renders).
