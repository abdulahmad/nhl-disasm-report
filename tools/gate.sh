#!/bin/sh
# Pairing gate: regenerate the report from the alignment branch (or main where a repo has no such branch),
# then run the pairing checks. Exit 1 if a known pair breaks or a count rises above tools/baseline.json.
#   tools/gate.sh [branch]        default branch: claude/project-thread-ggw7zu
set -e
cd "$(dirname "$0")/.."
branch="${1:-claude/project-thread-ggw7zu}"
python3 tools/generate.py --branch "$branch"
python3 tools/test_group_order.py
python3 tools/test_pairs.py
