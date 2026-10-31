# Silhouette diff, map v50 (HEAD 941305b)

Image: `diff_band_period_v50.png` (1198x260). Grey = both, red = MISS (gold in ref, not in relief), orange = EXTRA.
Made with `CROPX=7 python3 tools/wip_v3/diff.py` (needs `/tmp/band_v3_out/T2.png` from `stage2.py`, then `stage49.py`, `stage50.py`).

## Numbers (grid 2396x520, S=2)
- IoU 0.874 | ref gold 57.3% | relief gold 52.4% | MISS 76217 px | EXTRA 15814 px
- Relief mask = map > 0.3. Ref mask = Lab k-means (k=4, fixed centres), clusters 1 and 3, then 3x3 open+close.

## MISS breakdown (`tools/wip_v3/missstats.py`, full output in `diff_v50_stats.txt`)
| distance from relief edge | MISS px |
|---|---|
| 0-2 px | 29761 |
| 2-4 px | 15558 |
| 4-8 px | 11598 |
| 8-16 px | 10131 |
| >16 px | 9169 |

- Within 4 px of the relief edge: 45319 px (59%). Mostly the ref's soft rim and glow, which is partly a measurement artifact.
- Core MISS (opening 9x9, blobs wider than about 8 px): 24446 px in 40 blobs. These are the real gaps to fill.
- Largest blobs (x, y, w, h on the 2396x520 grid): (333,269,71,61) and its mirror (1994,269); (811,12,76,50) and (1511,12); (1062,166,78,58) and (1258,166); (58,219,79,23) and (2261,219).

# v51 (stage51.py: fill the real MISS gaps), NOT wired into the viewer yet
Run: `CROPX=7 python3 tools/wip_v3/stage51.py` (reads stage50 map, writes `/tmp/band_v3_out/band_period_v51.png`), then `diff.py` on it.
Files: `diff_band_period_v51.png`, `diff_v51_stats.txt`, `crops_ref_v50_v51.png` (columns: ref | v50 | v51).

| | v50 | v51 |
|---|---|---|
| IoU | 0.874 | 0.907 |
| relief gold | 52.4% | 54.4% |
| MISS px | 76217 | 52261 |
| EXTRA px | 15814 | 15900 |
| core MISS blobs (>8 px wide) | 40 / 24446 px | 4 / 324 px (isolated ground speckles, skipped on purpose) |

Method: blobs that touch the relief are reconstructed within 6 px, their ragged k-means edge is smoothed (gaussian 3), then the relief edge slope (median profile of the existing relief) is grown outward continuously (profile of distance to outside x local modulation), so there is no step at the join.
Remaining MISS (52k) is the rim: 0-4 px from the edge is 43578 of it. Known flaws in the crops: faint crease on the top leaf-tip patch, fill edges still slightly angular.
