# Reusable scripts (tools/wip_v3)

All take `BAND_OUT` (work dir, default `/tmp/band_v3_out`) and `CROPX` (default 7). Run from anywhere; they locate the repo themselves.
Needs: python3 with opencv-python, numpy, scipy, scikit-image; `node` for the site test. Invoke with `bash script.sh` / `python3 script.py` (files pushed via API have no exec bit).

| script | what it does |
|---|---|
| `chain.sh` | Rebuilds the current map (v58) from scratch: stage1,2,49,50,51 -> 54 -> 56 -> 55 (RIB=0 KNEE=.70 COMP=.6) -> 52 -> 55 (RIB=.22 COMP=1). Output `$BAND_OUT/chain_final.png`. `LATE=1` skips stage1..51 and reruns only the late chain (seconds, use this when tuning stage54/56/55/52). Stage params set in the env (`ALPHA=1.5 bash chain.sh`) are passed through. |
| `measure.sh [map.png]` | Runs diff.py, idiff.py, tdiff.py, cdiff.py on a map (default `chain_final.png`) and prints IoU, groove recall/precision, ridge recall/precision, plateau/clipped, lowfreq corr, cushion-slope corr/R2, crown-profile RMSE/lead. Needs `$BAND_OUT/T2.png` (written by stage1). |
| `wire.py MAP.png` | Copies MAP to `maps/band_period.png`, regenerates the b64 in `site/relief_band.js`, bumps `?v=reliefN` in `site/index.html`, runs `node site/test.mjs`. `--check` verifies the committed b64 equals `maps/band_period.png` (does not modify anything). `--no-test` skips the node test. Does not commit. |
| `push.sh` | `GH_TOKEN=... bash tools/wip_v3/push.sh` pushes HEAD to origin/main (token masked in output) and verifies HEAD == origin/main. If the git proxy 403s (repo not in session sources), use `mcp__Madmcp__overwrite_files` on branch main instead. |

## Typical loop
```
bash tools/wip_v3/chain.sh                         # once per fresh sandbox (~2 min)
# edit a late stage (54/56/55/52), then:
LATE=1 bash tools/wip_v3/chain.sh && bash tools/wip_v3/measure.sh
# if metrics improve without regressions:
python3 tools/wip_v3/wire.py $BAND_OUT/chain_final.png
git add -A && git commit      # trailers: see checkpoint
GH_TOKEN=... bash tools/wip_v3/push.sh
```

## Notes
- The stages hardcode `/tmp/band_v3_out` and `exec()` each other via `tools/wip_v3/stageN.py`. `chain.sh` therefore runs from a shadow repo root at `$BAND_OUT/_root` (symlinks to the repo, with a sed-patched copy of `tools/wip_v3`); the repo files are never modified by it.
- Reproducibility: with cv2 5.0.0 / numpy 2.5.3 the rebuilt v58 is not byte-identical to the committed map (earlier sandboxes were), but all metrics are within noise (IoU .995, line .976/.987, ridge .945/.932, corr(L,H) .557, R2 .329). Always compare a rebuilt map against `measure.sh maps/band_period.png` from the same environment, not against numbers recorded in other sandboxes (the committed map measures IoU .994 / EXTRAR 5015 here).
- `err.py` is INVALID, do not use.
