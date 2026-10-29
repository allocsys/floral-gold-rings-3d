WIP: band height map v3 (not wired into maps/ yet; maps/ still = v2).
Run from repo root: mkdir -p /tmp/band_v3_out && python3 tools/wip_v3/stage1.py && python3 tools/wip_v3/stage2.py && python3 tools/wip_v3/stage3.py
Needs opencv-python, numpy, scipy, scikit-image.
stage1: exact seamless period (side flower axis -> centre flower axis, mirrored, 1198 cols) tiled x3, upscaled 2x, gold mask + slit detection.
stage2: bead circle refinement (fits well on all 7 beads).
stage3: carve beads/centre domes, marker watershed into separate petals/leaves (51 labels), label overlay.
stage4: per-region smoothed SDF relief, thin slit grooves, veins, bead/dot/centre domes, symmetrize -> /tmp/band_v3_out/band_period_v3.png (16-bit 2396x520, exact seamless period) + previews.
TODO: user approval, then replace maps/band_period.png, wire into band() in geometry.js (continuous 0..1 height), Wide band, Solitaire, STLs.
NOTE: maps/band_period.png and maps/band_preview.png are now v3 (approved by user 2026-10-29). maps/band_height.png is still the old v2 window map (not used by anything); tools/band_heightmap.py is the old v2 generator.
