#!/bin/bash
# Commit everything with the standard identity and trailers.
#   bash tools/wip_v3/commit.sh "D21: message"
# Env: CLAUDE_SESSION (session URL for the Claude-Session trailer; default below).
set -eo pipefail
MSG="${1:?usage: commit.sh \"message\"}"
SESSION="${CLAUDE_SESSION:-https://claude.ai/code/session_01K96UYpLs7mTNwJ3z2Md3ke}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"
git config user.name  >/dev/null || git config user.name  "Claude"
git config user.email >/dev/null || git config user.email "noreply@anthropic.com"
git add -A
git diff --cached --quiet && { echo "nothing to commit"; exit 0; }
git commit -q -m "$MSG" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: $SESSION"
git log --oneline -1
git show --stat --format= HEAD | tail -8
