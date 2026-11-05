# Rules (report)

The rules for this repo's part of the alignment, then the learned rules. Read before every unit. Any tool adds a learned
rule in the same commit as the fix that confirmed it, newest last: `- YYYY-MM-DD <area>: <rule>. (<evidence>)`.

## Who decides what (all games)

| Category | Decided by |
|---|---|
| Name of a routine several games share | the earliest game that has it (92G is the root); a fix goes to the earliest repo first, then down the lineage |
| Name of a feature new in year N | that year's Genesis game (94G for 94S and 94PC, 95G for 95S and 95PC) |
| Name of a platform-only job | the earlier repo on that platform (93S for 94S, 94PC for 95PC), else what the code does |
| Same name, different job | the earlier meaning keeps the name |
| Top folder or file | the same-year Genesis file |
| RAM order | the merged order (92G, 93G, 94G, 93S, 94S, then 95G, 96G) |
| Data, assets, banks | the earlier repo on the same platform |
| Order inside a file | ROM order (the report re-sorts for display) |
| History | `docs/name_map.csv` only, never source comments |

## This repo

- The pairing gate never gets looser to make a step pass. A count in tools/baseline.json only goes down; a new exception in tools/pair_exceptions.csv needs a reason.
- The report reads the alignment branch with --branch. This repo is the one exception to branch-only (Abdul, 2026-11-03): `claude/project-thread-ggw7zu` may be merged into `main` once tools/gate.sh passes, so the live page is current. Every other repo stays branch-only.

## Learned

- 2026-11-04 D6: 96G leftover `sub_` names are named from job/callers/SRAM/role; same job + new body takes the 95G name. `input96_shot` SetRoles / SetTeamRoles / ClearRolesIfGoalie. Pairing counts unchanged. (96G `07141d8`; `tools/gate.sh`)
- 2026-11-04 D6: 96G leftover `sub_`/`loc_`/`unk_` closed (StartDpadBoost through ram96 unk_FF). Pairing counts unchanged. (96G `f170dbe`; `tools/gate.sh`)
- 2026-11-04 D6: 96G leftover ram96 `word_FF` / `byte_FF` / `dword_FF` named from job, 94G/95G RAM, or layout. Pairing counts unchanged. (96G `2a7c295`; `tools/gate.sh`)
- 2026-11-04 D6: 96G For-Abdul same-job 95G names: BlankMenuBox→ClearMenuBox, CupChampionsScreen→StanleyCupScreen; PauseScreenDraw, SimTeamGoals, SimScorers, SimShots, ClearSeasonData kept. Pairing counts unchanged. (96G `fb49066`)

- 2026-11-04 contributing: CONTRIBUTING.md must not contradict History: lineage lives only in the name history file, never in source comments. (CONTRIBUTING rewrite vs RULES History row)
- 2026-11-04 name_map: a `from 92 Parent` split is not a rename row. Putting Fprint→Fprintsmall or periodicevents→RestoreBenchEnergy into a source repo's name_map.csv made pairing counts rise (93S~93G, lineage, 95S~95G). The map is old→new in that repo, not "came from 92".
- 2026-11-04 leftovers: D2/D5/D6 and F3 95-feature names closed with no report regen; pairing input did not change. (no asm rename this unit; D2 LockScroll was already on the branch)
- 2026-11-04 93S: comment-layout only (column 36 / wrap 110) does not change pairing counts or units; regen updates the 93S SHA. 94S #386 stub-fold also SHA-only for pairing. (93S #121 `9e442ac`; 94S #386 `e72e360`; `tools/gate.sh`)
- 2026-11-05 names: 94G/95G/96G/95S CreditsList is 93G CreditsPages (title-screen pages after Credits). 92G has only Credits. Pairing counts unchanged. (94G #231; 95G #60; 96G #45; 95S #5; `tools/gate.sh`)
- 2026-11-05 files: 95S CreditsList.asm → CreditsPages.asm; pairing counts unchanged. (95S #6 `19eff3e`; `tools/gate.sh`)
