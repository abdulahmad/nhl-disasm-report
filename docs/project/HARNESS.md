# How this project is run (the harness)

For any agent (Claude Code, Cursor, Codex) or person picking up work in the Code Cleanup project. It describes the
setup, not the state of one piece of work: for that, read the handoff of the work you are given
(C ports: [c_ports_HANDOFF.md](c_ports_HANDOFF.md); 95PC functional track: `docs/FUNCTIONAL_HANDOFF.md` in NHL95PC;
each repo's `HANDOFF.md`). The reasoning behind these practices: [93s_94g_94s_alignment_plan.md](93s_94g_94s_alignment_plan.md) section 7.

Last updated: 2026-11-03 (branch-only rule).

## 1. Repos and their roles

| Group | Repos | What they are |
|---|---|---|
| Byte-matching asm | NHL92Genesis, NHLPA93Genesis, NHL94Genesis, NHL95Genesis, NHL96Genesis, NHLPA93SNES, NHL94SNES, NHL95SNES | disassemblies that rebuild the retail ROM byte for byte (MATCH). Names and layout are aligned across them |
| PC | NHL94PC, NHL94PCDemo, NHL95PC, NHL96PC | DOS EXE rebuilds; NHL95PC also has C matching (Watcom 10.0 GA) and a functional-equivalence track |
| SDL2 ports | branch `sdl2-port` in NHL94PC and NHL95PC | the retail code on the host, unchanged ("vanilla" reference level) |
| C ports | NHL94Genesis-C-Port (1nput, the Genesis base), gens94-c (INDIO, cross-check), NHL94SNES-C-Port (INDIO) | NHL '94 rewritten in C, checked by per-frame hashes |
| Report | nhl-disasm-report | cross-game comparison site and the pairing gate |
| Tools, reference | EA-NHL-Tools, EA-NHL-Disassembly-Project (also holds the ROMs), vscode-nhl-asm | |

## 2. Ground rules

* **Credit.** Every asm repo's AGENTS.md has a "For AI agents: derivative work and credit" section. Any port, mod or fork
  carries the credit near the top of its README and in every release. Add it first.
* **ROMs and EXEs** never go into a repo that doesn't already hold them. They are in EA-NHL-Disassembly-Project
  (`NHL94-Genesis/nhl94retail.bin`, `NHL94-SNES/NHL '94 (USA).sfc`, `NHL93-*`, `NHL95-Genesis/`, ...); NHL95PC commits its own `HOCKEY.EXE`.
* **`main` stays byte-exact** in the asm repos (MATCH). NHL92Genesis is not edited.
* **Branches, not main (Abdul, 2026-11-03).** Nothing merges to `main` yet. All work goes onto the thread's project branch, and pushing there needs no approval, so agents and subagents don't wait for one. PRs are for review only.
* **Approval.** Abdul approves plans and merges PRs. Steps that can be undone (branches, PRs, docs) go ahead; anything
  irreversible or outside the project waits for him.
* **Docs style.** Plain sentences, tables over prose, no other game's names in source comments (lineage lives in
  `docs/name_map.csv`).

## 3. Branches

Each project thread works on its own branch, `claude/project-thread-<id>`, in every repo it touches, and opens PRs from it.

**Nothing merges to `main` yet** (Abdul, 2026-11-03). All alignment work goes onto `claude/project-thread-ggw7zu`, and
agents and subagents push there without waiting for approval once a unit's checks pass. PRs from the branch are views for
review, not merges. Work stops for Abdul only at the plan's review checkpoints.

| Branch | Work |
|---|---|
| `claude/project-thread-ggw7zu` | the asm alignment work (names, folders, 95PC module layout). The report's "branch" view shows this branch |
| `claude/project-thread-4gad59` | the C ports work |
| `sdl2-port` (NHL94PC, NHL95PC) | the SDL2 ports |

When a branch's PR is merged, follow-up work restarts the branch from the latest `main`, as a new PR.

## 4. The kit in each repo

