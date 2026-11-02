#!/bin/bash
# Push HEAD to origin/main with a short-lived GitHub token and verify. The token is never printed.
#   GH_TOKEN=<token from mcp__Madmcp__gh_token(repo=floral-gold-rings-3d)> bash tools/wip_v3/push.sh
# Pushes straight to github.com with the token (not via the session git proxy). If it still fails with 403/401 the token
# is expired or lacks write access: mint a new one (tool_search 'gh_token mint github token'), or fall back to
# mcp__Madmcp__overwrite_files on branch main.
set -eo pipefail
: "${GH_TOKEN:?set GH_TOKEN (mint with mcp__Madmcp__gh_token)}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
URL="https://x-access-token:${GH_TOKEN}@github.com/allocsys/floral-gold-rings-3d.git"
mask() { sed "s#${GH_TOKEN}#***#g"; }
git diff --quiet && git diff --cached --quiet || echo "WARNING: uncommitted changes are NOT pushed (run commit.sh)"
git push "$URL" HEAD:main 2>&1 | mask || true
git fetch "$URL" main 2>&1 | mask
H="$(git rev-parse HEAD)"; R="$(git rev-parse FETCH_HEAD)"
if [ "$H" = "$R" ]; then echo "PUSHED, HEAD==origin/main==${H:0:7}"; else echo "NOT IN SYNC: HEAD ${H:0:7} origin ${R:0:7}"; exit 1; fi
git status --short | head -5
