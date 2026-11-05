# Folder preview: 93G, 94G, 93S, 94S after the plan

Preview only. Counts are routine files, measured from today's `main`. Part of 94S `hockey/` is still marked
"until C4", because where those routines go depends on the C4 placement pass.

## The examples, before and after

| Routine | Repo | Today | After B (93S passes) | After C1 + C4 | After C6, if you pick option 1 | After C6, if you pick option 2 |
|---|---|---|---|---|---|---|
| `asswingd` | 93S | `routines/logic/assignments/asswingd.asm` | same | same | same | same |
| `asswingd` | 94S | `routines/logic/asswingd.asm` | same | same | `routines/logic/assignments/asswingd.asm` | same (flat) |
| `checkcoll` | 93S | `routines/hockey/collisions/checkcoll.asm` | `routines/hockey/collide/checkcoll.asm` | same | same | same |
| `checkcoll` | 94S | `routines/collide/checkcoll.asm` | same | same | same, no subfolder (the 93S area is `collide`, the same as the top folder) | same |
| `Goal` | 93S | `routines/hockey/game/Goal.asm` | `routines/hockey/collide/Goal.asm` | same | same | same |
| `Goal` | 94S | `routines/hockey/Goal.asm` | same | `routines/collide/Goal.asm` | same | same |
| `getname` | 93S | `routines/hockey/teams/getname.asm` | `routines/hockey/setup/getname.asm` | same | same | same |
| `getname` | 94S | `routines/hockey/getname.asm` | same | `routines/setup/getname.asm` | same | same |
| `chkatop` | 93S | `routines/stats/chkatop.asm` | `routines/penalty/chkatop.asm` | same | same | same |
| `chkatop` | 94S | `routines/penalty/chkatop.asm` | same | same | same | same |

My earlier example `collide/collisions/checkcoll.asm` was wrong. Once B2 renames the 93S area to `collide`, the 94S
subfolder would repeat the top folder, so it's dropped. In practice, the second level in 94S only appears inside
`logic/`, `penalty/`, `middle/` and `video/`, where one 94G file covers several 93S areas.

Option 1 = 93S areas as a second level inside 94S. Option 2 = 94S stays flat inside each 94G folder.

## 93G (no change)

```
src/
  hockey93.asm (top, includes the rest), main93, logic93, penalty93, stats93, middle93, video93,
  print93, decompress93, menu93, sram93, checksum93, tables93, teamdata93, frames93, graphics93, ram93
  sega/   SegaIDTable93, SegaInit
  sound/  sound93, z80_snd_drv93
  macros/
```

## 94G (no change)

```
src/
  nhl94.asm (top), main94, hockey94, setup94, collide94, logic94, penalty94, period94, stats94, cards94,
  scout94, shootout94, onetimer94, arena94, shootoutpath94, ui94, helpers94, fourway94, crowd94, replay94, records94, title94, logos94, chgplayer94, menu94,
  optsetup94, middle94, video94, print94, decompress94, sram94, checksum94, tables94, teamdata94,
  frames94, graphics94, ram94
  sega/   segacd/   sound/   macros/
```

## 93S after Stage B

Top folders are the 93G modules (unchanged). The areas under `hockey/` are named after the 94G file their routines went to.

```
src/
  nhlpa93snes.asm   ram93s.asm
  banks/        b80_engine_game ... b8F_spriteframes_hud_flow   (16, ROM order; names per the bank-names proposal)
  header/       snes_header.asm
  inc/          snes_regs.asm
  macros/       snes93.mac
  data/
    frames93s.asm   teamdata93s.asm
    gfx/  sound/  text/
    tables/       Penaltylist, linelist, priolist, sublist, asstab, ...   (B3: from routines/tables, as 94S has it)
  routines/
    hockey/
      game/       23   (hockey94 part)
      setup/      29   (was spread over teams/, screens/, game/)
      collide/    37   (was collisions/ + parts of teams/ and game/)
      password/   14   playoffs/  7   replay/  7
      title/  1   optsetup/  2   scout/  1
      screens/  9   teams/  11   display/  3   util/  3   input/  1   interrupts/  2   players/  1
                       (left: no 94G counterpart; these stay as they are)
    logic/        assignments 27, skating 20, puck 19, controls 15, lines 8, offsides 7, computer 6,
                  contact 4, animation 2, collisions 2, display 1, players 1
    penalty/      penalties 21, scoreboard 13, ticker 9, energy 5, highlights 3, util 1, + 4 flat (chkatop, ChkShotStat, AdvanceStringPtr, dobar)
    middle/       math 15, input 8, util 4, + 4 flat (sfx, forceblack, remap, waitjoy)
    video/        interrupts 11, objects 8, sprites 8, text 4, hud 3, rink 3, crowd 2, dma 1, + updatesound
    stats/  17    print/  12    sound/  17    decompress/  1    main/  1
```

