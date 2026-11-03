# Aligning 94S with 93S and 94G: analysis and plan

Analysis only. Nothing in any repo was changed. Sources: NHLPA93Genesis `c2d8bae`, NHLPA93SNES `13c8848`,
NHL94Genesis `25a26cd`, NHL94SNES `646937f` (after #382 and #383), nhl-disasm-report `cd72b38` (after #65).
Counts come from a script over every global label and `=` equate in each `src/` (segacd skipped),
matched the way the report matches them: lowercase names, plus the 94G `name_map.csv` lineage.

## 1. The short answer

The pull between 93S and 94G is much smaller than it looks, and it is not about names.

* **Names already agree.** 93S kept the 93G names (its history map has 32 renames), and 94G mostly kept them too.
  Of the 94S symbols that have a counterpart in both games, 756 have the same name in all three. Only **4**
  94S names are a 93 name that 94G later changed (table in section 3).
* **Folders already mostly follow 94G.** Of the 286 94S routines that exist in both 93S and 94G, 260 sit in
  the folder named after their 94G file. 79 of those follow 94G where 93S puts them somewhere else
  (for example the 31 collision routines that are `hockey/collisions` in 93S and `collide94.asm` in 94G).
* **The report already shows this.** 94S vs 93S has 100 "matched, other file" (yellow) routines.
  94G vs 93S has 106. Those are almost the same set: they are the 93G to 94G reorganisation you already accept.
* **What is really left** is the 94S code that has no partner name yet (about 525 routine names, mostly in
  an overloaded `routines/hockey/`), a few 94G files that 94S has no folder for, and a report that pairs
  94S folders with 93S *top* folders only.

So the recommendation is one rule per category, with 94G deciding the shape and 93S deciding nothing new:

> **94S looks like 94G** (folders, file names, which file a routine lives in, names of 94 features), **inherits
> 93S only where 94G is silent** (SNES-only code, data layout, banks, the SNES jobs that 94G does not have),
> and **uses the 93S area as a second level** so the 93S pairing stays visible.

This keeps your two accepted baselines intact: 94S vs 93S then differs exactly by "93G to 94G" plus "93G to 93S",
and 94S vs 94G differs only by "Genesis to SNES".

## 2. How much 94S comes from 93S, and how much from 94G

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

## 3. Where the two pulls conflict

### Names: 4 real conflicts

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

## 4. Who is authoritative for what

| Category | Authority | 93S role |
|---|---|---|
| Top routine folder (`routines/<x>/`) | 94G file the routine is in | none |
| Second-level folder | 93S area the routine comes from (optional, see decision) | the area name |
| Routine name, 94 feature | 94G | none |
| Routine name, shared with 93 | already identical in all three; if 94G renamed it, 94G wins unless the 94S job is the 93S job (`BitstoPW`) | name kept only for SNES jobs |
| Locals vs globals (routine boundaries) | 94G (`Pausemode.pall`) | none |
| SNES-only job (password, SPC, DMA queue, pads) | 93S name and 93S folder for that job | authoritative |
| SNES engine with no parent | name from what it does, folder by job (#383 rule) | folder vocabulary |
| RAM names | as today (93S where 94G is the same, 94G for 94 fields) | shared |
| RAM order | merged order (already applied) | shared |
| Data files, assets, text tables | 93S shape | authoritative |
| Banks (file names, order) | ROM order, shared bank vocabulary | authoritative |
| Order of routines inside a file | ROM order (the report re-sorts for display) | none |

Where a name has to differ, the other game's name goes into `docs/name_map.csv`, never into a source comment
(your existing rule).

## 5. How the report should pair them

The matching itself needs no new aliases: names already agree. Three changes make the pairing honest.

1. **94S vs 94G:** keep the current key (`routines/<folder>` pairs `<folder>94.asm`). After phase 2 a yellow here
   means a real misplacement.
2. **94S vs 93S:** pair a 94S routine with the 93S *area*, through the crosswalk in section 3, not with the 93S top
   folder. Build the crosswalk in `generate.py` from where each 93S area's routines live in 94G (majority vote, at
   least 60%), so nobody keeps a hand table. Then `collide/checkcoll` vs `hockey/collisions/checkcoll` counts as the same
   place. A 94S yellow vs 93S is then only shown when 94G also disagrees with 93S, which is the accepted baseline.
3. **A "why yellow" tag:** for each yellow 94S routine, say whether 94G explains it (94G moved it too) or not.
   Unexplained yellows are the to-do list.

Display order stays as #65 made it: the 94S groups follow the comparison game's folder order.
Smaller: the report reads `docs/name_map.csv`, but 93S keeps its map in `docs/history/name_map.csv`. Its 32 rows
barely matter now, but the report should read both paths so lineage is not silently lost.

## 6. Phased plan

Each phase is its own PR (or a few), builds MATCH before every commit, and regenerates the report at the end. Units inside a phase are cut by 94G file (section 7.2).

| # | Phase | Repo | Scope |
|---|---|---|---|
| 0 | Write the authority table (section 4) into `docs/RULES.md`, and the gates, lanes and return rule (section 7) into AGENTS.md | 94S, 93S, 94G | Small, doc only |
| 1 | Gates first: report crosswalk pairing, "why yellow" tag, `test_pairs.py` with `known_pairs.csv` / `baseline.json`, the lineage check, and `check_scope.py` in the SNES repos (section 7.1). Runs alongside phases 2 and 3 | report, 93S, 94S | Medium, about 1 day |
| 2 | Move the ~40 known-misplaced routines into their 94G folder; create `print/`, `title/`, `period/` contents | 94S | Small, 1 PR. 94S vs 94G yellow (58 now) should drop by about the number moved |
| 3 | Resolve the 4 name conflicts (fold the 2 locals, check `IceRinkMap`) | 94S | Small |
| 4 | Empty out `hockey/`: place each 94S-only routine by the 94G file of its callers (the neighbour rule). A script proposes and a worker checks one target folder at a time | 94S | Medium. 221 files, about 8 units (stats, period, setup, cards, title, optsetup, scout, the rest) |
| 5 | Naming pass on the ~525 unpartnered routine names: call order against 94G first, then 93S. Unsure stays as is | 94S | Large, one unit per 94G file. Your review goes here |
| 6 | (If you say yes) add the 93S area as a second-level folder inside 94S `logic`, `penalty`, `middle`, `video`, `collide`, `setup` | 94S | Medium, moves only |
| 7 | Data: `IceRinkMap` follow-up, bank renames from the bank-names proposal, SPA/frame labels | 94S, 93S | Small to medium |

Phases 2, 3 and 4 are mechanical and low-risk (moves only, MATCH proves the bytes). Phase 5 is the only step without an
automatic check, so that is where your review matters.

## 7. How we run it

Sources: the two x.com posts and the two articles they quote ("the model is the engine, the harness is the job"
by NO1ennn and "Loops and Graphs" by Hanako), read from the PDFs you attached, plus the YouTube link. The video is
Karpathy's "How I use LLMs" (February 2025), a general guide to using chat assistants. It doesn't cover agents,
loops or graphs, so the post that called it a harness masterclass oversold it, and a reply under the post says the
same. The only part that applies here is "use a thinking model for hard calls and a cheaper one for routine work",
which the model tiers below already cover. The "99% of engineers run 300+ agents" and "prompting is over" headlines
have no source. I left them out.

### 7.1 The checks come first

The articles say to write the check first, as something a program can fail. "The model says it is confident" doesn't count.
This work has one such check (MATCH) and needs three more. Build them before phases 2 to 7.

| Gate | What fails it | Where |
|---|---|---|
| **MATCH** | any byte differs from the retail ROM | each repo, `tools/verify_all.sh` (exists) |
| **Scope** | the diff touches a file outside the unit's list. The list is the unit's folder, the bank `incsrc` lines that point at it, and `docs/name_map.csv` | new `tools/check_scope.py` in each SNES repo, given the unit's file list |
| **Pairing** | (a) a row of `known_pairs.csv` no longer pairs (one routine per 93S area, e.g. `checkcoll`, `PWtoBits`, `ShootoutWonBy`, `Fprint`); (b) the number of yellows that 94G doesn't explain goes up from `baseline.json`, for 94S vs 94G or 94S vs 93S | nhl-disasm-report, new `tools/test_pairs.py` |
| **Lineage** | a 94S name equals a 94G `name_map.csv` *old* name while 94G has the new name, and RULES.md has no exception for it (finds the `BitstoPW` kind of case automatically) | report, same script |

Only naming has no automatic check, so your review goes there.

### 7.2 The graph for this work

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

### 7.3 Which steps really depend on each other

Phase 1 (report gates) does not read the output of phases 2 or 3, and phases 2 and 3 do not read each other.
So 1, 2 and 3 can run side by side. Phase 4 needs the gate from phase 1. Phase 5 needs phase 4, because a name is
judged against the 94G file the routine now sits in. Phases 6 and 7 can go any time after phase 4.

### 7.4 The return path

When a unit fails a gate, only that unit goes back, with four things: the failing check's output, the file and line,
the scope line ("fix these files only, do not touch other units"), and the attempt number. After 3 failed attempts
the plan is wrong, not the worker, so it goes to the advisor. The article's point: sending the whole batch back
rewrites correct work, and the next version is different, not better.

### 7.5 Lanes by blast radius, not confidence

| Lane | Work here | Gate |
|---|---|---|
| Reversible, contained | moving routine files inside 94S, folding a local, bank file renames | MATCH + scope + pairing. You approve the merge without reading every file |
| Reversible, wide | renames used in many files, RAM equates, the shared `snes_regs.asm`, report generator changes, any change that "propagates down the lineage" to another repo | gates + your read of the diff |
| Never opens | NHL92Genesis edits, anything that changes retail bytes on main, force-push, rewriting merged history | no score lets it through |

Inside an open lane the gate weighs evidence in this order: the checks, then how this unit's tries went, then how
often this kind of work was reverted before. The worker's own opinion comes last.

### 7.6 Model tiers and the advisor

| Job | Claude | Cursor |
|---|---|---|
| Search, grep call sites, read docs (read-only) | Haiku | Composer |
| Moves, folding, gates, report regen (phases 2-4, 6) | Sonnet | Grok medium |
| Naming (phase 5), lineage exceptions | Sonnet, with the advisor | Grok 4.7 medium |
| Advisor: before a phase plan is fixed, after the same error twice, before a phase is called done | Opus | Grok 4.7 high |

The post's `claude --model sonnet --advisor opus` flag points to code.claude.com/docs/en/advisor. I couldn't check that
page from here, so try `claude --help` before relying on it. If the flag isn't there, a rule in AGENTS.md
("consult the advisor at these three moments") does the same job in both tools.

### 7.7 Night shift

The first article's job description fits almost word for word. A scheduled run, written down once:

> Every night, build 93G, 93S, 94G and 94S and confirm MATCH, regenerate the report offline, and run `test_pairs.py`.
> Read every failure, not only the count, and compare it with the night before. Post a morning report: what broke,
> what got worse and why, what got better. For each regression open a PR with the fix and a new `known_pairs.csv` row
> so it can't come back. Flag a flaky check separately. Do not merge or change anything on your own.

Before the first run, it writes `docs/nightly/schedule.md` and `report-template.md` for you to correct, as the article
recommends. Unapproved PRs show up again in the next report.

### 7.8 Files that hold it together (same in Cursor and Claude)

* `AGENTS.md`: the jobs, the gates, the three advisor moments, the return rule. CLAUDE.md and `.cursor/rules` point to it.
* `docs/RULES.md`: section 4's authority table plus the learned rules. The splitter reads it, not just the workers:
  the article puts the learning edge in "the brief that shapes how the work gets cut".
* `docs/HANDOFF.md`: where each phase stands, so either tool can pick it up.
* nhl-disasm-report `tools/known_pairs.csv` and `baseline.json`: the pairing gate's memory.

## 8. Decision for you

Should 94S get 93S area subfolders under its 94G folders (phase 6)? I recommend yes: 94G stays the top-level shape,
and 94S vs 93S pairs by area instead of showing as moved. The alternative is flat 94G folders only, with the report
crosswalk carrying the 93S pairing alone.
