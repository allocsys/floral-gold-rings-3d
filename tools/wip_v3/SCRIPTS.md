# Reusable scripts (tools/wip_v3)

All take `BAND_OUT` (work dir, default `/tmp/band_v3_out`) and `CROPX` (default 7). Run from anywhere; they locate the repo themselves.
Invoke with `bash script.sh` / `python3 script.py` (no exec bit). `bash_tool` is /bin/sh, so always use `bash`.

## LIVE MAP = VECTOR BUILD (tools/vec, since V3/relief63; current V8/relief68)
`maps/band_period.png` is built by `tools/vec/build_map.py`, NOT by chain.sh. INPUT = `maps/band_raster_src.png` (the old raster map from the chain below, kept in repo); the live chain no longer needs stages 1-64 to be rerun.
```
pip install potracer --break-system-packages          # per sandbox
python3 tools/vec/build_map.py                        # -> /tmp/vec/band_vec.png (~20 s, 16-bit 520x2396, periodic)
python3 tools/wip_v3/wire.py /tmp/vec/band_vec.png    # writes map + site/relief_band.js b64 (MESH off); then bump ?v in index.html AND geometry.js relief_band import
```
Method: potrace outline of ref mask (SM1.6, UP4) -> corner-protected outline smoothing (OSM 3) -> sub-pixel SDF bevel (W10, SDFS 1.6) -> per-shape interior denoise (median5, LP1, ER3) -> despeckle (DSP 120) -> bead refit (BEAD=1: ellipse + parabolic cap). Env knobs: W SM OPTT ER OSM OCORN TAU LOWS DESPECKLE BEAD. Default build == committed map (bit-identical in the s46-47 sandbox).
Other files: `wobble.py` (outline inflection/corner metric), `pilot_outline.py` + `pilot_interior.py` (window pilots, history only).
Revert to the raster map: `git checkout b00d366 -- maps/band_period.png site/relief_band.js` (+ bump ?v).

## Fresh sandbox (3 commands) - LEGACY RASTER CHAIN (stages 1-64, produces band_raster_src.png equivalent)
```
git clone https://github.com/allocsys/floral-gold-rings-3d.git && cd floral-gold-rings-3d
BUILD=1 bash tools/wip_v3/setup.sh        # deps + git identity; BUILD=1 also starts chain.sh in background (only needed for T2.png / compare.py / measure.sh; the vector map does not need it)
bash tools/wip_v3/chain.sh status        # repeat until "not running" (~4 min for stages 1..51 + late chain)
```

| script | what it does |
|---|---|
| `setup.sh` | Installs missing libs, sets git identity. `BUILD=1` also starts the legacy raster chain detached (default: no build). |
| `chain.sh` | Rebuilds the current map (v66): stage1,2,49,50,51 -> 54 -> 56 -> 55 (RIB=0 KNEE=.70 COMP=.6) -> 52 -> 55 (RIB=.22 COMP=1) -> 57 (terrace fix) -> 58 (ghost bumps) -> 59 (bead fill) -> 60 (iso-line smoothing) -> 61 (bead bites) -> 62 -> 63 (pearls) -> 64 (flower-centre domes, seam spike, star speck) -> `$BAND_OUT/chain_final.png`. Stages 4-45 and 53 are retired in `archive/` (not part of the chain). `LATE=1` reruns only the late chain (seconds). `BG=1` runs detached (a plain `&` is killed when the tool call ends); `chain.sh status` shows log tail + running state. Stage params in the env (`ALPHA=1.5 bash chain.sh`) are passed through. |
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

## D28 grain.py (ground grain + bead pits vs reference)
`CROPX=7 python3 tools/wip_v3/grain.py [map.png]` (needs T2.png from the build). Ref Lab-L vs map H on the same px grid; writes /tmp/band_v3_out/grain_dbg.png (red = map dip>.10 with no ref dip within 4px, blue = ref dip missing in map).
Findings (v60): (1) ground grain is NOT excessive: std(hp1.5) map .0048 vs ref .0067, std(hp4) map .0079 (ref .026 includes shading). The +38% at .02 is the intentional stipple (stage50 STIP_A .04) now resolved, ref has at least as much fine grain. (2) Gold dips >.10: unmatched with ref = 2927 px = 0.5% of gold, 251 comps, median 5 px; only large ones are the kept dark-ref terrace (221 px, H .5, x2 mirrored) and 2 comps of ~50 px. The "skull" bead patches are the dark-ref terrace + grey recesses, which the ref also has. Conclusion: map-side cleanup of grain/pits = no measurable gain, do not redo. Do not blur the ground.

