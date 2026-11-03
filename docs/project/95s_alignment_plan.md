# NHL95 SNES (95S) alignment plan

Plan only: no repo changes until Abdul approves. Written 2026-11-03. Runs on the harness in [HARNESS.md](HARNESS.md);
supersedes Stage E in [alignment_plan_all_games.md](alignment_plan_all_games.md) §8.

## TL;DR

95S builds to MATCH and every one of its 256 segments is source, so it is ready to move into the aligned layout. The rule is
the one used for 94S: **95G decides the folder shape and the names; 94S decides only where 95G has nothing** (SNES-only
engine jobs, data, assets, banks). The work runs in six phases on branch `claude/project-thread-ggw7zu`: kit and gates first,
then the report, an inventory script, scripted moves, naming, RAM. Each phase ends in a PR Abdul reviews; nothing else
needs him. Both decisions are settled (§10): folders mirror 95G for now, and alignment wins over the existing names.

## 1. Where 95S stands (checked 2026-11-03, `main` at `de232e3`)

| Item | State |
|---|---|
| Build | `build.sh` and `tools/verify_all.sh` MATCH (SHA-1 `0b939f26...`), every segment also builds alone from `src/stubinc/` |
| Layout | 256 flat `src/bankCx_y000.asm` slices, plus `ram95s.asm`, `frames95s.asm`, `inc/` |
| Names | `docs/name_map.csv` has 9,405 rows: 5,014 auto (`new`), 2,960 named from the code, about 1,000 from 94S, 117 from 95G. About 4,470 labels in source |
| Kit | AGENTS.md (credit present), START_HERE, SEGMENT_AGENT, PROMPT, CONTRIBUTING, `docs/HANDOFF.md`. No `docs/RULES.md`, no `.cursor/rules/`, no scope check |
| Branch | no `claude/project-thread-ggw7zu` yet |
| Report | `generate.py` knows 93S and 94S only; 95S is not in the pairing gate |
| Code base | a separate Visual Concepts engine: the unpacker, transfer queues and sound driver are not 94S code, so 94S names need a purpose match, not a byte match |

## 2. Target shape

| Part | Rule | 95S result |
|---|---|---|
| Routines | top folder from the 95G file the routine's 95G partner lives in | `src/routines/<95G file key>/<Routine>.asm`, one routine per file as in 94S. 95G keys: engine (`collide`, `faceoff`, `fourway`, `goal`, `input`, `lines`, `logic`, `middle`, `pause`, `penalty`, `players`, `playoff`, `replay`, `setup`, `skate`, `video`), front (`awards`, `create`, `crowd`, `injury`, `records`, `scout`, `season`, `shootout`, `stats`, `summary`, `title`, `trade`), and the top files (`main`, `hockey`, `control`, `display`, `graphics`, `schedule`, `sram`, `teamdata`, `frames`, `credits`) |
| No 95G partner | the 95G file of its callers (majority, by script) | same folders |
| SNES-only engine job | the 94S folder for that job | `video`, `sound`, `decompress`, `middle`, `main` |
| Banks | 94S style, ROM order, named by content | `src/banks/bC0_engine_sound.asm` ... `bCF_sound_frames.asm` (16 files, the `include` lists) |
| Data and assets | 94S style, one asset per file | `src/data/{tables,gfx,sound,text}/` |
| RAM | merged order (`ram-order/`), extended to 95G | `ram95s.asm` stays one file, reordered and renamed |
| History | `docs/name_map.csv` only, never source comments | |

Routine folders keep 95G's `engine/` and `front/` level (decision 1).

## 3. Phase 0: kit and gates (Sonnet; one PR)

1. Create `claude/project-thread-ggw7zu` from `main`.
2. AGENTS.md: keep the credit section and the segment history pointer; add the repo's role, the gates (§4), units and the
   return rule, lanes and model tiers, copied from the 94S kit and adjusted.
3. `docs/RULES.md`: the authority table (as 94S) plus a "This repo" section written from §2, and an empty "Learned".
4. `.cursor/rules/main.mdc` (one line: read AGENTS.md); CLAUDE.md already does this.
5. `tools/check_scope.py`: new (HARNESS lists it, but no SNES repo has it yet). Fails when a commit's diff touches a file
   outside the unit's list. Reuse it in 93S and 94S later.
6. `docs/HANDOFF.md`: a new "Alignment" section at the top that each PR keeps current. START_HERE and SEGMENT_AGENT stay as the
   segment history and point to it.

## 4. Gates

| Gate | Fails when | Phase |
|---|---|---|
| MATCH (`tools/verify_all.sh`) | a byte differs | every unit |
| Scope (`tools/check_scope.py`) | the diff leaves the unit | every unit |
| Pairing (report `tools/gate.sh`) | a known 95S pair stops pairing, or yellows grow past the 95S baseline | from phase 1 |
| Inventory diff | a routine is lost, doubled or changes size between the inventory and the moved tree | phase 3 |
| Comments (`tools/check_comments.py`, already in the repo) | another game's name appears in a source comment | every unit |

## 5. Phase 1: put 95S in the report first (Sonnet; wide lane, Abdul reads)

