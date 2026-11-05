# 94S naming pass against 94G: what changed and what needs your call

Branch `claude/project-thread-ggw7zu`. Every change builds MATCH and passes the pairing gate.

## Applied (role or body match)

| game | old name | new name | why |
|---|---|---|---|
| 94S | `PauseTimeout` | `TimeoutMenu` | pause menu "Timeout" item for team a2: frame, "Timeout", team name, rest the players, wait |
| 94S | `PauseGoalie` | `Pausemode_go` | pause menu goalie item: pick team a2's goalie or pull him, then `setpersonel` (94S cycles, 94G shows a list) |
| 94S | `PauseGoalieMode` | `ManualGoalieMenu` | pause menu "Manual Goalie" toggle. Folder `period/` (94G `period94`) |
| 94S | `ReloadRink` | `ExitStatsScreen` | every pause screen leaves through it: screen off, then the rink again (94G: forceblack, then `ReloadRinkGraphics`) |
| 94S | `GetPlayerRecord` | `GetPlayerNamePointer` | a0 = roster record of player d0 of team a2; same callers (`getname`, `FormatPlayerNumInitial`) |
| 93S | `GetRosterEntry89` | `GetPlayerNamePointer` | the same routine in 93S; 93G has both `GetRosterEntry` and `GetPlayerNamePointer`, and this is the one `getname` calls |
| 94S | `Reset` | `Start` | the reset entry; 93S and 94G both call it `Start` |

## Unsure: your call

Each one does the same kind of job, but the steps are different enough that I left the 94S name.

1. `ScrollPenaltyDown/Up`, `ScrollScoringDown/Up`, `ScrollGameStatsDown/Up` vs 94G `UpdatePenaltyScroll`, `UpdateScoringScroll`, `DisplayPenaltyLineDown`... 94S scrolls one page at a time with the IRQ scroll registers, and 94G scrolls line by line.
2. `DrawEditLinesBack` + `DrawEditLinesTitle` vs `DrawTeamScreen`. 94S splits one 94G routine into two.
3. `DrawPlayerStatsPage` vs `DrawStatsList`. Both draw the header and rows of the stats screen, but 94S copies from a page buffer.
4. `ClearEditLinesMenu` vs `ClearLineEditorTop` / `ClearLineArea`. Each one erases a different area.
5. `ScoutHomeArena`, `ScoutHomeCity`, `ScoutVisNick`... vs `GetTeamArena`, `GetTeamCity`, `GetTeamNickname`. 94S has the text code handler, and 94G has the lookup that the handler calls.
6. `CheckCrowdMeter` / `UpdateCrowdMeter` vs `Crowd_Noise`. Both do the meter, but 94G also switches the crowd noise.
7. `NMI` / `NMI_Fast` vs `VBlank` (93S `VBlank`). 94S runs its frame work through hooks, so there is no single routine that matches.
8. Already rejected in `docs/unmatched_vs_94g.md`: `PauseFromPad` (one routine standing in for `startpause2/3/4`), `EndPenaltyShot` / `EndPenaltyShotPlay`, `FadeOut` / `forcefade`.

The rest of the 94S-only routines are SNES machinery with no 94G partner: heap, math, DMA and IRQ, the Multi5 adaptor, password and title zoom.

# Round 2: the 8 split or merged pairs (applied)

Your call: all 8 applied, 24 labels in 94S. Where 94S splits a 94G routine, the entry takes the 94G name and each extra piece is `<94G name>_<part>`. Where one 94S routine stands for several 94G ones, it takes their stem plus a suffix. The list is in 94S `docs/unmatched_vs_94g.md`.

Also found on the way: 94S and 93S `pucknothing` both become `puckunflip`. The body is the 93G/94G `puckunflip`, and the 93G `pucknothing` is only a `bra` to it.

# 95PC naming (F3)

Applied, with MATCH in both builds:

| old | new | why |
|---|---|---|
| `holdplayer`, `Readjoy1`, `Readjoy2`, `StopNA`, `puckIChk` | `Holdplayer`, `ReadJoy1`, `ReadJoy2`, `stopna`, `PuckIChk` | the 94G spelling of the same 93G routine |
| `IntermissionStart`, `defaultsprites2`, `ProcessPenaltyList` | `PeriodOver_sp`, `defaultsprites_0`, `updatepentime_ut` | 94G renamed these 93G names (94G name_map) |
| `CheckAndReleasePlayer` | `updatepentime_ut_chk` | the 93G `.chk` part, under the 94G name of its parent |
| `LockScroll` | `freezewindow` | the 94G body exactly (95G made the same rename) |
| `GameLoop` | `Gameloop` | role: the in-game loop |
| `StartShotPath` | `StartShootoutPath` | role: starts the shootout skate path (PC builds the path, 94G picks one) |
| `CrowdNoiseUpdate` | `Crowd_Noise` | role: the crowd noise each frame (PC MIDI) |
| `PassRecOneTimer` | `assonetimer` | role: the one-timer shot when the pass arrives |

Unsure, your call:

1. `ReplayPrevFrame` / `ReplayStep`, compared with 94G `suba4` / `adda4`. PC steps the record pointer, and steps the play pointer by N frames.
2. `PenTeamScored`. It checks whether a goal cancels a delayed penalty. It's close to `releasepl`, but not the same job.
3. `ass_pc_slot20`. This is asstab slot 14h, which is `assfight` in 93G, but the body is not fight code.
4. `PuckCheckColl`. This is the collision part of the 93G `pucknorm`. One option is `pucknorm_coll`, like `pucknorm_body`.

95G names for the 95 features (season, trades, awards): 95PC has almost none of them under a 95G name. Matching those needs a body-by-body pass across 68000 and x86. That's a bigger job, and I'd plan it separately.
