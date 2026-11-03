# Reusable scripts (tools/wip_v3)

All take `BAND_OUT` (work dir, default `/tmp/band_v3_out`) and `CROPX` (default 7). Run from anywhere; they locate the repo themselves.
Invoke with `bash script.sh` / `python3 script.py` (no exec bit). `bash_tool` is /bin/sh, so always use `bash`.

## Fresh sandbox (3 commands)
```
git clone https://github.com/allocsys/floral-gold-rings-3d.git && cd floral-gold-rings-3d
bash tools/wip_v3/setup.sh               # deps, git identity, starts chain.sh in background
bash tools/wip_v3/chain.sh status        # repeat until "not running" (~4 min for stages 1..51 + late chain)
```

| script | what it does |
|---|---|
| `setup.sh` | Installs missing libs, sets git identity, starts the full build detached. `NOBUILD=1` skips the build. |
| `chain.sh` | Rebuilds the current map (v59): stage1,2,49,50,51 -> 54 -> 56 -> 55 (RIB=0 KNEE=.70 COMP=.6) -> 52 -> 55 (RIB=.22 COMP=1) -> 57 (terrace fix) -> 58 (ghost bumps) -> `$BAND_OUT/chain_final.png`. `LATE=1` reruns only the late chain (seconds). `BG=1` runs detached (a plain `&` is killed when the tool call ends); `chain.sh status` shows log tail + running state. Stage params in the env (`ALPHA=1.5 bash chain.sh`) are passed through. |
| `compare.py [A] [B]` | **Main check.** Metrics of A (default committed `maps/band_period.png`) vs B (default `chain_final.png`) side by side with deltas and `<<` regression flags (exit 1 if any). Library drift cancels because both maps are measured in the same sandbox. `--one MAP` for a single map. |
| `measure.sh [map]` | Raw output of diff/idiff/tdiff/cdiff for one map (needs `$BAND_OUT/T2.png` from stage1). |
| `wire.py MAP.png` | Copies MAP to `maps/band_period.png`, regenerates the b64 in `site/relief_band.js`, bumps `?v=reliefN`, runs `node site/test.mjs`. `--check` verifies b64 == map; `--no-test` skips node. Does not commit. |
| `commit.sh "msg"` | `git add -A` + commit with identity and the Co-Authored-By / Claude-Session trailers (`CLAUDE_SESSION` env overrides the URL). |
| `push.sh` | `GH_TOKEN=... bash tools/wip_v3/push.sh`: pushes HEAD to origin/main directly (token masked), verifies HEAD == origin/main, warns on uncommitted changes. Token: `tool_search 'gh_token mint github token'` then `mcp__Madmcp__gh_token(repo=floral-gold-rings-3d)`. |

## Typical loop
```
LATE=1 bash tools/wip_v3/chain.sh && python3 tools/wip_v3/compare.py     # edit a late stage (54/56/55/52) first
python3 tools/wip_v3/wire.py $BAND_OUT/chain_final.png                  # only if no regressions
bash tools/wip_v3/commit.sh "D21: ..." && GH_TOKEN=... bash tools/wip_v3/push.sh
```

## Notes
- The stages hardcode `/tmp/band_v3_out` and `exec()` each other via `tools/wip_v3/stageN.py`, so `chain.sh` runs from a shadow root at `$BAND_OUT/_root` (symlinks + sed-patched copy of `tools/wip_v3`); repo files are never modified.
- Reproducibility: rebuild is byte-identical to the committed v58 on cv2 4.13.0 / numpy 2.4.4 (verified 2026-11-02); on cv2 5.0.0 / numpy 2.5.3 it is not, but metrics are within noise. Always use `compare.py` (same-environment baseline), never numbers recorded in older notes.
- Metric scripts: `diff.py` IoU/silhouette, `idiff.py` groove recall/precision, `tdiff.py` ridge + plateau/clipping, `cdiff.py` cushion slope + crown profile, `rdiff.py` slit-rim raggedness (silhouette; 'rag' 1.00 = smooth). `err.py` is INVALID, do not use.

## D24 additions
- `sharp.py [map] [outdir]`: sharp-edge probe (rim profile vs ref L, |grad|/|lap| percentiles, interior hotspots, `sharp_vis_a/b.png`). Not in compare.py yet.
- `live_shot.py OUT.png TAB`: real 3D screenshot of the site (needs `python3 -m http.server 8765` in `site/` and `npm i three@0.160.0` in /tmp/viewer). Now injects `__ctl/__cam` itself; `DSF=2 CLIP=x,y,w,h` for zoomed crops.
- Findings (v59): rim walls are the sharp edges. Site map 1198x260, relief .4 mm, mesh .04 mm: median wall .086 mm = 2.1 cells, 47% of rim px <2 cells, median angle 73 deg / p99 84 -> staircase hatching. Ghost bumps: 1.7% of ground px H>.05 (12 patches >30px at H>.2). Solitaire has no relief.

