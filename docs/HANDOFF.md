# Handoff: nhl-disasm-report

## Now

- Stage / unit: regen after 95PC leftover functional work (SHA only; 93S/94S/94G asstab already on #78).
- Branch: `cursor/regen-95pc-e79b`
- Last check: `tools/gate.sh` PAIRING OK, all counts 0, known pairs 752 (2026-11-06).
- Next: none for this unit.
- Open PRs: this unit

## Status (2026-10-20)

- The report is regenerated from the latest `main` of all seven source repos (92G, 93G, 94G, 95G, 96G, 93S, 94S). The generated files are `docs/index.html` and `docs/data/<game>.js`; the same source SHAs give byte-identical output.
- Regenerate with `python3 tools/generate.py` (fetches each source repo at `origin/main` into `.cache/src`, read-only; `--offline` reuses the cache). Open a PR and merge it each time a source repo changes layout or names. Agents may merge `claude/project-thread-ggw7zu` into `main` here (this repo only, Abdul 2026-11-03) once `tools/gate.sh` passes.
- Last sources (origin/main): 92G `9eeb1a1134`, 93G `c7b3ca2956`, 94G `c57bad143d`, 95G `edc9f7e255`, 96G `105ce1f1a3`, 93S `d7f287545f`, 94S `e6833cb48b`, 95S `19eff3eff9`, 95P `2339fb69d6`.

## Pairing gate

- `tools/gate.sh [branch]` regenerates the report from that branch of each source repo (default `claude/project-thread-ggw7zu`, the alignment branch; a repo without it is read at `main`), runs `tools/test_group_order.py`, then `tools/test_pairs.py`.
- `tools/test_pairs.py` fails when a row of `tools/known_pairs.csv` stops pairing or a count rises above `tools/baseline.json`: 94S routines not in their 94G file (`94S~94G`), 94S placed unlike 93S where 94G does not explain it (`94S~93S`), 93S routines outside their 93G module (`93S~93G`), 93S `hockey/<area>/` routines whose 94G file is not the area's (`93S-area`), 93S/94S names 94G renamed (`lineage`), and files that still name the 94G files merged on 2026-10-31 (`stale94`). `--list <count>` prints the routines behind a count. `tools/pair_exceptions.csv` holds the deliberate exceptions, each with its reason.
- After a step lowers a count, run `python3 tools/test_pairs.py --write-baseline` and commit the new baseline with that step. A count may never go up.
- `--src DIR` checks sibling checkouts instead of `.cache/src` (also scans the PC repos for `stale94` when they are there).
- `generate.py` also reads `docs/history/name_map.csv` (93S keeps its rename history there).

## Open

- The report must be regenerated after the NHL94SNES comment pass finishes (see that repo's `docs/HANDOFF.md`; about 1,640 labels were still uncommented).
- 94S matches 93S by routine group; 94S folders follow the 94G files, so many 94S routines show as placed differently from 93S. That is expected, not a bug.
- SNES *groups* / `rom:groups` / a groups layout pane / a groups include-tree pane re-sort modules to a **Genesis** comparison's include order (`targets.*.seq`). Applies to both 93S and 94S vs 92G, 93G, 94G, 95G, 96G. Banks view stays ROM order. An SNES groups comparison (groups view with `c=93S:groups`, a groups layout / include-tree pair) makes the groups view (right pane) follow the other game's folder order; unmatched folders go after their best routine-overlap folder, else stay after their first-ROM predecessor. An SNES banks comparison leaves first-ROM order. Routines inside a group stay in ROM order. `python3 tools/test_group_order.py` checks the 93S/94S × Genesis pairs.
