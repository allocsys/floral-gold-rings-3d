WIP: band height map v3 (not wired into maps/ yet; maps/ still = v2).
Run from repo root: mkdir -p /tmp/band_v3_out && python3 tools/wip_v3/stage1.py && python3 tools/wip_v3/stage2.py && python3 tools/wip_v3/stage3.py
Needs opencv-python, numpy, scipy, scikit-image.
stage1: exact seamless period (side flower axis -> centre flower axis, mirrored, 1198 cols) tiled x3, upscaled 2x, gold mask + slit detection.
stage2: bead circle refinement (fits well on all 7 beads).
stage3: carve beads/centre domes, marker watershed into separate petals/leaves (51 labels), label overlay.
TODO: per-region smoothed SDF height profile, slits as grooves, veins, bead/dot/centre domes, symmetrize, write period + preview.
