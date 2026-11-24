#!/bin/sh
# Pairing gate: regenerate the report for main (docs/) and for a branch view (docs/branch/, the given branch
# where a repo has it, else main), then run the pairing checks on that view. Exit 1 if a known pair breaks or
# a count rises above tools/baseline.json. The page's Source picker switches between the two.
#   tools/gate.sh [branch]        default branch: main
set -e
cd "$(dirname "$0")/.."
branch="${1:-main}"
python3 tools/generate.py
python3 tools/generate.py --branch "$branch" --docs docs/branch
# repos the report does not show yet, but the pairing checks read (stale 94G file names, known pairs)
for repo in NHL94PC; do
  d=.cache/src/$repo
  [ -d $d/.git ] || git clone -q --depth 1 https://github.com/abdulahmad/$repo.git $d
  (cd $d && { git fetch -q --depth 1 origin "$branch" 2>/dev/null || git fetch -q --depth 1 origin main; } && git checkout -q --detach FETCH_HEAD)
done
NDR_DATA=docs/branch/data python3 tools/test_group_order.py
python3 tools/test_pairs.py
