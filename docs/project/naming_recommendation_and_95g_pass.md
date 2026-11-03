# Naming: recommendation on the 4 unsure 95PC pairs, and the plan for the 95G body-by-body pass

## 1. The 4 unsure pairs: what the bodies say

| 95PC now | recommendation | why (from both bodies) |
|---|---|---|
| `PuckCheckColl` | **rename to `checkpuckcoll`**, and the current 95PC `checkpuckcoll` becomes **`checkpuckcoll_ccx`** | `PuckCheckColl` is the 94G `checkpuckcoll` step for step: it stops the puck past y 190h, returns when Z is above 16, then walks the OOlist up and down within 40 and runs the per-object test on each one. The function 95PC calls `checkpuckcoll` is that per-object test, which is the 94G local `.ccx`. 94S already calls it `checkpuckcoll_ccx`. So the two names are off by one level, and with the fix all three games agree. |
| `ass_pc_slot20` | **rename to `assstarskate`** (a PC name) | This is asstab entry 20 (14h). 94G has `assfight` in that slot, but 95PC has no fights and reuses the slot. `StartThreeStars` gives each star this assignment, between `assleaveice` (1Dh) and `asseben` (9): skate a 4-point path, and maybe stop at a random point for SPA 731h. That's the three stars skate, which only the PC has. The current name, and the "slot 20h" in its comment, read as hex; the slot is really 20 decimal. |
| `PenTeamScored` | **keep** | During a delayed penalty it checks whether the team that scored has the player who caused the penalty. If so, the goal does not count. 94G and 95G only set and clear `gmpendel` and have no such check, so this is PC only and keeps its own name. |
| `ReplayPrevFrame`, `ReplayStep` | **keep**, adding a comment line that names 94G `suba4` / `adda4` | `ReplayPrevFrame` takes the record pointer back one frame. 94G never steps the record pointer back. `ReplayStep` moves the play pointer N frames either way, with sound, for the PC replay gadgets, where 94G steps one frame per call. That is one PC routine for two 94G jobs, and the stem rule would give a meaningless `a4` name. |

These are cheap to undo, so I'll apply the first two when you say go (MATCH and the gate as usual).

Applied (MATCH twice): `PuckCheckColl` -> `checkpuckcoll`, `checkpuckcoll` -> `checkpuckcoll_ccx`, `ass_pc_slot20` -> `assstarskate`.

## 2. The 95G body-by-body pass: what the pilot showed, and the revised plan

### What I measured
* I built `tools/xmatch95.py` in 95PC. It scores every 95PC function against every routine of one 95G file, using shared strings, shared names (RAM, fields, callees) and shared constants, each idf weighted so common words count for little.
* **Pilot, `trade95`: no body pairs.** The PC trade screen is a DOS rewrite. It swaps one player for one player ("Select first player to trade."), and has no GM decision, no trade value table (the 95G `TradeRatingSteps` bytes are nowhere in 95PC) and no INVALID TRADE rules.
* **The 95G front end overall: same words, different code.** Of 95G front-end routines that print text, the strings 95PC shares with them are generic labels ("agility", "checking", "goalie", "player"), spread over unrelated PC dialogs. That holds for season, create, stats, records, awards and scout too. The PC front end (desk, dialogs, league files) was written fresh for DOS.
* **The engine: a handful of real pairs.** I ran the scorer on the 95G engine files and read the bodies of the best mutual leads. One is clear: 95PC `calcpuckcross` is the 94G/95G `findpc` (where and when the puck crosses each goal line, into `puckcross`). It's applied now. The rest were noise, or PC helpers with no partner (`ChkPullGoalieLate` is a PC test that sits next to the PC's own `CPgoalie`).

### Recommendation (strong)
1. **Don't run a 95G body-by-body pass on the front end.** There are no shared bodies to pair. Renaming DOS dialogs after Genesis screens would claim more than the code shows, and it goes against your own rule (95PC's own name for DOS-only jobs). Those keep their PC names.
2. **Do a short engine-only review instead.** Run `xmatch95.py --pcnew` per 95G engine file, then read the bodies of the mutual leads above a score of 0.8 (about 60 leads in all). Apply the clear ones and the role matches by the suffix rule, and list the unsure ones. I expect 5 to 15 renames, not 100+. It takes about one sitting per two or three engine files.
3. **Write the 95 features in 95PC under their PC names, plus a note.** Where a PC routine does the job of a 95G screen (for example `ShowAwardScreens` and the awards screen), its comment names the 95G routine, so the report can link the two without a rename.
4. **95PC in the report.** Add 95PC to nhl-disasm-report as a fourth view (engine only, by function name), so the remaining gaps can be seen next to 94G and 95G.

### Order
1. Engine review: `logic95`, `collide95`, `goalie95`, `faceoff95`, `penalty95`, `goal95`, `replay95`, `onetimer95`, `hockey95`, `pause95`.
2. The 95G-routine notes in the comments of the PC front-end functions.
3. 95PC in the report.

## 3. Engine review: results

I ran the scorer on the 95G and 94G engine files (logic, collide, hockey, penalty, goalie, one-timer, replay, crowd, video, middle, setup), read the bodies of every mutual lead above 0.7, and went through the evidence of all 120 PC-name engine functions.

Applied (MATCH twice each time, gate OK):

| 95PC old | new | why |
|---|---|---|
| `calcpuckcross` | `findpc` | where and when the puck crosses each goal line (`puckcross`) |
| `StopIfFree` | `donothing` | `doplayeracc` 8 unless `pfalock` or the joystick, the 94G body exactly |
| `GameTimeStamp` | `GetPeriodTimeRemaining` | (gsp << 14) + PerTimeTotal - gameclock, for the scoring and penalty summaries |
| `RestBench` | `RestoreBenchEnergy` | once a second with line changes on, bench players gain energy up to the cap (PC +8, 94G +9) |

Read and kept, with no 94G partner: `ChkPullGoalieLate` (a PC test beside the PC's own `CPgoalie`), `GiveControl`, `clearteams`, `SetupPenaltyShot`, `SetPenaltyStrength`, `GoalieToPuckVec`, `SprSortVert`, the referee and intro assignments, the three stars code, the announcer and the MIDI crowd. The rest of the scorer's leads were noise (a shared flag or two).

The engine review is finished. 95PC now uses the 94G name wherever a body or role matches that I could find.
