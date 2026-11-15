Offline cleanup that produced site/nodiamond2.glb from site/nodiamond1.glb.
Run: python3 clean.py OUT.glb (needs numpy, scipy). Paths inside point at /tmp/r and /tmp; adjust SRC and the glb.py import.
Steps: delete old rim bulbs/cups/skirt/flap triangles, peel ragged boundary triangles (ears, strips, long thin), Taubin-smooth the boundary loops, repack GLB (images untouched).
v6 (site/nodiamond6.glb): python3 clean3.py nodiamond5.glb 0.13 6 (only bulbs+cups deleted, skirt/flap kept, peel/smooth limited to 0.13 around the 4 knobs) then python3 fill.py nodiamond5.glb nodiamond6.glb 24 300 (caps the 4 bulb holes with faired ring patches). Paths inside point at /tmp/w and /tmp/r.
