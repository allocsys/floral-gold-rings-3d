# Floral Gold Rings – 3D

Parametric 3D model of a floral-engraved gold ring set: a wide band, a band and a solitaire. Units are millimetres.

## Status
The bands are **plain polished** for now; the engraving is being rebuilt from `reference/rings_flat.png`. The solitaire stone, basket and prongs are complete. No STLs are checked in; generate them when needed (below).

Next: build rounded height maps from `reference/*.png`, wrap them around each band, and feed them into `band()` in `site/geometry.js`.

## Layout
| Path | Purpose |
|---|---|
| `site/geometry.js` | Single source of truth for all geometry (browser + Node, no dependencies) |
| `site/index.html` | three.js viewer: pick a ring, adjust sliders, orbit, Download STL |
| `site/test.mjs` | Smoke test (finite coordinates, positive volume, STL size) |
| `tools/export_stl.mjs` | Writes full-detail STLs to `models/` |
| `reference/` | `rings_flat.png`: straight-on view of the three rings (wide band, band, solitaire) |

## Commands
```
node site/test.mjs          # smoke test
node tools/export_stl.mjs   # writes models/*.stl
cd site && python3 -m http.server   # local viewer at http://localhost:8000
```
After changing `geometry.js`, bump the `?v=` on its import in `site/index.html` (browsers cache it).

## Deploy
GitHub Pages: `.github/workflows/pages.yml` tests and deploys `site/` on every push that touches it (Settings → Pages → Source: GitHub Actions).

The meshes are not NURBS; use them as scale/reference geometry and rebuild in Matrix for production.
