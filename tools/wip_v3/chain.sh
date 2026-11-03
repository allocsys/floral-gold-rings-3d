#!/bin/bash
# Rebuild the band height map (current chain = v60) from scratch.
#   bash tools/wip_v3/chain.sh            # full rebuild (~1.5 min for stages 1..51), then the late chain
#   LATE=1 bash tools/wip_v3/chain.sh     # reuse existing stage1..51 outputs, rerun only 54 -> 56 -> 55 -> 52 -> 55 -> 57
# Env:
#   BAND_OUT   work dir (default /tmp/band_v3_out). The stages hardcode that path, so a patched copy of the
#              tools is made under $BAND_OUT/_root and used instead; the repo files are never modified.
#   CROPX      default 7. Any stage parameter (RIB, KNEE, COMP, TL, ALPHA, ...) set in the env is passed through
#              to every stage, EXCEPT the three that the chain pins itself (RIB/KNEE/COMP on the two stage55 runs).
# Output: $BAND_OUT/chain_final.png (16-bit 520x2396). Intermediates: c54, c56, c55a, c52 (.png).
# Final line says whether chain_final.png is byte-identical to maps/band_period.png.
set -eo pipefail
# BG=1 bash chain.sh   -> run detached (survives the tool call), log in $BAND_OUT/chain.log
# bash chain.sh status -> show the log tail and whether it is still running / finished
_OUT="${BAND_OUT:-/tmp/band_v3_out}"
if [ "$1" = status ]; then
  tail -4 "$_OUT/chain.log" 2>/dev/null || true; pgrep -f "_root/tools/wip_v3/stage" >/dev/null && echo "RUNNING" || echo "not running"; exit 0
fi
if [ -n "$BG" ] && [ -z "$_CHAIN_CHILD" ]; then
  mkdir -p "$_OUT"; _CHAIN_CHILD=1 setsid nohup bash "${BASH_SOURCE[0]}" > "$_OUT/chain.log" 2>&1 < /dev/null &
  echo "started in background, log $_OUT/chain.log (check: bash tools/wip_v3/chain.sh status)"; exit 0
fi
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${BAND_OUT:-/tmp/band_v3_out}"
ROOT="$OUT/_root"     # shadow repo root: symlinks to the real repo, except tools/wip_v3 = patched copy
TOOLS="$ROOT/tools/wip_v3"
export CROPX="${CROPX:-7}"

mkdir -p "$OUT"
rm -rf "$ROOT"; mkdir -p "$ROOT/tools"
for e in "$REPO"/* "$REPO"/.[!.]*; do [ -e "$e" ] && [ "$(basename "$e")" != tools ] && ln -s "$e" "$ROOT/$(basename "$e")" || true; done
for e in "$REPO"/tools/*; do [ "$(basename "$e")" != wip_v3 ] && ln -s "$e" "$ROOT/tools/$(basename "$e")" || true; done
cp -r "$REPO/tools/wip_v3" "$TOOLS"
sed -i "s#/tmp/band_v3_out#$OUT#g" "$TOOLS"/*.py
# stages exec() each other via the repo-relative path 'tools/wip_v3/stageN.py', so they must run from $ROOT
cd "$ROOT"   # stages use ROOT='.'

if [ -z "$LATE" ]; then
  for s in stage1 stage2 stage49 stage50 stage51; do echo "== $s"; python3 "$TOOLS/$s.py"; done
else
  [ -f "$OUT/band_period_v51.png" ] && [ -f "$OUT/T2.png" ] || { echo "LATE=1 needs $OUT/band_period_v51.png and T2.png (run without LATE first)"; exit 1; }
fi

run() {  # run <stage> <input> <outname-written-by-stage> <copy-to>   (stages overwrite their own output name)
  python3 "$TOOLS/$1.py" "$2"; cp "$OUT/$3" "$OUT/$4"
}
echo "== late chain"
run stage54 "$OUT/band_period_v51.png" band_period_v54.png c54.png
run stage56 "$OUT/c54.png"             band_period_v56.png c56.png
RIB=0 KNEE=.70 COMP=.6 run stage55 "$OUT/c56.png"  band_period_v55.png c55a.png
run stage52 "$OUT/c55a.png"            band_period_v52.png c52.png
RIB=.22 COMP=1          run stage55 "$OUT/c52.png"  band_period_v55.png c55b.png
run stage57 "$OUT/c55b.png"            band_period_v57.png c57.png
run stage58 "$OUT/c57.png"             band_period_v58x.png chain_final.png
python3 "$REPO/tools/wip_v3/stage59.py" "$OUT/chain_final.png" && cp "$OUT/c59.png" "$OUT/chain_final.png"   # D29 bead fill
python3 "$REPO/tools/wip_v3/stage60.py" "$OUT/chain_final.png" && cp "$OUT/c60.png" "$OUT/chain_final.png"   # D30 iso-line smoothing
python3 "$REPO/tools/wip_v3/stage61.py" "$OUT/chain_final.png" && cp "$OUT/c61.png" "$OUT/chain_final.png"   # D35 bead bite fill (convex hull dome)
python3 "$REPO/tools/wip_v3/stage62.py" "$OUT/chain_final.png" && cp "$OUT/c62.png" "$OUT/chain_final.png"   # D36 star ghost -> single pearl

echo "wrote $OUT/chain_final.png"
python3 -c "import cv2,numpy,scipy,skimage;print('libs: cv2',cv2.__version__,'numpy',numpy.__version__,'scipy',scipy.__version__,'skimage',skimage.__version__)"
if cmp -s "$OUT/chain_final.png" "$REPO/maps/band_period.png"; then
  echo "chain_final.png is BYTE-IDENTICAL to maps/band_period.png"
else
  echo "chain_final.png DIFFERS from maps/band_period.png."
  echo "  Expected if you changed a stage. If not, it is library drift (byte-identical on cv2 4.13/numpy 2.4.4; not on cv2 5.0/numpy 2.5)."
  echo "  Judge it with: python3 tools/wip_v3/compare.py   (A = committed map, B = this build, same environment)"
fi
