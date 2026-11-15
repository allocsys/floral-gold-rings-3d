Offline cleanup that produced site/nodiamond2.glb from site/nodiamond1.glb.
Run: python3 clean.py OUT.glb (needs numpy, scipy). Paths inside point at /tmp/r and /tmp; adjust SRC and the glb.py import.
Steps: delete old rim bulbs/cups/skirt/flap triangles, peel ragged boundary triangles (ears, strips, long thin), Taubin-smooth the boundary loops, repack GLB (images untouched).
