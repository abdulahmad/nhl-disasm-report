# NHL alignment plan: all games

Analysis and plan only. Nothing in any repo has changed. Measured on `main` of every repo as of 2 Nov 2026,
including NHL94SNES after #382 and #383 and nhl-disasm-report after #65. Short names: 92G, 93G, 94G, 95G and 96G are
Genesis; 93S, 94S and 95S are SNES; 94PC and 95PC are DOS.

## TL;DR

1. **Names mostly agree already.** 93G, 93S, 94G and 94S share the name for almost every routine they have in
   common. Only 4 94S names conflict with 94G (see §5.3). The work left is file shape and the
   routines that have no partner name yet.
2. **One rule for every game** (§1). The same-year Genesis game decides the folder, and the names of that year's new
   features. A shared routine keeps the name of the earliest game that has it. Since those already agree, this is mostly
   about files. The SNES or PC sibling keeps its own name only for its own jobs (password, SPC, DOS menus).
   Data and banks follow the platform's earlier repo.
3. **Build the checks and the handoff kit first** (Stage A (§4)). That means a pairing check
   in the report next to MATCH, plus the same AGENTS.md, RULES.md, HANDOFF.md, Cursor rule and Claude agent files in
   every repo, so any tool can pick up any repo (§3). It also fixes a trap:
   94G merged six files on 31 Oct, and 95G, 95PC and the report still use the old file names. The old
   `video94` is now `middle94`, and the old `display94` is now `video94`.
4. **Then a light pass on 93G/93S/94G** (Stage B (§5)). Leave 93G alone. In 93S,
   move 17 routines back to their 93G module and re-cut 3 overloaded `hockey/` areas so each one maps to one 94G file
   (about 45 file moves). One shared rename to check.
5. **Then 94S** (Stage C (§6)). Move about 40 routines to their 94G folder, empty the overloaded
   `routines/hockey/` (227 files) into the 94G files those routines come from, then do the naming pass.
6. **Then 95G and 96G** (Stage D (§7)). Their names already follow 94G (883 of 1,715 labels in 95G).
   What's left is to update the old 94G file names in their docs and maps, extend the shared RAM order to them,
   and finish 96G's own naming against 95G.
7. **Later:** 95S once McMarkis finishes the segments (Stage E (§8)), 95PC with its naming
   rule updated to 94G/94S/95G and its multi-contributor lanes removed, since you're the only one on it now
   (Stage F (§9)), and 94PC once its disassembly is done (Stage G (§10)).
8. **Three decisions for you** (§12).

One step at a time, in this order. Each step is one PR (or one per repo), merged before the next one starts.
Hours are working time for the step, without the time a PR waits for your review.

| # | Step | Hours |
|---|---|---|
| 1 | A1 gates in the report (pairing check, crosswalk, baseline) | 3-4 |
| 2 | A2 handoff kit, one small PR per repo | 2 |
| 3 | A3 old 94G file names (95G, 95PC, 96G, 94G, report) | 1.5 |
| 4 | F0 95PC process for one owner | 0.5 |
| 5 | B1-B3 93S moves | 2 |
| 6 | C1-C3 94S known moves | 1.5 |
| 7 | C4 94S `hockey/` placement (about 8 units) | 3-4 |
| 8 | C6 94S subfolders (if yes) | 2 |
| 9 | C7 94S banks and data | 1.5 |
| 10 | D1, D3, D4 95G/96G maps, report, RAM order | 3 |
| 11 | F2b 95PC file split (if option A) | 3 |
| | **Structure total** | **about 25 hours, so 3 to 4 working days** |
| 12 | Naming: C5 (94S), D2 and D6 (95G/96G), F3 (95PC), clear matches only | about 2 days, plus your batch reviews |
| later | E 95S (McMarkis), G 94PC (after disassembly) | |

The moves are scripted and proven by MATCH plus the pairing check. Naming is the only open-ended part, because each
name needs evidence and the rule is never to guess. It's limited to the clear matches a script finds; anything unclear
stays on the Unsure lists.

## 1. Who decides what

