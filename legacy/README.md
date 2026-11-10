# legacy/ - the pre-Meshy relief-map work (kept, not used)

Everything here built the hand-made band relief (`maps/band_period.png` -> `site/relief_band.js`). The viewer's band tabs now use the Meshy model (`site/band_meshy_tile.glb`), so none of this is on the live path. It is kept in case some piece turns out useful.

| Path | What it was |
|---|---|
| `tools/vec/` | The last relief pipeline (potrace outline -> daisies -> berries -> zonal -> centre_fill -> veins -> notches -> petalsmooth -> endfix -> ground_dots). Docs: `tools/vec/SCRIPTS.md` |
| `tools/wip_v3/` | The older raster chain (stages 1-64, `archive/` = retired stages), metric probes (`diff/idiff/tdiff/cdiff/rdiff/jag/sharp/grain/meshq/compare`), `wire.py` (map -> `site/relief_band.js`), `chain.sh`, `sol1-4.py` (Solitaire). Docs: `README.md`, `SCRIPTS.md` |
| `tools/v2/`, `tools/band_heightmap.py` | Even older map generators |
| `maps/` | Height maps and previews (`band_period.png` = last committed relief map, `band_raster_src.png` = input of the vec pipeline) |

Still live in `site/`: `relief_band.js` (used by `?src=old`).

`relief_sol.js` = the relief map of the old parametric solitaire (moved here when the Solitaire tab was replaced by the Meshy model `site/solitaire_meshy.glb`). The old parametric solitaire code (stone, prongs, basket) was removed from `site/geometry.js`; the last commit that has it is `3597c30`.

## Running it again
The scripts use repo-root-relative paths (`tools/wip_v3/...`, `maps/...`), which changed when they moved here. To run them exactly as they were:
```
git checkout pre-meshy-cleanup      # tag = repo state right before this folder move (d9d61d0)
```
(or copy `legacy/tools/*` to `tools/` and `legacy/maps` to `maps/` in a scratch checkout).

## Possibly reusable ideas
- `wip_v3/compare.py` + metric probes: map-vs-reference regression metrics (IoU, groove recall, ridge recall, rim raggedness).
- `wip_v3/meshq.py`: mesh-side normal roughness / facet-angle probe for any heightfield mesh.
- `vec/veins.py`, `notches.py`, `petalsmooth.py`: local relief clean-up steps on a 16-bit height map.
