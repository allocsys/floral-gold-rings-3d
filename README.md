# Floral Gold Rings – 3D

Parametric 3D model of a floral-engraved gold ring set: a wide band, a band and a solitaire. Units are millimetres.

## Status
The two bands use the **Meshy image-to-3D model** of the floral engraving (`site/band_meshy_tile.glb`): one seamless repeat, tiled round the ring and bent into a cylinder by the viewer, with a smooth polished inside and plain gold side edges. The Solitaire is still the parametric model (stone, basket, prongs). No STLs are checked in.

URL switches in the viewer: `?src=old` previous hand-built relief band, `?mr=0` flat metal/roughness instead of Meshy's map, `?bore=0` Meshy's textured inside/edges.

## Layout
| Path | Purpose |
|---|---|
| `site/index.html` | three.js viewer (tabs, sliders, GLB loader + ring bending for the Meshy bands) |
| `site/geometry.js` | Parametric geometry (Solitaire, plaque, old relief bands), browser + Node |
| `site/band_meshy_tile.glb` | The Meshy band tile (31.6 MB, original textures byte-identical) |
| `site/test.mjs` | Smoke test (runs in CI before every Pages deploy) |
| `reference/meshy/model.glb` | The original Meshy output (3-repeat flat strip, 38 MB) |
| `reference/band_face.png` | The image the Meshy model was generated from (Image to 3D, Standard, 4K geometry, glb) |
| `tools/meshy/make_tile.py` | `model.glb` -> `site/band_meshy_tile.glb` (crop one repeat at matched columns, weld ends, rebuild the inside, re-embed original JPEGs). Reproducible: output is byte-identical to the committed tile |
| `tools/live_shot.py` | Headless 3D screenshot of the live viewer (docs in the file header) |
| `tools/export_stl.mjs` | Writes STLs of the parametric rings to `models/` |
| `legacy/` | All pre-Meshy relief-map work, kept but not used (see `legacy/README.md`) |

## Commands
```
python3 tools/meshy/make_tile.py reference/meshy/model.glb site/band_meshy_tile.glb   # needs trimesh shapely scipy numpy pillow
node site/test.mjs                  # smoke test
cd site && python3 -m http.server   # local viewer at http://localhost:8000
```
After changing `geometry.js`, bump the `?v=` on its import in `site/index.html` (browsers cache it).

## Deploy
GitHub Pages: `.github/workflows/pages.yml` tests and deploys `site/` on every push that touches it (Settings → Pages → Source: GitHub Actions).

The meshes are not NURBS; use them as scale/reference geometry and rebuild in Matrix for production.
