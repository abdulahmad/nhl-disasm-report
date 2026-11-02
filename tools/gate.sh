#!/bin/sh
# Pairing gate: regenerate the report from the alignment branch (or main where a repo has no such branch),
# then run the pairing checks. Exit 1 if a known pair breaks or a count rises above tools/baseline.json.
#   tools/gate.sh [branch]        default branch: claude/project-thread-ggw7zu
set -e
cd "$(dirname "$0")/.."
branch="${1:-claude/project-thread-ggw7zu}"
python3 tools/generate.py --branch "$branch"
# repos the report does not show yet, but the pairing checks read (stale 94G file names, known pairs)
for repo in NHL94PC NHL95PC; do
  d=.cache/src/$repo
  [ -d $d/.git ] || git clone -q --depth 1 https://github.com/abdulahmad/$repo.git $d
  (cd $d && { git fetch -q --depth 1 origin "$branch" 2>/dev/null || git fetch -q --depth 1 origin main; } && git checkout -q --detach FETCH_HEAD)
done
python3 tools/test_group_order.py
python3 tools/test_pairs.py
