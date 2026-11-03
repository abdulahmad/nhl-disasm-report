# The C ports: equivalence, alignment, vanilla, 95PC and the library question

Analysis and plan only. Nothing in any repo was changed. Sources: NHL94Genesis-C-Port `1b0b30e` (= upstream
1nputs/ninety-four v0.3.6, whose tags I fetched from upstream because the fork has none), gens94-c `32c30fc`,
NHL94SNES-C-Port `d1562ae`, NHL95PC `da7f241` (plus branches `sdl2-port` and `claude/project-thread-ggw7zu`),
NHL94PC `sdl2-port`, NHL94Genesis `main`, NHL94SNES `main`. I had no ROM or EXE runs here, so every number below
comes from reading code, diffs and the repos' own docs and scripts. Nothing was built or played.

## 1. The short answer

* **INDIO's Genesis port is 1nput's port with the extras taken out.** gens94-c says it is ninety-four v0.3.6 minus
  game rules, roster sets, wide view, netplay, save states and the menu, and the diff confirms it. Compared with
  v0.3.6, ignoring comments, whitespace and line endings, about **550 lines of game code differ** across the 19k lines.
  The ones I read are all the removed hooks put back to the original path: `rules[RULE_ASSIST_FIX]`,
  `rule_scale(RULE_TIRING, 0x21)` becomes `0x21`, `ART(FaceOffMap)` becomes `SYM_FaceOffMap`, the roster set's banner
  path is gone. `goalie.c`, `assign.c`, `menu.c`, `sound.c`, `z80.c`, `sram.c` and `start.c` are identical.
  So the equivalence question for INDIO's port is mostly answered by 1nput's work. Section 2 says how to prove the rest.
* **"Tag 2.0.0" is upstream `v0.2.0`** (the tags are v0.1.0, v0.2.0, v0.3.0, v0.3.5 and v0.3.6). It is the last release
  before game rules, rosters and netplay, but it already had save states and rewind. It is also older than the
  "native state" rewrite. gens94-c starts from v0.3.6 instead, so it carries 1nput's later fixes and the native
  structs, with the extras taken out. The two are not the same code (about 4,900 changed lines between v0.2.0 and gens94-c),
  but both should play the same frames. One run settles it (section 2, step E4).
* **Both Genesis ports leave out one real difference: the cartridge's slowdown.** On the cartridge, when the 68000 runs out of
  time, a pass of the game loop takes two vblanks and everything moves twice as far. Both C ports always use one vblank.
  1nput's lockstep check gets around this by resyncing to the emulator's state at every lag frame. So the claim that is
  proven is "every pass computes what the cartridge computes, given the same elapsed count". It is not "plays the same
  frames as the cartridge". The SNES port has an Original speed with a CPU cost model for exactly this. That is decision 2.
* **The SNES port's evidence lives outside the repo.** It was checked in iDNi's earlier `ninety-four-snes` against snes9x,
  and that repo isn't public. All the SNES repo can show today is its own hashes. Ask INDIO for the oracle tools, or build them
  (section 2.3).
* **Alignment is mostly renames and file moves, and both are safe**, because the frame-hash check cannot change under
  either one. Both INDIO ports follow the asm layout from before 94G's commit `0fe607c` ("Combine logic and setup files;
  rename middle and video"). Genesis: 759 original-routine functions, 700 still exist as labels, 446 sit in the same module.
  SNES: 702, 609 and 331.
* **The Watcom C library does not need decompiling.** It needs replacing with the host libc plus a small shim for
  the 5 or 6 behaviours the game can see (`rand`, `qsort` order, `sprintf` formats, DOS file calls). The bigger non-x86 job is
  the code that is neither game nor Watcom: **EA's PC library (111 KB) and the EACSNDF sound drivers (105 KB)**, about as much
  x86 again as a third of the game. Section 6.

## 2. How far INDIO's port can be shown equivalent

### 2.1 The chain of evidence today

```
cartridge ROM ──(1nput: 10,276 recorded routine calls; 18 lockstep sessions vs Genesis Plus GX,
   │              work RAM + VDP at every vblank, resync at lag frames)
   ▼
ninety-four (Classic rules) ──(1nput: golden runs, 20 runs / ~227k frames, bit for bit across every refactor)
   │
   ▼  hashes from ninety-four commit d503a46, which is NOT in the public repo (public main = v0.3.6 1b0b30e)
gens94-c ──(test/check.sh: 8 scripts, 156k frames; work RAM, VDP, Z80 RAM, picture and sound hashed each frame)
```

