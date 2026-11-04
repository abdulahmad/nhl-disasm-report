# C ports: handoff

**Read this first if you are picking up the C ports work.** It is kept current after every finished step.
How the project is run (repos, branches, gates, model tiers, checkpoints): [HARNESS.md](HARNESS.md).
The plan with its reasoning: [c_ports_plan.md](c_ports_plan.md).

Last updated: 2026-11-04 (caught up to per-repo Now blocks; no longer paused at E2).

## Standing rule (Abdul, 2026-11-03 15:00)

**Nothing merges to `main` yet.** All work goes onto the project branch `claude/project-thread-4gad59` in each repo.
Pushing to that branch needs **no approval**, so don't wait for one; every subagent must be told this too. The open PRs
are for review only. Do not merge them.

## 1. Goal

Abdul's goals: bring the three NHL '94 C ports into line with each other and with the asm repos; prove they behave like
the original game; keep them as vanilla as the NHL94PC / NHL95PC SDL2 ports; finish 95PC functional equivalence; and
work out whether the Watcom library needs decompiling for non-x86 (answer: no; replace it with libc plus a small shim,
see the plan's section 6.2).

## 2. Decisions already made (do not reopen)

| Decision | Choice | When |
|---|---|---|
| Genesis base | **1nput's ninety-four (NHL94Genesis-C-Port)**, with a planned `VANILLA=1` build. gens94-c (INDIO) is the cross-check | 2026-11-03 |
| Slowdown | **an option, off by default** (Smooth is the default). The SNES port defaults to Original today, so flipping that is a question for INDIO | 2026-11-03 |
| Plan approval | approved ("start implementing this on the project branches") | 2026-11-03 |

Still open (from the plan's section 9; recommendations stand until Abdul says otherwise): one flat C file per asm module
(3), 95PC 32-bit targets first (4), translate the SB/OPL driver to C (5).

## 3. Repos, branches, PRs

Branch for this work in every repo: **`claude/project-thread-4gad59`**.

| Repo | Role | PR | State |
|---|---|---|---|
| NHL94Genesis-C-Port | Genesis base (1nput's v0.3.6 mirror; upstream github.com/1nputs/ninety-four) | [#1](https://github.com/abdulahmad/NHL94Genesis-C-Port/pull/1) | open; phases 0-1, E1–E5, VANILLA=1 |
| gens94-c | Genesis cross-check (INDIO's cut of v0.3.6) | [#1](https://github.com/abdulahmad/gens94-c/pull/1) | open; phases 0-1, E1/E3 done. **Ignored from 2026-11-03 (Abdul)** |
| NHL94SNES-C-Port | SNES port (INDIO) | [#1](https://github.com/abdulahmad/NHL94SNES-C-Port/pull/1) | open; Linux crash fix, 92 renames + re-cut |
| NHL95PC | 95PC asm/C (functional track) | none yet | not started in this thread |

No CI runs in the three C repos. Nothing merges to `main` for now (standing rule above).

## 4. ROMs (never commit them)

They are committed in **EA-NHL-Disassembly-Project** (Abdul, 2026-11-03):

| Game | Path in EA-NHL-Disassembly-Project | SHA-1 |
|---|---|---|
| NHL '94 Genesis | `NHL94-Genesis/nhl94retail.bin` | `7b1489ab501258133bf03e5f0892b77d04312580` |
| NHL '94 SNES | `NHL94-SNES/NHL '94 (USA).sfc` | `10dcd21be9c5542e82b0b94473bf5ff569b36cf5` |

Copy them out of the repo before use (this thread used `~/roms/nhl94.bin` and `~/roms/nhl94.sfc`), and never into a C port repo.

## 5. Results so far (all verified by running, 2026-11-03)

| Check | Result |
|---|---|
| gens94-c `test/check.sh` (8 runs, 156k frames) | **8 of 8 identical** |
| E1: public ninety-four v0.3.6 plays gens94-c's 8 scripts | **8 of 8 identical** to gens94-c's `expected.txt`. INDIO's reference hashes are reproducible from public code |
| E4: tag v0.2.0 ("2.0.0", the pre-extras release) on the same scripts | **8 of 8 identical**. v0.2.0, v0.3.6 Classic and gens94-c are one game on these runs |
| SNES `test/check.sh` (7 runs, 116k frames) | crashed on Linux (`strtok_r` undeclared under glibc with `-std=c11`); fixed in `test/golden.c`; then **7 of 7 identical** |
| Names gate, Genesis (both repos, phase 1) | 756 routines: 473 ok, 250 other module, 30 renamed, 3 missing |
| Names gate, SNES (after re-cut) | 855 routines: 844 ok, 0 other module, 6 parked, 5 missing |
| Vanilla gate (gens94-c, SNES, base VANILLA=1) | PASS |
| E2 (base): 1nput oracle on this machine | `make lockstep` **18 of 18**; `make test` **10,276 of 10,276** (0 failed, 570 skipped); `make golden-check` **20 of 20** |
| E3: gens94-c `game/` in the base lockstep host | **18 of 18**; two planted bugs were caught |
| E5 coverage (scripts + lockstep + golden) | 793 of 838 original routines ran (94.6%), 93.0% of lines; lockstep alone 785 (93.7%) after `demo_long`/`shootout_full`, 53 never reached |
| VANILLA=1 (base) | gens94-c's 8 scripts 8 of 8; lockstep 18 of 18 |

Builds: v0.2.0 needs `make WERROR= nhl94` on GCC 13 (a pulseman warning); v0.3.6 and both INDIO ports build clean.
The SNES build needs `make ROM=path` (the SPC program is generated from the ROM).

## 6. Next steps, in order

E2, E3, E5 (parts 1–2), VANILLA=1, and the SNES rename/re-cut are done. See the per-repo Now blocks.

1. **Coverage, part 3** (plan E5): new lockstep vectors for the 53 routines lockstep never reaches
   (`test/coverage_lockstep.txt` in the base: injuries, fights, breakaways, the period stats screen, manual goalie, record holders).
2. **Ask 1nput** whether he takes renames and the file re-cut upstream. Until then the names gate only reports.
3. **Ask INDIO** for ninety-four-snes's oracle tools, and whether he wants Smooth as the SNES default. Else build them (plan S2).
4. **Slowdown option** (off by default): a 68k cost model, then lockstep with lag frames checked (plan E6).
5. **95PC functional track**: `docs/FUNCTIONAL_HANDOFF.md` in NHL95PC (round 7 first), then the SDL-port golden runs (plan 6.1 F5).

**gens94-c is ignored from 2026-11-03 (Abdul)**: no work or cross-checks on it. Keep it in step with the base only if those happen.

## 7. How to run the checks

```
# gens94-c (cross-check)
make && bash test/check.sh ~/roms/nhl94.bin            # 8 runs, ~2 min with 8 cores
python3 tools/check_names.py --check && tools/check_vanilla.sh

# NHL94SNES-C-Port
make ROM=~/roms/nhl94.sfc && bash test/check.sh ~/roms/nhl94.sfc
python3 tools/check_names.py --check && tools/check_vanilla.sh

# NHL94Genesis-C-Port (base): build, then gens94-c's scripts on it (E1)
git submodule update --init && make nhl94
bash test/crosscheck.sh ~/roms/nhl94.bin               # 8 runs, ~2 min
python3 tools/check_names.py --check
```

E1 / E4 runner: `test/crosscheck.sh ROM [../gens94-c] [build/nhl94]` in the base (committed). It plays gens94-c's
scripts on a ninety-four build and compares with gens94-c's `expected.txt`; pass another binary (e.g. a v0.2.0 worktree's)
as the third argument. `test/check.sh` is executable again in both INDIO repos (on the branch).

The names gate needs the asm repo beside the C repo (`../NHL94Genesis`, `../NHL94SNES`), or `--asm` / `$NHL_ASM`.

## 8. Blockers and asks

| Waiting on | What |
|---|---|
| 1nput | OK to rename and re-cut files in the base (else the base keeps his names and the report pairs by address) |
| INDIO | ninety-four-snes oracle tools; the ninety-four commit d503a46 (no longer needed: E1 reproduced its hashes); Smooth as SNES default |
| (resolved) | E2 needs vasm (it builds the asm for the oracle's `symbols.json`): `sun.hasenbraten.de` is blocked by this environment's network policy, and building it from a GitHub mirror was refused by the safety check. Either allow that host in the cloud environment, or OK the mirror (github.com/StarWolf3000/vasm-mirror). **Abdul OK'd the mirror (2026-11-03 14:16):** clone it into `ref/vasm-src/vasm` in the base, then `tools/patches/vasm-build.sh ref/vasm-src/vasm`, `tools/patches/gpgx-cpuhook-extern.sh ref/gpgx`, `tools/asm/build_vasm.sh`, and continue E2. `tools/fetch_refs.sh` has already cloned and built Genesis Plus GX and the references in `ref/` |
| Abdul | decisions 3-5 if he disagrees with the recommendations (the PRs stay unmerged by his rule) |

## 9. Log

* 2026-11-04: project handoff caught up to the per-repo Now blocks (no longer paused at E2). CONTRIBUTING.md added on the C-port branch.
* 2026-11-03 14:20: **paused by Abdul** to save usage. Resume was E2 with the vasm mirror; E2 later passed on the branch.
* 2026-11-03: plan written and approved; decisions 1-2 made; phases 0-1 pushed (3 PRs); ROMs found; gens94-c check, E1, E4
  and the SNES check all identical; SNES Linux crash fixed.
