# Floral Gold Rings – 3D

Viewer for a floral-engraved gold ring set: a wide band, a band and two solitaires. All four models are Meshy image-to-3D meshes (GLB); the bands are one seamless repeat tiled round the ring and bent in the viewer. Units are millimetres. The meshes are not NURBS: use them as scale/reference geometry and rebuild in Matrix/Rhino for production.

Tabs: Wide band, Band, Solitaire, Solitaire 2. Sliders: inner diameter (all), width + thickness (bands). GLBs load lazily on first visit of the tab.

## Layout
| Path | Purpose |
|---|---|
| `site/index.html` | three.js viewer (tabs, sliders, GLB loaders, band bending, stone/bore materials) |
| `site/geometry.js` | Tab table only: DEFAULTS, LABELS, CONTROLS |
| `site/band_meshy_tile.glb` | Band tile (one repeat of the Meshy strip) |
| `site/solitaire_meshy2.glb` | Solitaire (= `reference/meshy/solitaire_5.glb`) |
| `site/solitaire_6.glb`, `solitaire_6_stone.bin` | Solitaire 2 and its gem-triangle bitmask |
| `site/test.mjs` | Smoke test (CI, before every Pages deploy) |
| `reference/` | Source Meshy outputs and the images they were generated from |
| `tools/meshy/` | `make_tile.py` (strip -> band tile), `make_sym.py`, `make_stone_mask.py` (gem mask) |
| `tools/live_shot.py` | Headless screenshot of the live viewer (usage in the file header) |
| `legacy/` | Pre-Meshy relief-map work, kept but unused (`legacy/README.md`) |

URL switches: `?mr=0` flat metal/roughness on the bands, `?bore=0` textured inside/edges, `?gem=a..e|0` Solitaire 2 gem look.

## Commands
```
python3 tools/meshy/make_tile.py reference/meshy/model.glb site/band_meshy_tile.glb   # needs trimesh shapely scipy numpy pillow
node site/test.mjs                  # smoke test
cd site && python3 -m http.server   # local viewer at http://localhost:8000
```
After changing `geometry.js`, bump the `?v=` on its import in `site/index.html` (browsers cache it).

## Deploy
GitHub Pages: `.github/workflows/pages.yml` tests and deploys `site/` on every push that touches it.

## History
Removed in the clean-up (still in git, last commit with them is `d96176c`): Solitaire 3 (edited clone and parametric version), the parametric relief band (`?src=old`, `relief_band.js`), STL export, ultra-quality / shader normal-map code.