Every link is a program that can fail, which is good. The weak spots are:

1. **gens94-c has no direct link to the ROM.** The oracle, lockstep and vectors stayed in ninety-four.
2. **The reference hashes come from an unpublished ninety-four commit.** Probably harmless, but nobody else can reproduce them yet.
3. **Coverage is unmeasured.** 8 scripts and 18 sessions are a lot, but nobody has listed which routines and branches they never reach
   (overtime, penalty shots, injuries, a pulled goalie, the Cup final, 4 Way Play, records in save RAM).
4. **Lag frames are resynced, not checked** (section 1).
5. **The HV counter** is a fixed stand-in in golden runs. Lockstep feeds the oracle's values, so the check is sound, but the free-running
   game's "random" HV reads aren't the console's. That is fine for equivalence and worth one line in the docs.

### 2.2 Steps to close it (Genesis)

| # | Step | What it proves | Size |
|---|---|---|---|
| E1 | Build public v0.3.6 and record golden files for gens94-c's 8 scripts. Compare with `test/expected.txt` | gens94-c's reference is reproducible from public code | Small (needs ROM) |
| E2 | Run 1nput's own checks on v0.3.6: `make test`, `make lockstep`, `make golden-check` | 1nput's ROM claim holds on our machine | Small to medium (GPGX oracle build, 29 captures ~15 min, 3.6 GB) |
| E3 | Bring the lockstep player and oracle tools into gens94-c as **test tooling only** (`test/oracle/`, nothing in `game/`). Run the 18 sessions on gens94-c itself | INDIO's port against the ROM directly, with no v0.3.6 in between | Medium |
| E4 | Play the same 8 scripts on v0.2.0. Same hashes: v0.2.0, v0.3.6 Classic and gens94-c are one game. Different: bisect v0.2.0..v0.3.6 for the commit | answers "is 2.0.0 the same game as INDIO's" | Small |
| E5 | gcov on gens94-c over check.sh plus the lockstep sessions. Write `test/coverage.txt`: every routine and branch never reached. Add scripts until each is reached or has a reason it can't be | the runs actually exercise the code | Medium |
| E6 | (With decision 2) a 68k cost model, then lockstep with lag frames **checked**, not resynced | frame-for-frame the cartridge, slowdown included | Large |

After E1 to E5, the honest claim for gens94-c is: "every pass of the game loop matches the cartridge on N sessions reaching
X% of branches, and the remaining list is in `test/coverage.txt`". After E6 it can drop "every pass".

### 2.3 The SNES port

| # | Step |
|---|---|
| S1 | Ask INDIO for `ninety-four-snes`'s oracle tools (snes9x hook, recordings, the routine-by-routine checker). If he shares them, S2 becomes a copy |
| S2 | Otherwise build the same shape as 1nput's: the snes9x (or bsnes) libretro core with a CPU hook, recorded sessions, a lockstep player in `test/oracle/` |
| S3 | Coverage report, as E5 |
| S4 | Check the cost model: per session, count the passes where the C's `elapsed` matches the oracle's. The README says "close to it rather than exact", so put the number in the README |

## 3. Which repo is the base (revised after your answer)

| Repo | Role |
|---|---|
| **NHL94Genesis-C-Port** (1nput, ninety-four) | **The Genesis base.** It is the original C, with the oracle, lockstep, vectors and golden tooling already in it, so phase 2's E3 isn't needed: it is checked against the ROM in its own repo |
| **gens94-c** (INDIO) | A cross-check. It is the same game with the extras removed, so its hashes must stay equal to the base's Classic runs. Once the base has a vanilla build (below), gens94-c is no longer needed for play |
| **NHL94SNES-C-Port** (INDIO) | The SNES port. It has no 1nput counterpart, so its tooling is the gap (section 2.3) |

**Vanilla on top of 1nput's base.** v0.3.6 carries rules, rosters, save states and netplay. To keep the "PC ports" level, the base gets:
* Classic rules and the cartridge's rosters as the default (they already are);
* a `VANILLA=1` build that leaves out `native/rules.c`, `rosters.c`, `net.c`, `state.c` and the menu pages for them, the way INDIO cut gens94-c,
  but as a build switch in the same tree instead of a second repo;
* a vanilla gate: `VANILLA=1` and the default build both play gens94-c's 8 scripts with identical hashes.

