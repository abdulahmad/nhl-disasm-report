# How the NHL 95 PC programmers probably laid out their source

This is analysis only. Nothing in NHL95PC has changed yet.

## Short answer

* **Yes, bigger groups make sense, but they should be the PC's own groups, not 95G's.** The EXE was linked from Watcom C modules, and each module is still one unbroken stretch of code. The compiler left clues that show which functions shared a `.c` file. Those clues prove 84 multi-function modules in the game code, holding 821 of its 1,163 functions. The largest one has 57 functions.
* **The PC modules don't follow the 95G files.** For example, the proven module `burst` .. `ReturnGoalies` (now `engine/collide.asm`) is one C file. It holds routines that 95G keeps in `collide95` (20), `input95` (10), `logic95` (7) and `penalty95` (4). If we filed each function under its 95G (or 94G) file, as on the card I sent earlier, we would tear real modules apart. That's why I'm changing my recommendation (see the end).
* **The current 95PC files are cut in the wrong places in 17 spots.** In each spot, one proven module runs across two files, so 12 groups of current files should be joined. Several other files hold more than one module.

## The clues

| clue | why it shows one module | count |
|---|---|---|
| shared exit: a jump into another function's tail (`X_popx`, `X_ret`, `loc_` inside it) | Watcom merges tails only inside one compilation unit | 402 pairs |
| one string literal used by two functions | each module has its own literal pool | 4,065 data labels read, 1,316 in the literal pool |
| literal pool order | the linker puts each module's literals (CONST) in link order, so a later function that uses an earlier literal must be in the same module | used as a check (0 conflicts) |
| matched C files with more than one function | 76 matched `.c` files hold 2+ functions, and they only match when built together | 76 files |
| the same string text stored twice | Watcom keeps one copy per module, so two copies mean two modules | 147 pairs: only 2 clash with the rules above |

None of this can prove where a module **ends**. Of the duplicate-string pairs, only 6 pin down an exact boundary. So these are minimum groups: two neighbouring groups might still be one file.

## The joins of current files (corrected in the review: 11 crossings, see 95pc_file_names.md)

Each row is one proven module that runs across these current files:

| files to join | proof |
|---|---|
| front/main + pc/gamesave_io + front/stats_team + pc/asset_loading | shared exits (HandleHotKey_ret, PickAwardWinners_x), the awards C file |
| pc/file_utils + front/scoreboard + front/title | shared exits, DrawHudPanel and RunDemoGame C files |
| pc/output_files + pc/palette_fx | shared exits, one C file |
| front/desk_main + pc/temp_files | MainDeskLoop's shared exits |
| front/calendar + pc/import_export | a shared literal |
| engine/init + engine/logic | intro and three stars: FadeOutPalCycle's C file |
| engine/input + engine/faceoff | lineinput .. asspassrec |
| pc/joystick_calibration + pc/database_save + front/create | shared exits, one C file |
| front/lines (from GameLineEditor) + front/team_select | shared literals. A moved cut, not a join: the league line editor is its own module (review) |
| engine/replay + front/highlights | DrawGadgetButton's C file |
| pc/sound_config + front/speech + front/announcer | one speech module (ShutdownSpeech.c) |

## What the engine probably looked like (EXE order)

These are the proven groups plus the single functions between them, named by what they do:

| EXE range | likely PC module | holds | 95G files its functions come from |
|---|---|---|---|
| 47C31-499D7 | pre-game intro, three stars | FadeOutPalCycle .. assthreestars (15) | PC only |
| 499D8-4FCE7 | assignments | assboxenter, assdefd .. assrefgoalline (47), asspenshooter | logic95, faceoff95 |
| 4FCE8-51114 | input, line changes | joyq_*, lineinput .. asspassrec (17) | lines95, input95, control95, video95 |
| 51115-53293 | faceoff | TakePlayerFromBox .. asstakeposition (10), assrefpenshot | faceoff95 |
| 53294-59492 | puck, pass, shot and CPU control | burst .. ReturnGoalies (57), ChkPullGoalieLate | collide95, input95, logic95, penalty95 |
| 59493-59D99 | sound, crowd and announcer hooks | SndLoadFile, Crowd_Noise, Pa* | sound95 |
| 59D9A-5E16C | players, game setup, periods | SetSPA .. ResetBench (51), StartGame | middle95, players95, goal95, hockey95 |
| 5E16D-5FB02 | skating | doplayeracc, EvadePlayers .. stopna (9), goalieacc | skate95, logic95 |
| 614C2-644A7 | rink objects, deferred calls, penalties, penalty shot | RunDeferredCalls .. (13), InProgress .. ShotLaneOpen (16) | penalty95, lines95 |
| 644A8-6733x | lines, banners, team palette | BuildDefaultLines .. (11), checkwindow .. DrawCallBanner (6) | PC only, goal95 |
| 67564-69335 | replay steps | ReplayRecordReset .. ReplayStep | PC only |

The PC programmers seem to have grouped the engine by jobs of their own. Each job pulls from several 95G files, the same way 95G pulls from several 94G files.

## What this means for "make them match"

* **Folders follow the PC modules.** One file per reconstructed module, in EXE order. The folder and file names use the 95G or 94G subsystem name where a module is clearly that job (`engine/skate`, `engine/faceoff`, `engine/assign`). Otherwise the name says what the module does (`engine/puckcontrol`).
* **Cross-game matching lives in the names, not the files.** Each function keeps its 94G name. The report already shows where each one lives in 94G, 95G and 94S, and `95pc_engine_files.csv` lists all four homes.
* **No regressions.** It's only text moves: the bytes, the C files and the matched set stay the same. Every step must build MATCH in both builds (CBUILD=1 and 0), and the number of matched functions in `tools/c_functions.csv` must stay at 922.

Scripts and raw tables: in the session scratchpad, `mod/` (parse.py, ent.py, blocks.py). I can move them to `NHL95PC/tools/` if you want them kept.
