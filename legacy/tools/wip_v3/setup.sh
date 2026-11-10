#!/bin/bash
# One-time setup for a fresh sandbox. Safe to rerun.
#   git clone https://github.com/allocsys/floral-gold-rings-3d.git && bash floral-gold-rings-3d/tools/wip_v3/setup.sh
# Does: installs missing python libs (pip --break-system-packages), checks node, sets git identity,
#       starts the full chain rebuild in the background (BG=1) ONLY if BUILD=1 (legacy), prints next steps.
set -eo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${BAND_OUT:-/tmp/band_v3_out}"
need=""
for m in "cv2:opencv-python-headless" "numpy:numpy" "scipy:scipy" "skimage:scikit-image"; do
  python3 -c "import ${m%%:*}" 2>/dev/null || need="$need ${m##*:}"
done
[ -n "$need" ] && { echo "installing:$need"; pip install -q --break-system-packages $need; }
command -v node >/dev/null || echo "WARNING: node missing, wire.py site test will fail (use --no-test)"
cd "$REPO"
git config user.name  >/dev/null || git config user.name  "Claude"
git config user.email >/dev/null || git config user.email "noreply@anthropic.com"
python3 -c "import cv2,numpy,scipy,skimage;print('libs: cv2',cv2.__version__,'numpy',numpy.__version__,'scipy',scipy.__version__,'skimage',skimage.__version__)"
echo "HEAD $(git rev-parse --short HEAD)  branch $(git rev-parse --abbrev-ref HEAD)"
if [ -n "$BUILD" ]; then   # legacy raster chain is OPT-IN (BUILD=1): the live map comes from tools/vec/build_map.py
  if [ -f "$OUT/T2.png" ] && [ -f "$OUT/band_period_v51.png" ]; then echo "stage1..51 outputs already in $OUT (LATE=1 chain is enough)";
  else BG=1 bash tools/wip_v3/chain.sh; fi
fi
cat <<MSG
next:  bash tools/wip_v3/chain.sh status      # wait for the build (~4 min)
       LATE=1 bash tools/wip_v3/chain.sh && python3 tools/wip_v3/compare.py
see tools/wip_v3/SCRIPTS.md
MSG
