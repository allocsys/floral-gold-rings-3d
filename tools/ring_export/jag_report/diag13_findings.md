# Todo #13 - diagnosis of the 'jagged' inner edge (Wide band / Band)

Run: `python3 diag13.py <ring.stl> <Ri> <name>` and `python3 diag13b.py <ring.stl> <ring.glb> <Ri> <name>`
(Wide band Ri 9.5, Band Ri 8.5). Needs trimesh + numpy.

## Result: the edge geometry is clean; the zigzag is SHADING from smooth vertex normals

- Bore strip = 396 tris per ring, edge length up to 4.7 mm (Wide) / 4.2 mm (Band), spans the whole band width.
  72 tris have aspect (Lmax^2/2A) > 50, max ~39,600 (needle triangles). Face normals themselves are fine
  (deviation from radial: median 0.17 deg, max 0.91 deg).
- Flange faces: ~1000 tris per side, 36-76 zero-area slivers (< 1e-4 mm2) per side, aspect > 50 on 36-74 tris per side.
- The bore/flange corner is a hard 90 deg edge but the vertices are SHARED, and the GLB has POSITION only
  (no NORMAL), so export.html calls computeVertexNormals (area weighted). At each rim vertex the normal is then
  dominated by whichever neighbour is larger: long bore triangle -> radial, big flange triangle -> axial.
  Rim vertices whose normal is > 45 deg off radial: 46-48 percent. The normal flips radial <-> axial 514 (z+) /
  649 (z-) times around the ring = every 0.55-0.70 deg. That is the zigzag seen on the phone (interpolated across
  the needle bore triangles). Identical for both rings (same tile).
- Not the cause: rim height wobble (<= 7 um, todo #12), seams (3 um step).

## Implication for fix (#14)
Geometry fix options: (a) split the rim: duplicate the rim vertices so bore and flange do not share them (hard edge,
no geometry change, zero mm3 change, STL unaffected) - cures the shading only; (b) also regenerate the bore as a
clean quad strip with matched rim vertex counts (no needle triangles); (c) re-triangulate the flange face.
Nothing changed yet.