Lineage (from the repos' own SEGMENT_AGENT files, plus what you told me): 92G → 93G → 94G → 95G → 96G on Genesis. 93S is a port of 93G.
94S is the 93S code base carrying the 94G features. 95S is a separate Visual Concepts code base. 94PC is 94G with 93S and
94S parts. 95PC is 94G/94S with 95G parts.

| Category | Decided by | Notes |
|---|---|---|
| Name of a routine that several games share | The earliest game that has it; 92G is the root | Already true across 92G-94S. A fix travels down the lineage ("fix the earliest repo first"). |
| Name of a feature new in year N | That year's Genesis game (94G for 94S/94PC, 95G for 95S/95PC) | e.g. shootout, cards, season, trade |
| Name of a platform-only job | The earlier repo on that platform (93S for 94S/95S, 94PC for 95PC), else what the code does | password, SPC, DMA queue, DOS menus |
| Same name, different job | The 92-style clash rule: the earlier meaning keeps the name | `BitstoPW` stays in 94S (password), it's `BackupRAM_Save` in 94G (SRAM) |
| Top folder or file | The same-year Genesis file (94G for 94S and 94PC; 95G for 95S and 95PC) | 95G files are subsystems (`engine/`, `front/`), not 94G files |
| Second-level folder (SNES) | The earlier SNES repo's area, once Stage B makes each 93S area map to one 94G file | optional, decision 1 |
| RAM names | Same as routine names | |
| RAM order | The merged order in `ram-order/ram_order_and_matches.md`, extended to 95G/96G | |
| Data files, assets, banks | The earlier repo on the same platform | already settled |
| Order inside a file | ROM order; the report re-sorts for display | your rule |
| History | `docs/name_map.csv` only, never comments | existing rule |

## 2. How we run it

Sources: the two x.com posts and the two articles they quote ("the model is the engine, the harness is the job"
by NO1ennn and "Loops and Graphs" by Hanako), read from the PDFs you attached, plus the YouTube link. The video is
Karpathy's "How I use LLMs" (February 2025), a general guide to using chat assistants. It doesn't cover agents,
loops or graphs, so the post that called it a harness masterclass oversold it, and a reply under the post says the
same. The only part that applies here is "use a thinking model for hard calls and a cheaper one for routine work",
which the model tiers below already cover. The "99% of engineers run 300+ agents" and "prompting is over" headlines
have no source. I left them out.

### 2.1 The checks come first

The articles say to write the check first, as something a program can fail. "The model says it is confident" doesn't count.
This work has one such check (MATCH) and needs three more. Build them in Stage A, before any moves.

| Gate | What fails it | Where |
|---|---|---|
| **MATCH** | any byte differs from the retail ROM | each repo, `tools/verify_all.sh` (exists) |
| **Scope** | the diff touches a file outside the unit's list. The list is the unit's folder, the bank `incsrc` lines that point at it, and `docs/name_map.csv` | new `tools/check_scope.py` in each SNES repo, given the unit's file list |
| **Pairing** | (a) a row of `known_pairs.csv` no longer pairs (one routine per 93S area, e.g. `checkcoll`, `PWtoBits`, `ShootoutWonBy`, `Fprint`); (b) the number of yellows that 94G doesn't explain goes up from `baseline.json`, for 94S vs 94G or 94S vs 93S | nhl-disasm-report, new `tools/test_pairs.py` |
| **Lineage** | a 94S name equals a 94G `name_map.csv` *old* name while 94G has the new name, and RULES.md has no exception for it (finds the `BitstoPW` kind of case automatically) | report, same script |

Only naming has no automatic check, so your review goes there.

### 2.2 The graph for this work

The four kinds of node from the article are splitter, worker, code node and gate. Two rules shape them here:
"if you can describe it without judge, decide or assess, it is code" and "cut by blast radius, not by folder".

```
splitter (code) ── per 94G file: the 94S routines whose callers or names point there
   │
   ├─ worker: collide ─┐   each in its own context, one 94G file + its 94S candidates,
   ├─ worker: stats   ─┤   one lens (placement OR naming, never both in one unit)
   ├─ worker: setup   ─┤
   └─ ...             ─┘
          │
   gates (code): MATCH → scope → pairing → lineage
          │ fail: send back that unit only (correction edge), max 3 tries, then the advisor
          ▼
   merge (code): regenerate report, update baseline.json
          │
   you: approve the PR (names only need a real read)
          │
   learning edge: each correction you make → one line in docs/RULES.md, which the splitter reads
```

Code nodes, not models: the placement proposal (the 94G file of a routine's callers), the 93S area to 94G file
crosswalk, call-order name candidates against 94G and 93S, the yellow counts, and the baseline compare. A model is
only needed to read a candidate's body and agree or disagree.

The unit is cut by 94G file, not by 94S folder. Cutting by 94S folder sends three workers through the same `hockey/` files.
Cutting by 94G file gives each worker one partner file to compare against and an output that doesn't overlap the others.

### 2.3 Which steps really depend on each other

The article's test: does the next step read the previous step's output? If not, there's no dependency and the two can run side by side.

* A1 (gates) and A2 (handoff kit) don't depend on each other. A3 (old 94G file names) doesn't depend on either.
* Stage B needs A1, so its moves are checked. C1 to C3 (94S moves) don't read B's output either, but **you asked for B first**, and
  B changes the 93S areas that C6's second level copies. So B runs first and C follows.
* C5 (94S naming) needs C4 (placement), because a name is judged against the 94G file the routine now sits in.
* D needs A3 (95G's origin maps use the old 94G file names) and works best after C, because 95G and 94S share the 94 names.
* F3 (95PC renames) waits for C5 and D5, because it copies their names. E waits for McMarkis's segments, and G waits for 94PC's disassembly.

### 2.4 The return path

When a unit fails a gate, only that unit goes back, with four things: the failing check's output, the file and line,
the scope line ("fix these files only, do not touch other units"), and the attempt number. After 3 failed attempts
the plan is wrong, not the worker, so it goes to the advisor. The article's point: sending the whole batch back
rewrites correct work, and the next version is different, not better.

### 2.5 Lanes by blast radius, not confidence

| Lane | Work here | Gate |
|---|---|---|
| Reversible, contained | moving routine files inside 94S, folding a local, bank file renames | MATCH + scope + pairing. You approve the merge without reading every file |
| Reversible, wide | renames used in many files, RAM equates, the shared `snes_regs.asm`, report generator changes, any change that "propagates down the lineage" to another repo | gates + your read of the diff |
| Never opens | NHL92Genesis edits, anything that changes retail bytes on main, force-push, rewriting merged history | no score lets it through |

Inside an open lane the gate weighs evidence in this order: the checks, then how this unit's tries went, then how
often this kind of work was reverted before. The worker's own opinion comes last.

### 2.6 Model tiers and the advisor

| Job | Claude | Cursor |
|---|---|---|
| Search, grep call sites, read docs (read-only) | Haiku | Composer |
| Moves, folding, gates, report regen (A, B, C1-C4, C6, D1) | Sonnet | Grok medium |
| Naming (C5, D2, D6, F), lineage exceptions | Sonnet, with the advisor | Grok 4.7 medium |
| Advisor: before a stage plan is fixed, after the same error twice, before a stage is called done | Opus | Grok 4.7 high |

The post's `claude --model sonnet --advisor opus` flag points to code.claude.com/docs/en/advisor. I couldn't check that
page from here, so try `claude --help` before relying on it. If the flag isn't there, a rule in AGENTS.md
("consult the advisor at these three moments") does the same job in both tools.

### 2.7 Night shift

The first article's job description fits almost word for word. A scheduled run, written down once:

> Every night, build 93G, 93S, 94G and 94S and confirm MATCH, regenerate the report offline, and run `test_pairs.py`.
> Read every failure, not only the count, and compare it with the night before. Post a morning report: what broke,
> what got worse and why, what got better. For each regression open a PR with the fix and a new `known_pairs.csv` row
> so it can't come back. Flag a flaky check separately. Do not merge or change anything on your own.

Before the first run, it writes `docs/nightly/schedule.md` and `report-template.md` for you to correct, as the article
recommends. Unapproved PRs show up again in the next report.

The files that make this work in either tool are in §3.

## 3. Handing off between tools

Goal: any repo can be picked up by Claude or Cursor on any day, depending on which one has tokens left, with no
state stuck in one tool's chat, memory or project folder.

### 3.1 What's there today

| Repo | AGENTS.md | Cursor rule | Claude agents | HANDOFF | RULES.md |
|---|---|---|---|---|---|
| NHL95PC | full rules (53 lines) | `.cursor/rules/main.mdc` | `equiv-worker` / `fixer` / `advisor` | yes | yes |
| 92G, 93G, 93S, 94G, 94S, 95G, 96G | credit section only (13 lines) | none | none | yes (not 92G) | none |
| 94PC, 95S, 96PC | credit + a little (18 lines) | none | none | yes | none |
| nhl-disasm-report | none | none | none | yes | none |

The working rules live in SEGMENT_AGENT.md, START_HERE.md, PROMPT.md and CONTRIBUTING.md, and each tool finds them
only if something tells it to look. NHL95PC is the template that already works: copy its shape.

### 3.2 The kit (same in every repo)

* **AGENTS.md is the one instruction file.** It has the read order (AGENTS → RULES → HANDOFF → the stage's section of the plan),
  the gates, the unit rule, the return rule, the three advisor moments and the risk lanes (§2.5). It names jobs, not models.
* **CLAUDE.md** says "Read and follow AGENTS.md" (already). **`.cursor/rules/main.mdc`** says the same, with `alwaysApply: true`
  and the Cursor model per job. **`.claude/agents/`** holds worker, fixer and advisor files with the Claude model per job.
  Switching tools never means editing AGENTS.md.
* **`docs/RULES.md`**: the authority table from section 1 for this repo's game, then the learned rules, one line each
  (`- date area: rule. (evidence)`), newest last. Either tool adds lines in the same PR as the fix.
* **`docs/HANDOFF.md` starts with a fixed "Now" block** so a cold start knows exactly where to begin:
  ```
  ## Now
  Stage / unit: C4 / stats          Branch: <name or none>
  Last MATCH: <sha>                 Gates: MATCH ok, pairing ok (unexplained 31)
  Next command: python3 tools/place.py --unit stats
  Open PRs: #nnn (waiting for review)
  ```
* **The plan lives in a repo**, not only in this project's shared folder, because Cursor can't see the folder. Put it at
  `nhl-disasm-report/docs/ALIGNMENT.md`, next to the report that checks it, and each repo's RULES.md links to it. The report's gate files
  (`known_pairs.csv`, `baseline.json`) live in nhl-disasm-report.
* **Units sized to one session.** One unit is one PR that one session can finish (one folder, one 94G file, or one
  function on 95PC). If credits run out mid-unit: push the branch, mark it `WIP` in the Now block, and stop. Never leave
  uncommitted work.
* **Before you switch:** the tool you're leaving updates the Now block and pushes. In the other tool you say
  "Read AGENTS.md and docs/HANDOFF.md, continue." The nightly run (2.7) flags any repo whose last MATCH SHA in the Now block
  is older than `main`, so a stale handoff shows up the next morning.
* **Don't depend on tool-only features.** The `--advisor` flag, subagents and Cursor's model picker are conveniences.
  The rule itself ("ask the advisor at these three moments") is plain text in AGENTS.md, so either tool can follow it.

## 4. Stage A: foundation (all repos)

| Step | What | Repos | Size |
|---|---|---|---|
| A1 | The gates from 2.1: `test_pairs.py` with `known_pairs.csv` and `baseline.json`, the lineage check, the area crosswalk, the "why yellow" tag, and `check_scope.py`. The report also reads `docs/history/name_map.csv` (93S keeps its map there, so 32 lineage rows are skipped today). | nhl-disasm-report, 93S, 94S | about half a day |
| A2 | The handoff kit from 3.2 in every disassembly repo; the plan copied to `nhl-disasm-report/docs/ALIGNMENT.md` | all | about half a day, one small PR per repo |
| A3 | **Replace the old 94G file names.** On 31 Oct 94G folded `checks94`, `assign94`, `input94`, `attract94`, `data94` and `display94` into `logic94`, `setup94`, `middle94` and `video94`. Watch out: the old `video94` is now `middle94`, and the old `display94` is now `video94`. Still on the old names: 95G `docs/FILE_ORIGINS.md`, `docs/function_origins.csv`, `tools/segmap95.json`, `tools/SEGMAP95.md`, `SEGMENT_AGENT.md`, `docs/WHY_95_MOVED.md`; 95PC `name_map_94.csv` (the `94_source_file` column), `segmap95pc.json`, `EXE_SEGMAP95PC.md`, `SEGMENT_AGENT.md` and two C comments; the report's `categories.json`, `classify_routines.js` and `routine_addrs.json`; 96G `docs/HANDOFF.md`; 94G `SEGMENT_AGENT.md` and `shortcalls.inc`. Regenerate the origin files with their scripts against the new 94G rather than editing them by hand. | 95G, 95PC, 96G, 94G, report | about half a day |
| A4 | Nightly check (2.7), with its schedule and report template written first for you to correct | report or a routine | small |

## 5. Stage B: 93G / 93S / 94G light touch

What I checked: every 93S routine against its 93G file, every 93S area against the 94G file its routines went to,
and every 94G rename against 93G and 93S.

### 5.1 93G: leave it as it is

`hockey93.asm` is big (6,718 lines, 195 labels). 94G split it into `setup94` (82), `collide94` (38), `hockey94` (26),
`replay94` (9) and a few more. That split is 94's history, and 93G mirrors 92G `hockey.asm`, so splitting it would
break the 92G lineage. Every 94G "the 93 name was wrong" rename has already been copied back into 93G (88 of them).
Only one is left: `IceRinkMap` → `HorRinkTiles` (5.3).

### 5.2 93S: two small passes

**B1. 17 routines sit outside their 93G module.** In most of these 93G and 94G agree, and 93S is the odd one out.
Move each back to its module's folder (as an area), except where an SNES-only job is the reason it moved:

| Routine | 93G / 94G file | 93S now |
|---|---|---|
| `chkatop`, `ChkShotStat` | penalty / penalty | stats |
| `ConvertByteToDigits`, `FinalizeTextBuffer` | hockey / setup | print |
| `AdvanceStringPtr` | penalty / penalty | print |
| `sfx` | middle / middle | sound |
| `updatesound` | video / video | sound |
| `CheckLateGameSong`, `newcheck` | hockey / hockey, collide | sound |
| `clearTeamStats` | hockey / setup | stats |
| `PrintGameInfo` | stats / stats | penalty/ticker |
| `dobar` | penalty | video/hud |
| `defaultsprites_0` | hockey / setup | video/objects |
| `forceblack`, `remap` | middle / middle | video/interrupts, video/dma |
| `waitjoy` | middle / middle | hockey/screens |
| `ReadPads` | sound93 (pad read in the Z80 file) | middle/input. **Keep**: the SNES reads pads in its own job |

**B2. Re-cut the mixed `hockey/` areas so each one maps to one 94G file.** Today `hockey/game`, `hockey/teams` and
`hockey/screens` are each split between two or three 94G files. For example, `hockey/game` holds 11 `hockey94`
routines, 5 `setup94` and 5 `collide94` (`Goal`, `ResetBench`, `forcepldata`...). Measured, 47 routines sit
outside their area's majority 94G file. Proposed areas inside `routines/hockey/`: `collide/`, `setup/`, `game/` (the
`hockey94` part), `replay/`, `title/`, `optsetup/`, `scout/`, plus the existing `password/` and `playoffs/` (both are `setup94`
already). These are file moves only, so MATCH proves the bytes, and the folder under `routines/` (the 93G module) doesn't change.
Afterwards the report's crosswalk is exact, and 94S can take the 93S area as its second level with no hand table.

**B3. Tables folder.** 93S keeps 7 small tables in `routines/tables/` (`Penaltylist`, `linelist`, `asstab`...), while 94S
keeps the same kind of table in `data/tables/`. Move the 93S ones to `data/tables/`, so both SNES repos have the same shape.

The resulting trees and before/after examples are in [folder_preview.md](folder_preview.md).

### 5.3 Names: 4 real conflicts

| Name | 94G | Recommendation |
|---|---|---|
| `IceRinkMap` (93G, 93S, 94S) | `HorRinkTiles` | Check the bytes in 93G. If it's the `SetHor` tile block, as 94G found, rename it in 93G, then 93S, then 94S (the earliest repo first). |
| `BitstoPW` (93S, 94S) | `BackupRAM_Save` | Keep it. The SNES saves by password, 94G saves to SRAM. Different jobs. |
| `SetupPauseScreen` (93S, 94S) | `Pausemode.pall` (a local) | Fold it into `Pausemode` in 94S if only `Pausemode` reaches it. 93S keeps the 93G shape. |
| `DrawTeamBlocks` (93S, 94S) | `PlayoffScreen.doteam` (a local) | Same as above. |

### 5.4 94G: no change

Its 31 Oct merge already matches 93G's module boundaries. 94G is the reference for Stage C, so it stays put.
The only 94G change is the comment and SEGMENT_AGENT fix in A3.

## 6. Stage C: 94S

Measured detail is in Appendix A. Summary: 260 of the 286 routines
found in all three games already sit in their 94G folder. 94S compared with 93S shows 100 "matched, other file"
routines, and 94G compared with 93S shows 106. That's almost the same set, so it's the reshuffle you already accept.

| Step | What | Size |
|---|---|---|
| C1 | Move the ~40 routines whose 94G file is known (26 found in all three games, plus 11 with only a 94G name: the stats screens, line editor, `PlayerCards`, `ShowThreeStars`...). Create `print/` (both parents have it), and `title/` once `TitleScreen` moves | 1 PR |
| C2 | Fold `SetupPauseScreen` and `DrawTeamBlocks` if they qualify (5.3) | small |
| C3 | Fix 94S HANDOFF's folder list, which still names `checks` | tiny |
| C4 | Empty `routines/hockey/`: 221 of its 227 files have no partner name. A script puts each one in the 94G file of its callers, and a worker checks one 94G file at a time (stats, period, setup, cards, title, optsetup, scout, the rest) | about 8 units |
| C5 | Naming pass on the ~525 routine names with no partner: call order against 94G first, then 93S. Unsure stays as is. Your review goes here | large, one unit per 94G file |
| C6 | (If decision 1 is yes) the 93S area as a second-level folder inside the 94S folders | moves only |
| C7 | Data: the bank names from `bank-names/bank_names_proposal.md`, SPA and frame labels | small to medium |

## 7. Stage D: 95G and 96G

**Where they stand.** 95G is one file per subsystem (`engine/`, `front/`), in ROM order. Mark Lesser re-filed 94's code
for 95 (`docs/WHY_95_MOVED.md`). That reorganisation is real game history, so its file shape stays. Names already follow 94G:
883 of 1,715 95G labels are 94G names, and of the routines matched to 94 by fingerprint, only 13 carry a different
name. 96G follows 95G's folders with extra splits (`logic96_ass`, `pause96_menu`). Of its 1,303 labels, 480 are 94G
names, 249 are 95G names and 556 are its own. Its `docs/align95_plan.md` covers the rest.

| Step | What | Size |
|---|---|---|
| D1 | After A3, regenerate 95G's `FILE_ORIGINS.md` / `function_origins.csv` against the current 94G | small |
| D2 | The 13 fingerprint-matched routines with non-94 names (`rtsskate`, `StatScrollStep`, `PeriodStatsTeam`, `SkipStatColumn`...): take the 94G name, or the 94G local name, where the body is the same | small |
| D3 | Report pairing for 95G: a 95G subsystem file holds routines from several 94G files, so a 95G yellow vs 94G is expected. Mark it "explained" when `function_origins.csv` names the 94 file, so only real misplacements count | part of the report work |
| D4 | Extend the merged RAM order to `ram95.asm` / `ram96.asm` (the 92-94 order is done) | medium |
| D5 | 95 features that 94S/94PC/95PC will copy from (season, trade, create, awards) get their names reviewed here first, because 95PC and 95S inherit them | your review |
| D6 | 96G: finish its naming against 95G (`align95_plan.md` Unsure list), with 95G names winning when the body is the same | medium |

## 8. Stage E: 95S (later)

95S is a separate Visual Concepts code base. It's still in segment layout (256 `bankCx_y000` slices, all MATCH),
and naming is under way (McMarkis; 607 names marked `94S+code`, 134 `94S`).
Nothing to do until the segments are finished and McMarkis agrees. When that happens:

* Layout as 93S and 94S: `src/banks/`, `src/routines/<module>/`, `src/data/`. The module follows 95G's subsystem file when the
  routine is a 95G routine, else the 94S folder for an SNES job.
* Names: 94S for SNES jobs and shared code (it reuses 94S names already), 95G for 95 features, else what the code does.
* Add 95S to the report as soon as its layout exists, so that the pairing check covers it.

Until then, the one useful step is to share RULES.md and the section 1 table with McMarkis so new names follow it.

## 9. Stage F: 95PC

You're the only one working on 95PC now. Its AGENTS.md, `docs/LANES.md` and `docs/LANES_CURRENT.md` still split the
work into lane 1 (Mhopkinsinc, 001-037), lane 2 (StaticEck2026, 038-066) and lane T (you), and the board in `docs/board/`
is for talking between contributors. Process-wise it's still the furthest along: 977 of 1,084 functions match byte
for byte, and it has RULES.md, an advisor and the functional track.

* **F0 (with A2): simplify the process for one owner.** Drop the lane ownership and the board from AGENTS.md. Keep the
  parts that are really "one unit, one session" rules: one C file per unit, the timebox, `draft_history.csv`, UNSURE.md, the
  generated files, and PR titles. LANES_CURRENT.md becomes the work queue, with no names on it. Keep the files, so history
  isn't lost, but mark them as archive. Also update the README status line, which still says McMarkis is working on the C decompilation.
* **F1 (with A3): fix the old 94G file names** in `name_map_94.csv`, `segmap95pc.json`, `EXE_SEGMAP95PC.md` and `SEGMENT_AGENT.md`.
* **F2: naming rule.** Today it says "93G first, then 94G, NHL95Genesis is a loose reference only". Change it to
  the 94G name when the body matches (93G and 94G names almost always agree, so this rarely changes anything), the
  94S name for code shared with the SNES 94, the 95G name for 95 features (season, trade, create, awards), and 95PC's own
  name for DOS jobs. 969 of its 1,490 mapped names are `PC-new`, so the 95G step mostly applies to the front end.
* **F2b: file split and repo shape.** Today the code is in `src/cseg01/` and `src/c/`, in folders named `NNN_ADDR_topic`. I propose
  `src/c/{engine,front,pc,lib}/<module>` with matching asm, where each module is named after the 95G file it pairs with
  (`engine/logic`, `engine/skate`, `front/trade`...), and the link order stays in `segments.txt`. Options and cost are in
  [folder_preview.md](folder_preview.md). AGENTS.md says the `NNN_*` names stay, so this is your call (decision 3).
* **F3: renames.** Still go through `docs/pending_renames.txt` and the progress workflow, so the generated files stay right.
  With no one else editing the C, renames can go in large batches, one 95G subsystem per unit. They wait for C5 and D5, because 95PC copies
  those 94S and 95G names. Put them between C/D and E.
* **Report:** add 95PC once the report can read its C and NASM tree (a new parser, medium). Until then, the lineage
  check runs against `name_map_94.csv`.

## 10. Stage G: 94PC (after disassembly)

94PC has stopped at seg006, and the overlays aren't started. Agreed: don't align it now. Two cheap things meanwhile:

* Write the naming rule into its RULES.md now so new names are already right: 94G when the body matches, 93S or 94S for
  the parts taken from the SNES ports, else 95PC's name for the same DOS job, else MSC/EACLIB names.
* Add it to the report when the overlays are source.

## 11. Report changes, all stages

| When | Change |
|---|---|
| A1 | Gates (`test_pairs.py`, `known_pairs.csv`, `baseline.json`, the lineage check), 93S area crosswalk, "why yellow", read `docs/history/name_map.csv` |
| A3 | Categories and routine addresses on the current 94G files |
| B2 | Crosswalk becomes exact (one 94G file per 93S area); new baseline |
| C | Baseline lowered after each C step; 94S vs 94G yellows should fall from 58 by about the number of routines moved |
| D3 | 95G/96G "explained by origin" from `function_origins.csv` |
| E, F, G | New parsers for 95S (SNES layout, easy once it exists), 95PC (C plus NASM) and 94PC (MZ plus overlays) |

Display order stays as you set it: the right pane follows the comparison game's folder order.

## 12. Decisions for you

### Decision 1: should 94S get 93S area subfolders under its 94G folders? (step C6)

**The question.** 94S's top folders are named after 94G files (`collide/`, `setup/`, `stats/`...), and each holds flat files.
93S has a second level: each 93G module is split into areas (`hockey/collisions/`, `logic/assignments/`, `penalty/ticker/`).
The question is whether 94S also gets that second level.

**If yes, this changes:**
* Inside each 94S folder, routines that come from a 93S area go into a subfolder with that area's name, for example
  `routines/logic/assignments/asswingd.asm` and `routines/collide/collisions/checkcoll.asm`. Routines with no 93S counterpart
  (the 94 features, the SNES engine) stay directly in the folder.
* Only files move. The bank files' `incsrc` paths are updated, no bytes change, and MATCH proves it.
* The report's file key already stops at the first folder under `routines/`, so 94S vs 94G pairing doesn't change.
  94S vs 93S pairs by area, so a 94S routine shows in the same place as its 93S routine.
* Waits for Stage B2, so the 93S area names are clean before 94S copies them. Roughly 250 file moves, done one folder per PR.

**If no:** 94S stays flat inside each 94G folder. The report still pairs 94S with 93S through the crosswalk built in A1.
You just won't see the 93S grouping when you browse the 94S tree.

**My recommendation:** yes. Both "looks like 94G" and "shows where it came from in 93S" hold, at the cost of moves only.

### Decision 2: should the two 93S passes in Stage B go ahead? (steps B1 and B2)

**The question.** You said the 93G → 93S differences are fine as they are. Stage B still proposes two light changes to 93S
folder placement. Nothing in 93G or 94G moves.

**B1 changes:** 17 routines go back into the folder of their 93G module. Today `chkatop` and `ChkShotStat` (93G and 94G
`penalty`) are in 93S `stats/`, and `sfx` (93G and 94G `middle`) is in 93S `sound/`. The full list is the table in §5.2.
`ReadPads` stays where it is, because the SNES reads pads as its own job. These are file moves only.

**B2 changes:** three areas inside 93S `routines/hockey/` that mix routines from two or three 94G files are re-cut, so each area
holds routines from one 94G file:
* `hockey/game/` (23 files) keeps its 11 `hockey94` routines. 5 go to a new `hockey/setup/` and 5 to a new `hockey/collide/`.
* `hockey/teams/` (27) splits between `hockey/collide/` and `hockey/setup/`.
* `hockey/screens/` (28) splits into `hockey/setup/`, plus small `title/`, `optsetup/` and `scout/` areas.
* `password/`, `playoffs/` and `replay/` already map to one 94G file and stay.

About 45 file moves in total. The module folder (`hockey/`) and every byte stay the same.

**Why bother:** the report can then map each 93S area to exactly one 94G file with no hand-made table, so 94S vs 93S
comparisons stop showing false "moved" marks. Decision 1's subfolders also copy clean names.

**If no:** 93S stays as is. The crosswalk uses the area's majority 94G file, so a few routines in mixed areas still
show as moved when comparing 94S with 93S.

**My recommendation:** do both. They're small, they're moves only, and they're the only 93S change in the whole plan.

### Decision 3: 95PC naming rule and process (steps F0 and F2)

**The question.** 95PC's AGENTS.md says names come from "93G when the body matches, else 94G, else behaviour", with
NHL95Genesis as "a loose reference only". It also splits the work into lanes for Mhopkinsinc and StaticEck,
with a contributor board. You've told me 95PC is a hybrid of 94G/94S and 95G, and that you're the only one working on it.

**F2 (naming) changes:** the rule becomes, in order:
1. the 94G name when the body matches (this rarely changes a name, because 93G and 94G agree on almost all shared names);
2. the 94S name for code 95PC shares with SNES 94;
3. the 95G name for 95 features: season, trade, create player, awards, and the new menus that 95G has;
4. 95PC's own name for DOS-only jobs (file I/O, memory, sound cards, the PC front end).

Most of the effect is on the 969 names marked `PC-new`, where a 95G routine does the same job. Renames go
through `pending_renames.txt` after the 94S and 95G naming passes (C5, D5).

**F0 (process) changes:** AGENTS.md drops lane ownership and the board. `LANES_CURRENT.md` becomes a plain work queue,
the lane and board files are marked as archive (not deleted), and the README status line is updated. Everything that's really a
per-unit rule stays: one C file per unit, the 8-10 minute timebox, `draft_history.csv`, UNSURE.md, generated files that aren't
hand-edited, and PR titles.

**If no:** 95PC keeps 93G-first names and stays apart from the 95G names. The report would show more 95PC routines
unmatched against 95G once 95PC is added.

**F2b (file split) changes:** the 95PC folders are named by subsystem and module instead of segment number and address,
so its tree looks like 95G's `engine/` and `front/`. See [folder_preview.md](folder_preview.md) for option A (rename and group)
and option B (keep as is).

**My recommendation:** yes to F0 and F2, and option A for F2b, done after F0 while no one else has open work in the tree.

No PR opens until you say go.

---

# Appendix A: 94S measurements

## A1. How much 94S comes from 93S, and how much from 94G

The two kinds of inheritance are different, and that is why the question felt confusing.

| Kind | Comes from | Evidence |
|---|---|---|
| **Code lineage** (the 65816 instructions) | 93S | Game logic was named by matching opening instructions and small immediates to 93S routines (`docs/HANDOFF.md`). Player frames below 225 keep the 93S numbers. The assignment table is the 93S/94G numbering. 808 entries in `docs/name_map.csv` are sourced `93S`, 306 `94G`. |
| **Design lineage** (features, screens, file structure) | 94G | Shootout, player cards, line editor, crowd meter, three stars, matchups, scouting rewrite. 38 94S routines have only a 94G name, and 27 of them already sit in the matching 94G folder. |
| **Engine** | neither | Bank `$80` (NMI/IRQ, DMA queue, heap, SPC sequencer, decompressors, sprite cache) is new. 1,690 94S symbols have no partner in either game; most are this engine, its RAM, and asset labels. |

94S symbol counts by kind (auto labels left out):

| 94S area | same name in 93S and 94G | 93S only | 94G only | neither |
|---|---|---|---|---|
| routines | 286 | 33 | 38 | 525 |
| RAM (`ram94s.asm`) | 314 | 90 | 50 | 471 |
| data (text, tables, teams, frames) | 150 | 27 | 16 | 482 |
| data/gfx | 6 | 14 | 146 | 212 (+977 auto `SpriteFrame`) |
| hardware registers (`inc/`) | 0 | 207 | 0 | 0 |

The 33 "93S only" routines are mostly SNES jobs 94G does not have (password `PWtoBits`/`DecodePW`, `SPCUpload`,
`QueueTextDMA`, `ReadPads`, `marktextlo/hi`). They should keep the 93S name.

## A2. Where 93S and 94G pull 94S different ways (measured)

### Names: 4 real conflicts (detail)

| 94S now (93S name) | 94G name | Recommendation |
|---|---|---|
| `BitstoPW` | `BackupRAM_Save` | Keep `BitstoPW`. 94S saves by password like 93S; 94G renamed it because 94G saves to SRAM. Different job, so the 93S name is right. |
| `SetupPauseScreen` | `Pausemode.pall` (a local of `Pausemode`) | Follow 94G: fold into `Pausemode` as `.pall` if only `Pausemode` reaches it. If other routines call it, keep the global name. |
| `DrawTeamBlocks` | `PlayoffScreen.doteam` (local) | Same as above. |
| `IceRinkMap` (data) | `HorRinkTiles` | Check the bytes. If it is the `SetHor` bitmap tile block, as 94G found, rename it. |

### Folders: about 40 routines in the wrong folder for 94G

* 26 routines that exist in both games are not in their 94G file. Mostly they are in `hockey/` but belong in
  `setup` (`getname`, `FormatPlayerNumInitial`, `ClearRosterName`, `InitScoutingDisplay`, `FinalizeTextBuffer`),
  `period` (`StatsReport`, `DisplayStats`), `title` (`TitleScreen`), `replay` (`getpzjoy`), `collide` (`Goal`), and so on.
* 11 routines with only a 94G name are in the wrong folder: `CrowdMeterScreen`, `LineEditor`, `LineEditorExit`,
  `PenaltySummaryScreen`, `PlayerStatsScreen`, `ScoringSummaryScreen` and `ShowScores` belong in `stats`,
  `PeriodStatsScreen` in `period`, `PlayerCards` in `cards`, and `ShowThreeStars` in `setup`.
* `print94.asm` has no 94S folder. The 8 to 12 print routines (`Fprint`, `ConvertByteToDigits`, `AdvanceStringPtr`...)
  sit in `middle/`. 93S has `routines/print/` too, so both parents agree on this one.
* 94G files with no 94S folder yet: `print`, `title`, `menu`, `records`, `goalie`, `onetimer`, `fourway`, `sram`,
  `checksum`, `graphics`, `frames`. Create a folder only once a routine is shown to be that file's job.
  `sram`, `checksum` and `fourway` probably stay empty: 94S uses passwords and the 5-pad multitap.

### `routines/hockey/` is the catch-all

94G `hockey94.asm` has 28 labels. 94S `routines/hockey/` has 227 files, and 221 of their names have no partner.
They are mostly the pause menu, stats pages, line editor, password and title helpers. In 94G those live in
`stats94`, `period94`, `setup94`, `cards94`, `title94` and `optsetup94`, which have low 94S coverage today
(cards 5 of 84 labels, optsetup 1 of 52, title 2 of 71, stats 26 of 94). Most of the "file shape" work is here.

### Second-level folders: the one real shape conflict

93S splits each 93G module into areas (`hockey/collisions`, `hockey/password`, `logic/assignments`, `penalty/ticker`...).
94G is flat files. Many 93S areas map onto one 94G file (measured from where their routines sit in 94G):

| 93S area | 94G file |
|---|---|
| hockey/collisions, hockey/teams (most) | collide94 |
| hockey/password, hockey/playoffs, hockey/screens (most) | setup94 |
| hockey/replay | replay94 |
| print | print94 |
| video/dma, video/rink (text queue, scroll) | middle94 |
| logic/*, penalty/*, middle/* | logic94, penalty94, middle94 (same module) |

That table is what lets both pulls hold at once: top folder from 94G, second level from 93S.

### RAM order: done

`ram-order/ram_order_and_matches.md` already set one merged order (92G, then 93G, 94G, 93S, 94S).
93S vs 94S is 0 out of order. 94G vs 94S has 8 left, all 94G `rs` layout moves. No more work here except keeping new
equates in that order.

### Data and banks: SNES shape, already settled

94S `data/` follows 93S (one asset per file, `teamdata94s`, `frames94s`, `data/text/`). That is the accepted
93G to 93S difference, and the report already pairs `teamdata94s` with `teamdata94`. Banks are SNES-only and follow the
shared vocabulary in `bank-names/bank_names_proposal.md`.

