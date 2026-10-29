WIP: band height map v3 (not wired into maps/ yet; maps/ still = v2).
Run from repo root: mkdir -p /tmp/band_v3_out && python3 tools/wip_v3/stage1.py && python3 tools/wip_v3/stage2.py && python3 tools/wip_v3/stage3.py
Needs opencv-python, numpy, scipy, scikit-image.
stage1: exact seamless period (side flower axis -> centre flower axis, mirrored, 1198 cols) tiled x3, upscaled 2x, gold mask + slit detection.
stage2: bead circle refinement (fits well on all 7 beads).
stage3: carve beads/centre domes, marker watershed into separate petals/leaves (51 labels), label overlay.
stage4: per-region smoothed SDF relief, thin slit grooves, veins, bead/dot/centre domes, symmetrize -> /tmp/band_v3_out/band_period_v3.png (16-bit 2396x520, exact seamless period) + previews.
stage5 (2026-10-29, APPROVED-TO-REPLACE: maps/band_period.png is now the stage5 output): centre-flower polish on top of stage4. Run from repo root: mkdir -p /tmp/band_v3_out; python3 tools/wip_v3/stage2.py; python3 tools/wip_v3/stage5.py -> /tmp/band_v3_out/band_period_v4.png (+ v4_zoom_B.png). Centre petals rebuilt as convex leaf shapes (fills slit bites), no slit carving in centre zone, sigma 2.0S for pointed tips, wedge gaps near dome, one shallow tapered vein per petal. NOT approved; maps/band_period.png is still v3. Still to polish: petals stop short of the dome, only 1 vein per petal (reference has 2-3 fine radiating lines), L/R tips blunt.
TODO: user approval, then replace maps/band_period.png, wire into band() in geometry.js (continuous 0..1 height), Wide band, Solitaire, STLs.
NOTE: maps/band_period.png and maps/band_preview.png are now v3 (approved by user 2026-10-29). maps/band_height.png is still the old v2 window map (not used by anything); tools/band_heightmap.py is the old v2 generator.
stage6 (2026-10-29): stage5 generalised to BOTH flowers (side + centre); output band_period_v5.png = current maps/band_period.png. Run: mkdir -p /tmp/band_v3_out; python3 tools/wip_v3/stage2.py; python3 tools/wip_v3/stage6.py. Side flower: bottom pair split at axis, R/L petals keep their long tails (no hull), slit fork filled + thin groove. Previous version (centre-only polish) = commit 180c5cc.
