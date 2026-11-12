# Solitaire 3 = Solitaire 2 clone + gradual edits
- `s2map.py` : maps solitaire_6.glb into regions (gold/gem/bore x 15 deg sector x shell x z side), writes s2map.npz/png + table.
- `s3edit.py edits.json [base] [out]` : applies edit ops (scale_z / radial / move, smooth feathered selections) to the S2 vertices -> solitaire3.glb (same topology/UVs/textures). `s3edits.json` = [] = byte-identical clone; `s3edits_demo.json` = example.
- `s3diff.py base.glb edit.glb [png]` : per-region diff table + heat-map (front, theta x rho/R, theta x z).
Loop: edit s3edits.json -> s3edit.py -> s3diff.py (check) -> render -> commit.
