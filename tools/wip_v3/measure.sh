#!/bin/bash
# Run every metric script on a map and print their summaries.
#   bash tools/wip_v3/measure.sh [map.png]      default map = $BAND_OUT/chain_final.png
# Needs $BAND_OUT/T2.png (written by stage1, so run chain.sh once first). BAND_OUT default /tmp/band_v3_out.
# diff.py  : silhouette IoU, groove (line) recall/precision, clipping, plateau, H stats
# idiff.py : same family, inner-line diff
# tdiff.py : ridge recall/precision (writes tdiff_<map>.png)
# cdiff.py : cushion slope corr(L,H), R2, width-normalised crown profile RMSE/lead
set -eo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${BAND_OUT:-/tmp/band_v3_out}"
MAP="${1:-$OUT/chain_final.png}"
export CROPX="${CROPX:-7}"
[ -f "$OUT/T2.png" ] || { echo "missing $OUT/T2.png - run tools/wip_v3/chain.sh first"; exit 1; }
[ -f "$MAP" ] || { echo "missing map $MAP"; exit 1; }
cd "$REPO"
for t in diff idiff tdiff cdiff; do
  echo "===== $t.py $MAP"
  python3 tools/wip_v3/$t.py "$MAP" "$OUT"
done