## D29 stage59 (issue #1: skull-like bead recesses)
Live render showed beads with a pin-hole "eye socket" + inner notches (skull look). stage59 fills every bead (beads.pkl + 2 top beads) inside .82 r with the stage50 dome, feathered .1 r, SIL=1 keeps the ref silhouette (raises gold dents H>.3 and ENCLOSED holes only; ground bites open to the outside stay). Runs at the end of chain.sh (chain_final = stage58 -> stage59). Metrics vs v60 (compare.py): IoU .995->.994, line recall .976->.966, ridge recall .945->.934, corr(L,H) .564->.536, lowfreq .697->.666, plateau .023->.036, slit rim err 3.4->5.2px: these drop BY DESIGN (the ref's bead interior detail/pin hole was removed on purpose; user rejected the skull look). Visual check (live_shot DSF=2 CLIP=440,130,380,200): clean domes. Map v61, ?v bumped by wire.py.

## D30 stage60 + B-spline relief sampling (issue #2/#3 jaggedness, round 1)
Zoomed live render (DSF=4) showed horizontal hatching on steep petal walls and wobbly outlines. Map has NO row-wise structure (d2y/d2x on walls 1.11, equal-neighbour frac 0): cause is mesh-side: at ultra .02 one map px spans ~2.7 mesh cells in v, bilinear `sampleRelief` puts a slope kink at every map row. Fixes: (1) site/geometry.js sampleRelief = bicubic uniform B-spline (C2). (2) stage60.py (runs last in chain.sh, after stage59): iso-line (tangential) gaussian smoothing of H, SIGT 3 px along the structure-tensor tangent, weighted by wall strength (|grad| .02-.06), so rim stair-steps/outline wobble go without softening the across-wall profile. jag.py (new): silhouette jaggedness probe (boundary dev vs gauss, sharp turns >60deg/3px). Results vs c59: sharp turns 442 -> 276 (17.0 -> 10.9 per 1000 px), boundary dev p99 1.35 -> 1.26; compare.py: IoU .994 -> .990 (thin tips round off), groove prec +.004, wide RMSE -.003, others +-.002. Map v62, site ?v=relief40. Still jagged after this: ragged dark vein slits at petal tips, left arc smear at grazing angle, fine stripes at top wall of some petals.

## D47 B3 sol4.py (Solitaire pattern aspect)
Measured: map mm/px along u .0191 vs .0221 across v = aspect .862 (3 repeats of the 538x134 ref strip over the half circle; ref strip itself is 4.0:1, model 3.47:1). `sol4.py` (one-shot on the committed map, guard W==1614) cuts the 3rd repeat at the flower-centre bead (A col 389, mirror-symmetry error minimum) -> 538|538|390 = 1466 cols, aspect .949; bottom mirror axis now runs through that flower. Note: sol1-3 are not bit-reproducible in a fresh sandbox (lib drift, mean |d| 13/255), so do not re-run sol3 over the committed map. Bottom render clean. ?v=relief56.

## D48 B2 (Solitaire wall hatching) - checked, no code change
Zoomed shank renders (DSF=3 CLIP=300,180,700,420 CAM=16.8,16.8,3 TGT=6.9,6.9,0; fine vs ultra, ultra renders fine in headless for Solitaire with SUB="q === 'fine' && ULTRA_OK=>q === 'fine'"): fine shows serrated petal walls + rail ripple, ultra smooths the petal walls visibly but the measured gain is modest: pixel-scale roughness |img - gauss 1.5| in the petal zone mean 1.99 -> 1.81 (-9%), p99 15.5 -> 15.6; B2 = ultra is the only fix, no further map/mesh lever found. Residual irregular ticks along both rails at ultra (spacing irregular 18-274 px, not mesh-periodic). Tried straightening the rail edge rows in the map along u (rms dev from median profile on clean columns halved: top row 13 15.9 -> 10.3, bottom row 9 6.5 -> 2.7): render unchanged (mean abs diff .06, tick std 11.52 -> 11.52) -> REJECTED, do not redo; remaining rail ticks are small (<.02 mm) and not map wobble.

## D50 B4 (band-end banding / fillet ribbing) - probe, no code change
Band tab oblique edge view (CAM=15,15,10 TGT=6,6,1, fine, DSF=2; zoom DSF=6 CLIP=150,140,200,80): no env-panel banding visible at 1x; at 6x zoom the top fillet shows faint ribs across the rim (rib hp std 2.16 gold-px gray levels /255, p99 9.7). Same ribs with relief OFF (band2 relief:0 -> std 1.52, p99 7.1) => NOT the relief map. Tried deterministic tie-break of the quad diagonal in torus() (surface-of-revolution ties decided by float noise): ribs unchanged (2.09) -> REJECTED. Remaining suspects (untested): fillet row spacing (Kf=8 over rf .32 = .063 mm vs column pitch .055) / vertex-normal weighting. Subtle (<1% gray, only visible at 6x), not pursued without a user screenshot.

## D51 B5 (adaptive ultra mesh for mobile) - measured, NOT worth it
Block test on the committed maps (block of BxB map px is 'flat' if max |grad| < t and max |lap| < 2t; flat blocks would be coarsened Bx/2): band (260x1198): B=4 t=.02 flat 30% -> .78 of uniform tris; B=8 t=.02 flat 12% -> .89; B=16 flat 2% -> .98; at t=.005 (truly flat) only 4%/1%/0%. Solitaire (134x1466): B=4 flat 14-16% -> .88-.90; B=8 3-4% -> .97; B=16 0%. The ground carries the intentional stipple grain (stage50) so almost nothing is flat: best case ~-22% tris (band, B=4, loose threshold) for T-junction/crack handling in a regular-grid torus mesh. Rejected. Cheaper alternatives if mobile ultra is ever wanted: a mid step (ULTRA_STEP .03 = 2.25x fewer tris than .02, walls ~4 cells vs 6) - needs a device test, not done.

## D56/D57 stage64 (phone issue: skull-like flower centres)
Phone screenshot showed skull faces at the flower centres. (1) Main centre bead had a pin-hole + bump -> fitted dome. (2) The SEAM flower (map x=0/2396, shown at the band ends) had a skull-shaped centre blob -> dome bead (e=40000, P=61000, sqrt profile over the distance transform); a pointed shard between two petals at its bottom (rolled box x1182-1218,y473-506) -> ground. (3) Ragged star speck (comp H>8000 at (2012,295)) -> ground. `stage64.py [in.png]` -> `$BAND_OUT/c64.png`; verified: stage64 applied to the pre-fix committed map reproduces the committed `maps/band_period.png` byte-for-byte. Retired stages: see `archive/README.md`.

D81 centre fill (tools/vec/centre_fill.py): post-step AFTER zonal.py (build_map -> add_berries -> zonal -> centre_fill -> wire). Fills the dark moat around the main flower centre bead (map 1199.5,240) with the neighbouring petal surface (nearest-petal height, blended to a plateau near the bead) so petals surround the bead; thin radial grooves kept at auto-detected petal gaps / central veins. Env: CEN RF(104) RFE(10) R0(36) PL0 PL1 NB G0 GK. Main flower only (seam flower not done).

D82 daisies (tools/vec/daisies.py): pipeline now build_map -> daisies -> add_berries -> zonal -> centre_fill -> wire. Stamps three proper 8-petal daisies (broad rounded near-touching petals, hairline gaps, bead, bevel W9): side daisies at map (236,258) and (2162,258) L190, seam daisy at x=0 L195 (old mirrored partial flower cleared inside SEAMCLEAR 215, leftovers removed). Env DAISY 'x,y,L;..' N RB GAP BW WMAX MOAT SEAMCLEAR SEAMFAR SEAMAREA. Known: stray old-wing leftovers near map (140-230,15-100) and mirror remain; petals have no rib/hairlines yet (S-2).
D83 daisy petals rounded: elliptical tips (no kite point), WMAX 42, quarter-round bevel BW 12, flatter dome (.70+.10). relief95
D84 daisies.py leftovers cleanup: seam wing remnants (comps with no new daisy pixels within SEAMFAR 360 of seam), thin slivers + 1-px specks near daisies (SLA 2500, SLC .35 circularity). relief96. NOTE: never pipe run to head (SIGPIPE kills later stages).
D85 centre_fill spokes -> shallow hairlines (G0 1.3, GK .02, GD .5 floor); relief97. Rib+hairlines per petal (VEIN) still to do.
D86 petal vein = low rib (VEINR .05, half-width VEINO 4.5) + 2 hairline grooves at +-VEINO (VEINHW 1.3, depth VEIN .15) in build_map (main + SEAMVEIN); daisies.py DVO 9 DVHW 1.3 DVD .07 DVR .03 tapered rib+hairlines per petal. relief98
D87 ground micro-dots (tools/vec/ground_dots.py, LAST pipeline step after centre_fill, before wire): seeded poisson dots r 3-6.5 px, h .12-.26 dome, CLR 20 from gold, rows 46..h-46, left half mirrored x->w-x; env SEED RMIN RMAX HMIN HMAX CLR SP YM NMAX. 86x2 dots. NOT idempotent-safe: run once on centre_fill output. relief99
D88 S-4 leaf slits: tapered cuts along leaf axis (build_map TAPER 1 TW 3.2 TL 1.25 TP 1.6), relief100
D89 leaf cuts follow hole curvature (build_map TC 1, parabola fit) and TL 1.0, relief101