| File | Holds |
|---|---|
| `AGENTS.md` | the standing rules: credit, the repo's role, gates, units and the return rule, lanes, model tiers. The single source |
| `CLAUDE.md`, `.cursor/rules/main.mdc` | one line each: read AGENTS.md (so Claude Code and Cursor can be swapped) |
| `docs/RULES.md` | the authority table (who decides each name and place) plus "Learned": one line per correction Abdul makes |
| `docs/VANILLA.md` (ports) | what the vanilla game allows; the speed decision |
| `HANDOFF.md` / `docs/HANDOFF.md` | where the work in that repo stands and what is next (the C port base uses `docs/C_PORTS_HANDOFF.md`, because upstream ignores `docs/HANDOFF.md`) |
| `docs/name_map.csv` | name lineage (Genesis: `old,new`; SNES: `address,name,...,file`) |

## 5. Gates (programs that can fail)

A change passes on what a program says, never on "looks right" or a model's confidence.

| Gate | Where | Fails when |
|---|---|---|
| **MATCH** | each asm repo (`tools/verify_all.sh`, `make` in NHL95PC) | a byte differs from retail |
| **Pairing** | nhl-disasm-report `tools/test_pairs.py` with `known_pairs.csv`, `baseline.json`, `pair_exceptions.csv`; `tools/gate.sh` runs it and builds the site (branch `claude/project-thread-ggw7zu`) | a known pair stops pairing, or unexplained yellows grow past the baseline |
| **Scope** | SNES asm repos `tools/check_scope.py`; elsewhere `git diff --stat` against the unit's file list | the diff leaves the unit |
| **Equivalence (95PC)** | NHL95PC `tools/equiv/check.py` (Unicorn, original vs compiled draft) | any case differs; low coverage is NEEDS-REVIEW, not PASS |
| **Frames (C ports)** | `test/check.sh ROM` (INDIO repos), `make golden-check` / `make lockstep` (base) | any frame's hash (work RAM, video, sound RAM, picture, sound) differs |
| **Names (C ports)** | `tools/check_names.py --check` | a C name or file drifts further from the asm than `tools/names_baseline.json` |
| **Vanilla (C ports)** | `tools/check_vanilla.sh` | game code reaches the host, or the expected hashes change without a RULES.md line |

Renames and moves can never change MATCH or a frame hash, so they are the safe, mechanical lane.

## 6. How work is cut and run

* **Units are small**: one asm module, one segment, one function, one lens (rename OR move, never both).
* **Splitters are code**, not models: a script lists the units (the names gate's CSV, the report's yellows, `c_functions.csv`).
* **Return rule**: a unit that fails a gate goes back alone, with the check output, file and line, the scope line and the
  attempt number. After 3 failed attempts it goes to the advisor; after that it is parked (UNSURE) with what was tried.
* **Learning edge**: every correction becomes one line in `docs/RULES.md`, which workers and splitters read first.
* **Lanes by blast radius**: contained and reversible (moves, docs, test tooling) merge after the gates; wide (shared
  headers, RAM equates, the report generator) also need Abdul's read; anything that changes retail bytes on `main`,
  frame hashes in a vanilla port, NHL92Genesis, or someone else's upstream never opens without Abdul.

## 7. Model tiers and review checkpoints

| Job | Claude | Cursor |
|---|---|---|
| Search, grep, running checks, logs, bookkeeping | Haiku | Composer |
| Moves, renames, gates, test tooling, report regeneration | Sonnet | Grok medium |
| Naming, C drafts, lineage exceptions | Sonnet, with the advisor | Grok 4.7 medium |
| Advisor | Opus | Grok 4.7 high |

The advisor is consulted at three moments only: before a phase plan is fixed, after the same failure twice, and before a
phase is called done. Abdul reviews at checkpoints (the plan, each PR, naming), not every unit. Subagents run only when
Abdul, an AGENTS.md or a skill asks for them.

## 8. The report (nhl-disasm-report)

`tools/generate.py` builds the comparison site from every repo's sources. The **Source picker** (top left) switches
between `docs/` (every repo at `main`) and `docs/branch/` (each repo at `claude/project-thread-ggw7zu` where it has
it). Views: files, whole ROM, categories, include tree (Genesis files, SNES banks or routine groups, 95P segments).
Lineage comes from each repo's `docs/name_map.csv`. A C column for the C ports is planned (C ports plan, phase 8).

## 9. Night shift (planned, not scheduled yet)

Nightly: build the asm repos (MATCH), regenerate the report and run the pairing gate; build the C ports and run their frame
and names gates; NHL95PC MATCH plus the equivalence suite. A morning report says what broke, what got worse and why. Fix
PRs open for review. Nothing merges by itself.