## 94S after Stage C (option 1 shown)

Top folders are the 94G files. The second level is the 93S area, and only appears where it differs from the top folder.

```
src/
  nhl94snes.asm   ram94s.asm
  banks/        b80_engine_sound ... b9F_flow_hud   (32, ROM order)
  header/  inc/  macros/
  data/         frames94s.asm  teamdata94s.asm  gfx/  sound/  tables/  text/
  routines/
    hockey/     about 30 after C4 (the hockey94 part: game/ 20, plus the 94S-only flow routines)
                176 today that are still to be placed by C4: pause menu, stats pages, line editor, password and title
                helpers. They move to the folders below, by the 94G file of their callers.
    setup/      26 + password/ 8 + playoffs/ 5 + teams/ 1    (+ C4 arrivals)
    collide/    33 + Goal and the other moves from hockey/
    logic/      23 flat (94 and SNES-only) + assignments 24, puck 17, skating 15, controls 8, lines 8,
                offsides 7, computer 6, animation 2, collisions 2, display 1, players 1
    penalty/    10 flat + penalties 20, scoreboard 12, ticker 9, energy 5, highlights 2, util 1
    middle/     74 flat (SNES engine: math, heap, DMA queue, pads) + input 3, math 4, text 3, util 2, rink 1
    video/      64 flat (SNES engine: NMI, IRQ, PPU, sprites) + hud 3, objects 3, crowd 1, rink 2, sprites 2
    stats/      30   period/  5   cards/  5   scout/  3   shootout/  13   replay/  6   crowd/  1
    optsetup/   1    title/  1    print/  7 (new, from middle/)
    sound/      56   decompress/  5   main/  4
```

The 94 features (`cards`, `period`, `scout`, `title`, `optsetup`, `crowd`) are small today, because their routines
are still in `hockey/` with names that have no 94G partner. C4 and C5 fill them.

## 95PC: proposed shape (for Stage F)

Today: `src/cseg01/` has 198 asm files and `src/c/` has 63 folders of C, all named `NNN_ADDR_topic` (`037_4842A_engine_player_logic`).
The link order is in `src/segments.txt`. Each segment is most likely one original C source file.

| | Option A (recommended) | Option B (minimal) |
|---|---|---|
| Layout | `src/c/engine/`, `src/c/front/`, `src/c/pc/` (DOS-only: file I/O, memory, sound cards, dialogs), `src/c/lib/` (Watcom, CD stream, GUS), with matching `src/asm/...` | keep `cseg01/` and `c/` |
| Module names | named after the 95G file it pairs with, without the year: `engine_player_logic` → `engine/logic`, `engine_skating` → `engine/skate`, `engine_input` → `engine/input`, `line_editor_rosters` → `front/lines`, `trades` → `front/trade`, `create_player` → `front/create`, `scoring_penalty_text` → `engine/penalty`, `gadgets_replay` → `engine/replay`. PC-only modules keep a descriptive name | keep `NNN_ADDR_topic` |
| Order | `segments.txt` holds the link order (like 95G's include lists), so file names lose the number and address | unchanged |
| Report | `logic` pairs with 95G `logic95` with no hand table | needs a crosswalk |
| Cost | `gen_src.py`, `link_src.py`, `c_progress.py`, `c_functions.csv` and the docs that name paths are updated; MATCH proves it | none |

The module-to-95G pairing comes from which 95G file holds the routines each segment shares names with (a script, A1-style), not by hand.
