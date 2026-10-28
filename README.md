# Floral Gold Rings – 3D Models

Parametric STL models of a floral-engraved gold ring set: two bands and a solitaire engagement ring.

| File | Description |
|---|---|
| `models/ring_1_wide_band.stl` | 19 mm inner diameter, 4.5 mm wide, comfort-fit |
| `models/ring_2_band.stl` | 17 mm inner diameter, 4 mm wide |
| `models/ring_3_solitaire.stl` | 17 mm inner diameter, 5.2 mm round stone, basket + 6 prongs, engraving on shoulders |

Units are millimetres. Open in MatrixGold/Rhino (import STL), Blender, or any slicer.

## Notes
- The floral vine/flower engraving is a simplified approximation, not a faithful reproduction of the reference photo.
- These are meshes, not NURBS. Use them as scale/reference geometry and rebuild in Matrix for production.

## Regenerate
```
pip install numpy
python generate_rings.py
```