**What this costs.** Renames and file re-cuts (phases 4 and 5) in the base move it away from upstream ninety-four. Two choices:
offer them to 1nput as PRs, or keep a rename layer only in the docs and report. Ask 1nput first. If he doesn't want them,
the report pairs by address (`symbols_gen.h`) and the C names stay his.

**Credit (required first).** The NHL94Genesis and NHL94SNES AGENTS.md "derivative work and credit" rule applies to both INDIO
ports. The SNES README links NHL94SNES but names no one. gens94-c says "the community's byte-matching rebuild" with no link or names.
Phase 0 adds the full credit block near the top of both READMEs and to the release notes. A PR to INDIO's upstream should do the same.

## 4. Aligning the three ports with each other and with the asm

### 4.1 Authority table

| Category | Authority |
|---|---|
| Function name of an original routine | The current asm label (94G for Genesis, 94S for SNES). Old names go through each asm repo's `docs/name_map.csv` |
| Asm local (`Pausemode.pall`) | `Pausemode_pall`, a `static` function in the parent's file |
| Helper (a piece split off, or the C's own) | `<Routine>_<what>`, `static` where possible, listed as a helper in ROUTINES.md (already the convention) |
| File | One C file per asm module: 94G `collide94.asm` becomes `game/collide.c`, and 94S `routines/collide/` becomes `game/collide.c`. So the same module has the same file name in both C ports |
| Order inside a file | ROM order, as the asm |
| RAM field names (`ram.h`) | The asm RAM equates (`ram94.asm`, `ram94s.asm`) |
| Host code (`platform/`, `runtime/`) | Shared between the two INDIO ports where it is the same job (settings, pad setup, menu) |
| Comments | The routine's asm file and label on the first line, as now. No other game's names in comments (the asm repos' rule) |

### 4.2 What changes, measured

| | Genesis (gens94-c vs NHL94Genesis) | SNES (C port vs NHL94SNES) |
|---|---|---|
| Original-routine functions | 759 | 702 |
| Label still exists | 700 | 609 |
| Same module as the asm | 446 | 331 |
| Renamed since (name_map lineage) | 59 | 93 |
| Biggest file moves | checks → logic (73), input → logic (36), data → setup (35), video → middle (31), display → video (24), video → decompress (17), assign → logic (15), video → print (15) | checks → logic (54), snes → video / middle / sound (128), input → logic (24), data → setup (19), video → middle (14) |

The SNES `snes.c` (the bank `$80` engine) splits by job into the 94S folders the earlier plan settled on (`video`, `middle`,
`sound`, `decompress`, `main`).

### 4.3 How the report pairs them

nhl-disasm-report gets a C column. For each asm routine it shows the C function, its file, and whether file and name agree.
Its source is the first comment line plus `symbols_gen.h` addresses, so there is no hand table. The same pairing gate as the asm work
applies (`known_pairs.csv`, `baseline.json`), with a C row per lineage: 94G vs gens94-c, 94S vs the SNES C, and later 95PC asm vs 95PC C.

## 5. Keeping them vanilla

### 5.1 What the PC SDL ports allow, written down

From NHL94PC and NHL95PC `sdl2-port` (docs/SDL2_PORT.md): **"Nothing of the game is changed or patched"**, `src/` still builds
MATCH, and the host answers the hardware. The only game routines replaced are ones that can't work on the host: the FPU hook,
the CPU test, the VESA probe and the video mode save. Host features they do have: window, scaling, 4:3, fullscreen, OpenGL
looks and MiSTer filters, an ini file, input bindings, controllers, pointer rules, hotkeys, a stats display, WAV capture and
scripted input. The game runs at its own speed.

That becomes `docs/VANILLA.md` in all four port repos:

| Allowed (host) | Not allowed in the vanilla port |
|---|---|
| Window, scaling, aspect, filters, fullscreen | Any change to game rules, rosters, teams, art or text |
| Settings file, key and pad bindings, controller setup | New menu items inside the game's own menus |
| Screenshots, audio capture, FPS display | Save states, rewind, netplay (these go on a separate branch or repo) |
| Fast-forward as a host key (no game change) | Fixing original bugs (the weight bug stays) |
| Headless test runner, scripted input | Speed other than the original's, unless as a labelled option (decision 2) |

### 5.2 Where the C ports stand against it

* **gens94-c**: game code is the original path. The host has a settings menu (F9), pad setup, Show FPS and 4:3 / Native. That is
  within the PC ports' level. The one gap is speed: no Original (slowdown) mode.
* **SNES C**: same, with Original speed as the default and Smooth as an option. Within the PC ports' level.
* **1nput's**: not vanilla by design (rules, rosters, netplay). Its Classic rules mode plays the original, which is what makes it
  a usable reference.

### 5.3 The vanilla gate (a program, not a review)

`tools/check_vanilla.sh` in both INDIO ports fails when:
* `game/` includes anything from `platform/` other than `hal.h`, or reads a setting;
* a PR changes `test/expected.txt` without a `docs/RULES.md` line saying why (a changed hash means a changed game);
* a new global appears in `ram.h` that is not an asm RAM equate.

## 6. NHL95 PC

### 6.1 Remaining functional equivalence

Today: 977 of 1,084 functions bit-perfect, 25 of the other 107 proven functional (PASS), so 1,002 in total. 75 drafts are
NEEDS-REVIEW, mostly from low coverage of random inputs, and 8 are FAIL (triaged, none a confirmed draft bug). Harness round 7
is unfinished in `tools/equiv/wip/round7.patch`. The order in docs/FUNCTIONAL_HANDOFF.md stays right. I'd add one thing to step 5:

| # | Step |
|---|---|
| F1 | Finish round 7 (per-case stack fill, caller-driven entry states). Pilots stay PASS, the planted bug FAILs |
| F2 | Rerun all 75 NEEDS-REVIEW drafts (a plain script, 3 in parallel) |
| F3 | Triage new FAILs: max 3 tries each, then UNSURE |
| F4 | Advisor pass on what is still NEEDS-REVIEW |
| F5 | **Whole-game replay using the SDL port as the oracle.** The port runs the real x86 code natively with the real data, and it already has scripted input (`NHL95_KEYS`) and dumps. Add a golden mode: hash the game's data segment and the frame buffer every frame. Then a hybrid build that swaps in the compiled C of chosen functions must give the same hashes. This is the same tool the Genesis ports use, and it is what checks the 75 low-coverage drafts in real play. It also replaces the DOSBox-X snapshot idea in step 9 of FUNCTIONAL_PLAN.md |
| F6 | Nightly: `make` MATCH, the equivalence suite, the golden runs. It reports, and merges nothing |

CanFillLineSlot (the junk upper 16 bits) is still your call, as recorded.

### 6.2 Does the library code need decompiling for non-x86?

What the EXE's code is made of (from EXE_SEGMAP95PC.md):

| Part | Size | In the 1,084? | For non-x86 |
|---|---|---|---|
| Game (PC-new, 93G via 94PC, 95G roles) | ~660 KB | yes | the C we have, built by GCC/Clang for the host |
| EA PC library (memory manager, timer, windows, shapes, unpack, gfx, file blocks, CMV/MVI movies, cdstream, zone manager) | 111 KB | no | **needs C**: functional, not byte-exact |
| EACSNDF sound (high level 11 KB, PC speaker / AdLib / SB / MT-32 / GUS drivers and SDK 94 KB) | 105 KB | no | **needs C or a host replacement** |
| Watcom clib (incl. the 13 KB 387 emulator) | 47 KB | no | **replace, don't decompile** |
| DOS/4GW glue, video BIOS, VGA/VESA blitters, input drivers | ~25 KB | no | host replacements; blitters need C |
| 13 hand-asm game functions | small | no | C by behaviour |

**Watcom clib: replace it.** The game C calls about 35 library functions: `sprintf` 294 times, `strcpy` 180, `strcat` 136,
`memcpy` 49, `strcmp` 26, `rand` 23, `memset` 21, `qsort` 20, the `_dos_*` file calls, `fopen` / `fscanf` / `fgets`, `itoa`,
`strupr` / `strlwr`, `stricmp` / `strnicmp`, `int386` twice. Almost all of them behave the same in any libc. The ones that can change
the game are reproduced in a small `wclib/` shim, and each shim function is checked against the EXE's own routine with the
existing `tools/equiv` harness (it runs the original in Unicorn, which is exactly this check):

* `rand` / `srand`: Watcom's exact generator, because it decides game outcomes;
* `qsort`: Watcom's algorithm (the EXE has its `med3`), because it is not stable and the order of equal keys shows in standings and lists;
* `sprintf` / `printf`: `%f`, `%e` and padding as Watcom formats them (`_FtoS_`), for any text that reaches the screen or files;
* `_dos_*`, `fopen` on DOS paths: the SDL port's case-insensitive path mapping (`port/dos.c`) reused;
* `stricmp` / `strupr` / `itoa`: trivial, in the shim so no platform differences slip in;
* `__CHK` stack checks: nothing; the 387 emulator: nothing (the host FPU, with the float caveat below).

**EA PC library: needs C, but functional, not matched.** It is not game logic, but parts of it decide pixels and data: the
decompressors (`ea_unpack`, `ea_unpackf_blit`, `ea_shpi`), shapes and blitters, the memory manager's block choices, and the
file blocks. Same method as the drafts: Ghidra first pass (`tools/ghidra_decomp.py` already does LE with our labels), then
`tools/equiv` PASS. Timer, VESA init, keyboard, mouse and joystick become host calls, as the SDL port already answers them at port level.

**Sound drivers: two ways.** (a) Translate one driver path to C with each `in` / `out` as a host call, and keep the SDL port's
emulated chips (Nuked-OPL3, SB DSP, GUS). That's the most faithful, and the closest to the Genesis ports' "one call, one access" HAL.
(b) Reimplement the EACSNDF high-level API on the host. Less faithful. I recommend (a), Sound Blaster with OPL first, and GUS and MT-32 later.

**Three portability risks to measure before choosing targets:**
* **Pointers in game data.** The game is a flat 32-bit program and probably keeps pointers in 32-bit struct fields and tables.
  A 64-bit host breaks that. So build 32-bit targets first (wasm32 and armv7 are 32-bit), and treat 64-bit as its own phase
  (pointer fields become offsets or handles, as 1nput's "native state" did on Genesis).
* **char signedness and packing.** Watcom's `char` is unsigned by default. GCC on x86 is signed (ARM unsigned), so build with
  `-funsigned-char`. `-zp1` means `#pragma pack(1)` everywhere.
* **Floating point.** Only 8 C files use `float` / `double`, but Watcom keeps x87 80-bit intermediates. Check those functions in the golden
  runs on ARM, and fix with explicit rounding where they differ.

## 7. Phased plan

Each phase is a PR (or a few) per repo. Renames and moves must keep `test/check.sh` identical (C ports) or MATCH (95PC).

| # | Phase | Repos | Size |
|---|---|---|---|
| 0 | Credit block. AGENTS.md (CLAUDE.md and `.cursor/rules` point to it), `docs/RULES.md` (section 4.1), `docs/VANILLA.md` (5.1), HANDOFF.md | gens94-c, SNES C | Small, docs only |
| 1 | Gates: names (`tools/check_names.py`: every original function is a current asm label at the same address and module; every `ram.h` field is an equate), scope, vanilla (5.3), coverage report | gens94-c, SNES C, report | Medium |
| 2 | Genesis equivalence E1 to E5 | gens94-c (+ v0.3.6 / v0.2.0 locally) | Medium, needs ROM |
| 3 | SNES equivalence S1 to S4 | SNES C | Medium to large, depends on INDIO |
| 4 | Renames to current labels (59 Genesis, 93 SNES), locals as `Parent_local` | both | Small, mechanical |
| 5 | File re-cut to asm modules, ROM order inside files | both | Medium, moves only |
| 6 | Shared host layer between the two INDIO ports; host feature parity with the PC ports where it's cheap (bindings, filters) | both | Medium |
| 7 | (Decision 2) Genesis Original speed as an opt-in setting: 68k cost model, then E6 | NHL94Genesis-C-Port | Large |
| 8 | Report C column and pairing rows | nhl-disasm-report | Medium |
| 95-F | F1 to F6 (section 6.1) | NHL95PC | as FUNCTIONAL_PLAN.md |
| 95-N | Non-x86: N0 inventory tool (every x86 byte range by kind, which have C); N1 32-bit x86 host build of all game C (`gcc -m32`), golden vs the asm SDL port; N2 `wclib` shim with equiv checks; N3 EA library C; N4 SB/OPL driver C; N5 wasm32 / armv7 build, golden vs x86; N6 64-bit pointer work, aarch64 | NHL95PC | Large, after 95-F5 |

Dependencies: 0 first. 1, 2 and 3 can run side by side. 4 and 5 need the names gate from 1. 7 needs 2. 95-F and 95-N are their
own track, and N1 needs F5's golden runs.

## 8. How we run it

Same practices as `93s_94g_94s_alignment_plan.md` section 7, applied here.

### 8.1 Gates (programs that can fail)

| Gate | Fails when | Where |
|---|---|---|
| **Frames** | any hash in `test/check.sh` differs (the C ports' MATCH) | each C port |
| **Oracle** | lockstep against the ROM diverges outside a lag resync | `test/oracle/` (Genesis from 1nput's tools; SNES from S1/S2) |
| **Names** | an original function isn't a current asm label at the same address, or sits in another module; a RAM field isn't an equate | `tools/check_names.py`, reading the asm repo's symbols and `name_map.csv` |
| **Scope** | the diff leaves the unit's file list | `tools/check_scope.py` |
| **Vanilla** | section 5.3 | `tools/check_vanilla.sh` |
| **Coverage** | reached routines or branches drop below `test/coverage_baseline.txt` | gcov script |
| **95PC** | MATCH; `tools/equiv/check.py` PASS; golden runs of the SDL port | NHL95PC |

Naming has no automatic check beyond the label existing, so your review goes on phase 4's PR and on any helper names.

### 8.2 The graph

```
splitter (code) ── per asm module: the C functions whose label lives there (from the names gate's output)
   │
   ├─ worker: collide ─┐  one module, one lens per unit (rename OR move, never both)
   ├─ worker: logic   ─┤
   └─ ...             ─┘
          │
   gates (code): build → frames → names → scope → vanilla
          │ fail: that unit only, with the check output, file and line, scope line and attempt number; max 3, then the advisor
          ▼
   merge (code): regenerate ROUTINES.md / RAM.md (tools/routines.py), the report, baseline
          │
   you: approve the PR
          │
   learning edge: each correction → one line in docs/RULES.md, which the splitter reads
```

Code nodes, not models: the rename list (name_map lineage), the move list (asm module of each label), coverage, hashes.
A model is only needed to name helpers, read a body when the names gate can't decide, and write docs.

### 8.3 Lanes

| Lane | Work | Gate |
|---|---|---|
| Reversible, contained | renames, file moves, docs, test tooling in `test/` | frames + names + scope; you approve without reading every file |
| Reversible, wide | shared host layer, `ram.h` renames, report generator, the 95PC shim | gates + your read of the diff |
| Needs you first | anything that changes `test/expected.txt`, the cost model, the sound driver choice | decision, then gates |
| Never opens | game-logic edits that change hashes in a vanilla port, edits to the 1nput mirror, pushes to INDIO's upstream without his OK, retail bytes on asm `main` | none |

### 8.4 Model tiers and the advisor

| Job | Claude | Cursor |
|---|---|---|
| Running checks, coverage, logs, bookkeeping | Haiku | Composer |
| Renames, moves, gates, test tooling, shim functions | Sonnet | Grok medium |
| Helper naming, the EA library and driver C | Sonnet, with the advisor | Grok 4.7 medium |
| Advisor: before a phase plan is fixed, after the same failure twice, before a phase is called done | Opus | Grok 4.7 high |

### 8.5 Night shift

Every night: build both INDIO ports, run `test/check.sh` and the names gate; once phase 2 lands, one lockstep session in rotation;
for 95PC, `make` MATCH, the equivalence suite, and the SDL golden runs once F5 exists. A morning report: what broke, what got
worse and why, coverage movement. Fix PRs open for review, and nothing merges by itself. The ROM and EXE never go into git; the
night job reads them from a private location you set up once.

### 8.6 Working with INDIO

Both C repos are forks of his. Phases 0, 4, 5 and the test tooling are the kind of change he can take upstream, so offer each
as a PR to him, so the forks don't drift. Two asks for him: the `ninety-four-snes` oracle tools (S1), and the ninety-four commit
`d503a46` his hashes came from (E1).

## 9. Decisions for you

1. **Base: 1nput's ninety-four for Genesis** (your call, 2026-11-03), with a `VANILLA=1` build and gens94-c kept as a cross-check.
2. **Slowdown: an option, off by default** (your call, 2026-11-03). Smooth stays the default on Genesis. The cost model (phase 7)
   becomes an opt-in "Original speed" setting, and E6 checks lag frames only in that mode. For the SNES port, the matching
   choice would be Smooth as the default too. That flips INDIO's current default, so it's a question for him.
3. **Flat `game/<module>.c` (drop the play / screen / menus / sound / system folders).** I recommend flat, so that one path pairs
   with one asm file. The alternative keeps INDIO's grouping as an extra level the asm repos don't have.
4. **95PC non-x86 order: 32-bit targets first (wasm32, armv7), 64-bit later.** I recommend this, because 32-bit avoids the
   pointer-width rewrite until everything else works.
5. **95PC sound: translate the SB/OPL driver to C over the emulated chips (faithful), not a new host sound API.** I recommend this.