## D25 additions (v60)
- `stage58.py`: removes ghost bumps (relief on pixels >6 px from the ref gold mask, H in (.03,.3]); chain now ends ... -> 57 -> 58 = chain_final. Effect (vs its own input c57): only ground rough .011 -> .008, everything else identical. 17110 px, 1061 patches.
- `meshmap.py [map]`: mesh-side (site) map = 2x INTER_AREA downsample + Lipschitz cone slope cap (CONE=.16 per site px, (L+U)/2 keeps the .5 contour). `wire.py` applies it by default (MESH=0 = plain downsample); `maps/band_period.png` stays ref-truth. Rim-band |grad| p99 .456 -> .166, p90 .295 -> .157; cost: IoU(H>.5) vs plain site map .947 (thin lines lose amplitude), mean|dH| .024. CONE=.2: IoU .969 / p99 .207; CONE=.25: .984 / .255. Wall-blur variant (CONE=0, SIG/DIL) rejected: IoU .88-.91.
- Visual check (live_shot, band tab, DSF=2): slope-capped map shows less rim hatching/crumpling than the plain map.
- Library drift note: in this sandbox (cv2 5.0/numpy 2.5/scipy 1.18) stage57 finds 4 terraces (committed build: 2), so compare.py A-vs-B mixes drift; isolate a stage by comparing its input c57.png vs chain_final.png.

## D26 additions
- `meshq.py [--band band1|band2] [--float] [--cubic]`: mesh-side probe. Replicates `site/geometry.js` sampling (mip choice, bilinear, periodic u, real vertex grid, edge fade) and prints (1) seam test: wrap curvature p99 vs every other column, (2) normal roughness |slope - gauss(slope, 2 cells)| by zone (rim, gold 3-6 / 6-10 cells off rim, ground) split into u/v components, (3) per-row stripe periodicity; writes `/tmp/meshq_rough_BAND.png` (red = u, green = v). `--float` = un-quantised map, `--cubic` = cubic B-spline sampler.
- Findings (v60, band1, cell .040 mm, mip 1): 8-bit quantisation and bilinear kinks are NOT causes (float / cubic give equal or higher roughness). Seam is mild (wrap curvature .284 vs worst other column .2745). A/B render with `geometry.js` step .02 (scratch copy of site, same camera): sawtooth comb teeth on slits and zigzag bead outlines vanish -> hatching is mesh-resolution-limited (walls ~3 cells, median wall slope 1.6 mm/mm). The finer mesh also exposes map-side ground grain and bead pits (ground |grad| p99 .0345 per px). Not yet checked against the reference.

## D27 additions (mesh: ultra quality)
- `meshq.py` now takes `STEP=.03` (mesh step in mm, default .04) and prints facet angle (angle between neighbouring quad normals) on wall quads (slope > .5 mm/mm) and other quads, plus wall width in cells.
- Facet angle, band1, v60 map: step .04 -> wall p50 24.5 / p90 69.5 deg, share >10 deg .83 (wall 3.0 cells); .03 -> 21.1 / 69.0 / .76 (4.0 cells, barely better); .02 -> 13.9 / 50.8 / .62 (6.0 cells). Float vs 8-bit map identical at every step (quantisation is not a factor). Tris band1: .04 515k, .03 834k, .02 1.69M (band2 423k / 680k / 1.37M); build 110 ms at .02; volume within .005% of fine; STL .04 25.7 MB / .02 84.7 MB.
- Cost of .02: it uses the full-res map (mip 0) and exposes map grain: ground rough p50 .051 -> .071 (+38%), pits on beads. That is a map-side defect to fix next (compare against reference/band_face.png first).
- Site: `geometry.js` quality `ultra` (relief bands only, `ULTRA_STEP` = .02); `index.html` queues `ultra` 700 ms after a `fine` build of a relief band (new input cancels the timer; Solitaire never rebuilds). STL export is still `fine` (84 MB at .02 is too big to be the default). `test.mjs` checks ultra is >3x finer with volume within .3% of fine. Live check: real site crop == scratch .02 render (mean abs diff 0.00), vs .04 14.41. `?v=relief38`.
- GOTCHA (caught by live_shot, `pageerror Unexpected end of input`): never put a `//` comment on the same line as code in index.html's one-line animation loop; it swallowed `});`.