Add `('95S', 'NHL95SNES', 'snes', 'nhl95snes.asm')` to `generate.py` with a segment-layout reader, so the pairing gate covers 95S
before anything moves. Seed `known_pairs.csv` with the 95S rows of `name_map.csv` tagged `genesis` (pairs with 95G) and `94S`
(pairs with 94S), and record `baseline.json`. Every later unit is checked against this baseline.

## 6. Phase 2: inventory (script, Haiku runs it; checkpoint 1)

A script, not a model, writes `docs/routines95s.csv`: address, size, label, callers, current name and source tag, proposed
folder, and the rule that placed it (95G partner, callers, SNES job, or UNSURE). Its rules apply in order:

1. 95G partner from `name_map.csv` (`genesis` tags) or the same name in a 95G file: that 95G file.
2. SNES-only job (NMI/IRQ, DMA and HDMA queues, the unpacker at `$C581E1`, SPC upload, map-set loaders): the 94S job folder.
3. Callers: the folder most of its callers are in, repeated until nothing changes.
4. Else UNSURE, listed in HANDOFF, placed by hand at checkpoint 1.

Abdul reviews one summary table (routines per folder, the UNSURE list) before any move. This is the plan's main review point.

## 7. Phase 3: scripted moves (Sonnet; one PR per step)

Moves never change bytes, so MATCH plus the inventory diff proves them. One lens per step.

| Step | Unit | Change |
|---|---|---|
| 3a | one bank | 16 segment groups to `src/banks/bCx_*.asm`; segments' code stays in place |
| 3b | one 95G folder | routines out of the banks into `src/routines/<key>/`, from `routines95s.csv` |
| 3c | one data kind | tables, gfx, sound, text to `src/data/` |
| 3d | one pass | drop `src/stubinc/` and the per-segment checks once nothing uses them; `verify_all.sh` builds the whole ROM |

The move script reads the CSV and `main`, so when other PRs land on `main` the branch is regenerated by re-running the script
on the new `main`, not by rebasing hand edits. New names that land on `main` meanwhile are still checked in phase 4.

## 8. Phase 4 to 6

**Phase 4, naming (Sonnet with the advisor; checkpoint 2).** The pipeline names every routine, and alignment with the related
repos takes precedence over the names already in 95S (Abdul, 2026-11-03): where a 95G or 94S partner exists, its name replaces
the current one, McMarkis's included. Units are one 95G file. Rules, in order: a routine with a 95G partner (same job; for a 95
feature such as season, trade, create, awards, records, injury, scout, shootout, playoff) takes the 95G name; an SNES job with
no 95G partner takes the 94S name when the purpose matches; else the current 95S name stays if it says what the code does;
unsure keeps its current name and goes under Unsure (no guessing). Read both bodies; no call-order matching (94S Learned,
2026-11-02). Every rename is one `name_map.csv` row with the old name, the new name and the evidence, so overwritten names
stay traceable. Abdul reviews names per PR, as for 94S. A splitter script lists the candidates per 95G file: every 95S routine
paired with a 95G or 94S routine whose names differ.

**Phase 5, RAM (Sonnet; wide lane).** Rename `ram95s.asm` equates by the same rules, then reorder to the merged order. Two PRs.

**Phase 6, done (Opus advisor review).** Report regenerated on both views, pairing baseline tightened, HANDOFF and RULES
current, `alignment_plan_all_games.md` §8 marked done.

## 9. Model tiers and checkpoints

| Job | Claude | Cursor |
|---|---|---|
| inventory runs, MATCH and gate runs, CSV bookkeeping | Haiku | Composer |
| kit, scope tool, report parser, move script, moves | Sonnet | Grok medium |
| naming, UNSURE placement | Sonnet with the advisor | Grok 4.7 medium |
| advisor: before phase 3 starts, after the same failure twice, before phase 6 | Opus | Grok 4.7 high |

Abdul reviews: this plan, the inventory summary (checkpoint 1), each PR, the naming PRs (checkpoint 2). Failed units follow the
return rule (3 attempts, then advisor, then parked UNSURE). Every correction becomes one Learned line in `docs/RULES.md`.

## 10. Decisions for Abdul

1. **Folder depth. Decided 2026-11-03, for now:** mirror 95G (`src/routines/engine/collide/`, `src/routines/front/season/`);
   the report gets a small change to read the extra level. Abdul may revisit this after reviewing how 94G and 94S compare
   with 95G. Moves are scripted from `routines95s.csv`, so changing the depth later is a re-run of the move script.
2. **Naming lane. Decided 2026-11-03:** the pipeline does all naming, and alignment with the previous and related repos
   overrides the existing 95S names (McMarkis's included). Added to RULES.md "This repo" in phase 0.

## 11. Size

| Phase | PRs | Notes |
|---|---|---|
| 0 kit | 1 | small |
| 1 report | 1 | the parser is the biggest single piece |
| 2 inventory | 1 | script plus one review |
| 3 moves | about 4 | scripted; routine count comes from the inventory (about 4,470 labels today) |
| 4 naming | one per 95G file, about 30 | all routines; renames only where a partner is clear |
| 5 RAM, 6 done | 3 | |
