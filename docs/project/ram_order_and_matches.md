# RAM map order and missed matches: 92G, 93G, 93S, 94G, 94S

Files: NHL92Genesis `src/ram.asm` (reference, not changed), NHLPA93Genesis `src/ram93.asm`, NHLPA93SNES
`src/ram93s.asm`, NHL94Genesis `src/ram94.asm`, NHL94SNES `src/ram94s.asm`. Names are matched the way
nhl-disasm-report matches them (lowercase, plus the 94G `name_map.csv` lineage). Every build still matches
its ROM byte for byte (93G Rev 0 / A / B, 93S, 94S; 94G unchanged).

## Canonical order

One merged order: 92G first (fixed), then 93G, 94G, 93S, 94S, each game adding its own symbols after the
matched symbol they follow in that game. 92G anchors it because it is the reference and the ancestor of all
four; the 93G and 94G headers already say they follow it, and both SNES files already said they follow 93G.

The Genesis files allocate RAM with `rs`, so the order of `rs` lines is the memory layout and cannot change
without changing addresses. Only `=` / `equ` lines move there. The SNES files are all explicit `=`, so any line
can move (except that asar rejects a forward label reference, so a moved alias is written as its value).

## Result: matched symbols out of order, per pair

| pair | before | after | what is left |
|---|---|---|---|
| 92G-93G | 3 | 3 | `lldisp`, `DMAlistend` (93G `rs` layout), `GGSleft` (see below) |
| 92G-94G | 3 | 3 | same |
| 92G-93S | 1 | 1 | `GGSleft` |
| 92G-94S | 11 | 1 | `GGSleft` |
| 93G-94G | 11 | 10 | `DispAttribCtr` .. `TestList`: 94G moved these `rs` lines (its own comment says so); `playoffscroll`, `scoutcolumn`, `titlescrollspeed` are aliases that stay with `DispAttribCtr` |
| 93G-93S | 3 | 2 | `lldisp`, `DMAlistend` (93G layout; 93S follows 92G) |
| 93G-94S | 15 | 1 | `lldisp` |
| 94G-93S | 12 | 9 | the 94G `rs` moves above |
| 94G-94S | 37 | 8 | the 94G `rs` moves above |
| 93S-94S | 15 | 0 | |

Everything left is an `rs` layout difference between the Genesis games (or an alias tied to one).

`GGSleft` is kept where it is on purpose: in 92G it is `= stickhand`, in 93G/94G/93S/94S it is `= aggress`
(94G `name_map.csv` notes it). Moving it next to `stickhand` would put it beside the wrong field.

## Moves

* **93G**: `GoalieStruct` ($FFFFAFCA) moves from beside `varstart` to after the puck equates, where 94G defines
  it as `SortCords-SCstruct` (SortCords is $FFFFB04A in the 93G listing).
* **93S**: `PadRaw3`, `PadRaw4` and the ReadPads state (`padlast1`, `padnew1`, `padvcount`, `cheatpads`) join
  `PadRaw1`/`PadRaw2` at the 93G position; `CC_Font1Pal3` after `CC_Font1Pal1` (94G order);
  `PenaltyBufferEnd` before `PenBuf` (93G order).
* **94S**: the pad read block (`PadRaw1-5`, `padlast1`, `paddir`, `padchange`, `padnew1`, `padchangeany`,
  `padinputdone`) moves next to `puckcross` / `ltplayer`; `CC_Font1Pal2`/`Pal3` in palette order; `pf*`,
  `pf2*`, `gm*`, `sf*`, `sf2*`, `sf3*` masks in the 92G bit order; `tmflcc` after `tmflags`; `tmpasses` before
  `tmpasscomp`; the 94-only team stats (`tmPerGoals` .. `tmPenShotGoals`, with 94S-only `tmSHShots` and
  `tmOneTimerSwings` in their group) in 94G order after the per player arrays; `textsave` beside `textmap2`.
* **94G**: no change needed.

## Missed matches: applied (renames in 94S)

| 94S old | new | conf. | evidence |
|---|---|---|---|
| `padlast` | `padlast1` | EXACT | 94S `GetNewPresses` and 93S `ReadPads .new` both do new = (raw eor last) and raw, then last = raw, per pad |
| `padnew` | `padnew1` | EXACT | the "new presses" array of the same code; 94S has 5 pads, 93S 4 |
| `pausesavebuf` | `textsave` | EXACT | 94S `Pausemode` copies textmap there and back; 93S `Pausemode` saves textmap to `textsave`, `PauseExit` restores it |
| `tmpassatt` | `tmpasses` | EXACT | 94S `dopass` adds 1 per pass and `TeamStatSources` pairs it with `tmpasscomp`; 94G `dopass` `addq #1,tmpasses(a2)` and its stat table pairs `tmpasscomp,tmpasses`; 93G the same |

Name direction: the older game's name wins when both are SNES-only (93S before 94S), the Genesis name when
one side is Genesis.

## Not applied

| symbol | candidate | conf. | why |
|---|---|---|---|
| 93S `SFXstop` / `SFXstop2` | 92G `SFXskatestop` | LIKELY | same meaning (skate stop sound), but 92G only defines it as -1 and never plays it, so there is no use to compare |
| 94S `ppenmin` | 94G raw `$102` (penalty94.asm `addi.w #$102,d0`, "per-player penalty minutes byte at $102+pnum") | EXACT job | 94G has no name for it; naming it would be a new equate in 94G, not a rename |
| 92G `VRsize` (sort struct +$10) | 93G/94G unnamed slot between `VRoffs` and `VRchar` | POSSIBLE | would be a new equate; not checked for use |
| 94S `homepicaddr` / `vispicaddr` | 94G `homepicchars` / `vispicchars` | POSSIBLE | 94S is the source address of the picture tiles, 94G the VRAM tile base |
| 94S `sopathnext` / `sopathside` / `sopathface` | 94G `sopathend` / `sopathdir` | POSSIBLE | same shootout path, different fields (94G end distance and pass direction from the path table) |
| 94S `puckzfrac` | 93S `Zfrac`+puck | POSSIBLE | 94S keeps Z only for the puck |
| 93S `mula` / `mulb` | 94S `r1` / `r2` | NO MATCH | 94S math routines (`Mul16U`, `Div32U`) are a different implementation using general scratch registers |

Checked and SNES-only or game-only (NO MATCH): 92G `FrameList`, `tempmap`, `Voffset`, `SprStr*`, `optionsmenu`,
`tmFightsWon` (dropped in 93); 93G backup RAM serial EEPROM variables, `rosslide`, `tmrosstep` (93G roster
slide, absent on SNES); 93S sound driver queue, sprite tile cache (`spr*`), music cues (`goalcue`, `midpercue`,
`cuetimer`), `ffo*`/`sso*` arrays (94S engine is a rewrite: different NMI, sound and OAM code).

Method: symbol windows between matched neighbours in each pair, name similarity, an opcode-aligned vote over
same-named 93S/94S routines, and the routines that read each candidate, read in both games before a rename.
