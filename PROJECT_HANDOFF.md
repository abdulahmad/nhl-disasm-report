# Code Cleanup: project handoff

**Start here** if you are an agent (Cursor, Codex, Claude Code) or a person picking up Abdul's NHL disassembly cleanup
with no access to the project chat. This page is the map; the detail lives in the linked docs. The project's working
notes are copied into [docs/project/](docs/project/) so you can read them from this repo.

Last updated: 2026-11-03.

## 1. Goal

Bring Abdul's EA NHL disassemblies (Genesis, SNES, DOS) and the NHL '94 C ports into one shape: the same names and the
same folder layout for the same code across games, with every change proven by a program (byte-for-byte MATCH, the
report's pairing gate, frame hashes), never by "looks right". The C ports also need to be shown to play like the original
game and stay as vanilla as the SDL2 ports. Full reasoning: [alignment_plan_all_games.md](docs/project/alignment_plan_all_games.md)
and [c_ports_plan.md](docs/project/c_ports_plan.md).

## 2. Standing rules (Abdul's; they override anything older)

1. **Nothing merges to `main` yet.** All work goes on the project branch (section 4). Pushing there needs **no approval**,
   so don't wait for one, and tell every subagent the same. PRs are opened for review only; do not merge them.
2. **Alignment with the related games wins**, including over names already in a repo from earlier contributors
   (McMarkis's in 95S included). Who decides each name and folder is the authority table in each repo's `docs/RULES.md`;
   in short: a shared routine keeps the earliest game's name (92G is the root), the same-year Genesis game decides folders
   and the names of that year's new features, the platform's earlier repo decides platform-only jobs, data and banks.
3. **`main` stays byte-exact** in the asm repos, and **NHL92Genesis is never edited**.
4. **ROMs and EXEs never go into a repo that doesn't already hold them.** They are in
   [EA-NHL-Disassembly-Project](https://github.com/abdulahmad/EA-NHL-Disassembly-Project) (`NHL94-Genesis/nhl94retail.bin`,
   `NHL94-SNES/NHL '94 (USA).sfc`, `NHL93-*`, `NHL95-Genesis/`, ...); copy them out before use. NHL95PC commits its own `HOCKEY.EXE`.
5. **Credit first.** Every asm repo's `AGENTS.md` has a "derivative work and credit" section; any port, mod or fork carries it.
6. **History lives in `docs/name_map.csv`**, never in source comments. No other game's names in comments.
7. **Never guess a name.** No evidence means it stays on the Unsure list. Every correction Abdul makes becomes one line in
   that repo's `docs/RULES.md` "Learned" section.
8. Abdul approves plans and reviews PRs at checkpoints. Reversible steps (branches, PRs, docs) just go ahead; anything
   irreversible or outside the project waits for him.

## 3. Repos and their roles

| Group | Repos | Role |
|---|---|---|
| Byte-matching asm | NHL92Genesis (92G), NHLPA93Genesis (93G), NHL94Genesis (94G), NHL95Genesis (95G), NHL96Genesis (96G), NHLPA93SNES (93S), NHL94SNES (94S), NHL95SNES (95S) | rebuild the retail ROM byte for byte; names and layout aligned across them |
| DOS | NHL94PC, NHL94PCDemo, NHL95PC (95P), NHL96PC | EXE rebuilds. NHL95PC also has C matching (Watcom 10.0) and a functional-equivalence track. Branch `sdl2-port` in NHL94PC/NHL95PC is the SDL2 port (the "vanilla" reference) |
| C ports | NHL94Genesis-C-Port (1nput's ninety-four, the Genesis base), gens94-c (INDIO, cross-check), NHL94SNES-C-Port (INDIO) | NHL '94 in C, checked by per-frame hashes |
| Report | nhl-disasm-report (this repo) | cross-game comparison site and the pairing gate |
| Tools, reference | EA-NHL-Tools, EA-NHL-Disassembly-Project (holds the ROMs), vscode-nhl-asm | |

## 4. Branches: which one, per repo (checked 2026-11-03)

There are two project branches, one per workstream. Both are right; they hold different work.

| Branch | Workstream | Repos that have it |
|---|---|---|
| `claude/project-thread-ggw7zu` | asm alignment (names, folders, 95PC module layout, the pairing gate) | nhl-disasm-report, NHLPA93Genesis, NHL94Genesis, NHL95Genesis, NHL96Genesis, NHLPA93SNES, NHL94SNES, NHL95SNES, NHL94PC, NHL95PC |
| `claude/project-thread-4gad59` | C ports | NHL94Genesis-C-Port, gens94-c, NHL94SNES-C-Port |
| `sdl2-port` | SDL2 ports | NHL94PC, NHL95PC |

So: continue alignment work on `ggw7zu`, C ports work on `4gad59`. A repo without the branch is read at `main` by the
report's gate. Other `claude/project-thread-*` branches are older or single-task threads. This page itself was written
on `claude/project-thread-qq2fat`.

## 5. Workstreams and status

| Workstream | Status | Next | Detail |
|---|---|---|---|
| Kit and gates (Stage A) | done: AGENTS.md, `docs/RULES.md`, `docs/HANDOFF.md`, Cursor rule in every asm repo; pairing gate in this repo | | [HARNESS.md](docs/project/HARNESS.md) |
| 93G / 93S / 94G (Stage B) | done on `ggw7zu`: 93G left alone, 93S passes B1-B3 | | [93s_94g_94s_alignment_plan.md](docs/project/93s_94g_94s_alignment_plan.md) |
| 94S (Stage C) | moves and naming pass done on `ggw7zu`; Unsure names remain | regenerate report after the 94S comment pass | NHL94SNES `docs/HANDOFF.md`, [naming_review_94s.md](docs/project/naming_review_94s.md) |
| 95G / 96G (Stage D) | old 94G file names fixed (A3), D2 naming under way | 96G's own naming against 95G; RAM order (D4) | [naming_recommendation_and_95g_pass.md](docs/project/naming_recommendation_and_95g_pass.md), [ram_order_and_matches.md](docs/project/ram_order_and_matches.md) |
| 95PC (Stage F) | F3 94G renames and F4 module re-cut (198 to 195 files, one PC module each) done on `ggw7zu` | 95G names for the '95 features, body by body | [95pc_module_layout.md](docs/project/95pc_module_layout.md), [95pc_file_names.md](docs/project/95pc_file_names.md), NHL95PC `HANDOFF.md` |
| 95PC functional track | paused 2026-11-02; 25 of 109 drafts PASS | round 7 | NHL95PC `docs/FUNCTIONAL_HANDOFF.md` |
| **95S (Stage E)** | **in progress**: phase 0 (kit, RULES.md, scope gate) done on `ggw7zu` | phase 1: add 95S to this report and the pairing gate, then phase 2 the inventory script | [95s_alignment_plan.md](docs/project/95s_alignment_plan.md), NHL95SNES `docs/HANDOFF.md` |
| **C ports** | **paused at step E2** (2026-11-03). Phases 0-1 pushed; gens94-c, E1, E4 and SNES checks all identical | E2: 1nput's oracle checks, using the vasm GitHub mirror Abdul OK'd | [c_ports_HANDOFF.md](docs/project/c_ports_HANDOFF.md) (read this first for C ports) |
| 94PC (Stage G) | kit only; waits for the disassembly | | |

Open PRs for review: the three C ports `#1`s on `4gad59`. Alignment PRs are views of `ggw7zu`, not merges.

## 6. Gates (a change passes only on these)

| Gate | Command | Fails when |
|---|---|---|
| MATCH | `tools/verify_all.sh` in each asm repo; `make` / `make fullcheck` in NHL95PC | a byte differs from retail |
| Pairing | `tools/gate.sh` in this repo (on `ggw7zu`): regenerates and runs `tools/test_pairs.py` against `known_pairs.csv`, `baseline.json`, `pair_exceptions.csv` | a known pair stops pairing, or a count rises above the baseline |
| Scope | `tools/check_scope.py` (SNES repos); else `git diff --stat` against the unit's file list | the diff leaves the unit |
| Equivalence (95PC) | `tools/equiv/check.py` | any case differs |
| Frames (C ports) | `test/check.sh ROM` (INDIO repos), `make golden-check` / `make lockstep` (base) | any frame hash differs |
| Names / vanilla (C ports) | `tools/check_names.py --check`, `tools/check_vanilla.sh` | names drift from the asm, or game code reaches the host |

Units are small (one module, segment or function; rename OR move, never both). A unit that fails goes back alone with the
check output; after 3 failed attempts it goes to the advisor, then it is parked as UNSURE.

## 7. Model tiers and the advisor

| Job | Claude | Cursor |
|---|---|---|
| Search, running checks, bookkeeping | Haiku | Composer |
| Moves, renames, gates, report regeneration | Sonnet | Grok medium |
| Naming, C drafts, lineage exceptions | Sonnet with the advisor | Grok 4.7 medium |
| **Advisor** | Opus | Grok 4.7 high |

The advisor is consulted at three moments only: before a phase plan is fixed, after the same failure twice, and before a
phase is called done. An advisor reviews plans and failures against the rules above and the gates; it does not merge or
widen scope. Subagents run only when Abdul, an AGENTS.md or a skill asks for them.

## 8. Reading order for a new agent

1. This page, then [HARNESS.md](docs/project/HARNESS.md) (how the project is run).
2. The handoff for your workstream: [c_ports_HANDOFF.md](docs/project/c_ports_HANDOFF.md), [95s_alignment_plan.md](docs/project/95s_alignment_plan.md), or the repo's `docs/HANDOFF.md` (NHL95PC: `HANDOFF.md`).
3. In the repo you touch, on its project branch: `AGENTS.md`, then `docs/RULES.md` (read before every unit).
4. For this report: [README.md](README.md) and, on `ggw7zu`, `docs/HANDOFF.md` and `docs/ALIGNMENT.md` (the approved all-games plan).

Known trap: several repos' `HANDOFF.md` link to `docs/ALIGNMENT.md` on this repo's `main`; it only exists on `ggw7zu`
(and as [docs/project/alignment_plan_all_games.md](docs/project/alignment_plan_all_games.md)).

## 9. Index of docs/project/

| File | What it is |
|---|---|
| [HARNESS.md](docs/project/HARNESS.md) | repos, rules, branches, kit, gates, tiers, night shift |
| [alignment_plan_all_games.md](docs/project/alignment_plan_all_games.md) | the approved plan, stages A to G |
| [93s_94g_94s_alignment_plan.md](docs/project/93s_94g_94s_alignment_plan.md) | first plan and the reasoning behind the harness (section 7) |
| [95s_alignment_plan.md](docs/project/95s_alignment_plan.md) | 95S plan, phases 0 to 5 |
| [95pc_module_layout.md](docs/project/95pc_module_layout.md), [95pc_file_names.md](docs/project/95pc_file_names.md), [95pc_engine_files.csv](docs/project/95pc_engine_files.csv), [95pc_95g_comment_samples.md](docs/project/95pc_95g_comment_samples.md) | 95PC module re-cut evidence and names |
| [c_ports_plan.md](docs/project/c_ports_plan.md), [c_ports_HANDOFF.md](docs/project/c_ports_HANDOFF.md) | C ports plan and live handoff |
| [folder_preview.md](docs/project/folder_preview.md), [bank_names_proposal.md](docs/project/bank_names_proposal.md), [bank_names_preview.md](docs/project/bank_names_preview.md) | SNES folder and bank naming |
| [naming_review_94s.md](docs/project/naming_review_94s.md), [naming_recommendation_and_95g_pass.md](docs/project/naming_recommendation_and_95g_pass.md) | naming reviews |
| [ram_order_and_matches.md](docs/project/ram_order_and_matches.md), [bg_scroll_usage_93s_94s.md](docs/project/bg_scroll_usage_93s_94s.md), [unmatched_vs_94g.md](docs/project/unmatched_vs_94g.md), [unmatched_screenshot_matches.md](docs/project/unmatched_screenshot_matches.md) | measurements behind the 93S/94S decisions |

These are snapshots of the project's working files as of the date above. When you change state, update the repo's own
`HANDOFF.md` and this page's section 5.
