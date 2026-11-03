# SNES bank names: preview of the Grok aligned scheme

Preview only. Nothing in either repo has been renamed.

Source: the final "aligned" tables from the Grok conversation, with its shared label set
(Engine, Samples, Rink, Teams, Sprite Frames, Sound, Scouting, Screens / Frontend, Playoffs, Logos, Fonts, Game, Flow).
Filenames keep the repos' `bXX_snake_case.asm` style. One choice I made: Grok's '93 table still says
"Sprites +", but its shared set says "Sprite Frames", and '94 already uses `spriteframes`. So I used
`spriteframes_` on the '93 side, which is what the "name it the same in both" rule implies.

## NHLPA Hockey '93 SNES (NHLPA93SNES/src/banks)

| Bank | Current file | Grok name | New file | Fits the contents? |
|---|---|---|---|---|
| $80 | b80_engine | Engine | b80_engine (no change) | Yes |
| $81 | b81_samples | Samples | b81_samples (no change) | Yes. Only `gamesound.asm` |
| $82 | b82_samples_rink | Samples + Rink | b82_samples_rink (no change) | Mostly. Code starts at $82B86C after the $81 samples spill over, then `frames93s`, rink tiles, password and SPC upload routines |
| $83 | b83_teams | Teams | b83_teams (no change) | Yes. Also the small font, rink maps and palette, and pause screen |
| $84 | b84_sprites_scouting | Sprites + Scouting | b84_spriteframes_scouting | Yes. Also roster anims, attribute/stats display, HotList |
| $85 | b85_sprites_title | Sprites + Title | b85_spriteframes_title | **Weak.** Only `Title1Map` is here. `TitleScreen.asm` is in $88 |
| $86 | b86_sound | Sound | b86_sound (no change) | Yes. Boot sound driver plus some song-start code |
| $87 | b87_sprites_refs | Sprites + Refs | b87_spriteframes_refs | Yes. Also the EASN backdrop, faceoff tiles, team-block map |
| $88 | b88_sprites_teamblocks | Sprites + Menus | b88_spriteframes_menus | Yes. Game setup, password, title screen, playoff screen, Framer |
| $89 | b89_sprites_replay | Sprites + Replay | b89_spriteframes_replay | Yes. Also the scoreboard, `StartSng*` routines, horizontal ref tiles |
| $8A | b8A_sprites | Sprites + Playoffs | b8A_spriteframes_playoffs | Yes. Bracket map, credits |
| $8B | b8B_sprites | Sprites + Opening | b8B_spriteframes_opening | Yes. Opening, NewPO, ResolveGames |
| $8C | b8C_sprites | Sprites + Logos | b8C_spriteframes_logos | Partly. The only logo is NHLPA. The rest is SpriteSet0 |
| $8D | b8D_sprites | Sprites + Fonts | b8D_spriteframes_fonts | **Weak.** One BigFontTiles blob. Mostly code: MakeTree, InitPPU, StartPer, PeriodOver, updatesound |
| $8E | b8E_sprites | Sprites + Game | b8E_spriteframes_game | Yes. Gameloop, assbench |
| $8F | b8F_frontend | Frontend / HUD | b8F_frontend_hud | Yes. Scoreboard, ticker, intermission, clock, pause exit |

## NHL '94 SNES (NHL94SNES/src/banks)

| Bank | Current file | Grok name | New file | Fits the contents? |
|---|---|---|---|---|
| $80 | b80_engine | Engine | no change | Yes |
| $81 | b81_rink_logos | Rink + Logos | no change | Yes |
| $82-$8E | b82..b8E_spriteframes | Sprite Frames | no change | Yes. Each also holds one filler asset (center ice, a card, a song) |
| $8F | b8F_sound | Sound | no change | Yes |
| $90-$95 | b90..b95_gfx_sound | GFX + Sound | no change | Yes |
| $96 | b96_uniforms | Uniforms + Fonts | b96_uniforms_fonts | **Weak.** About 20 songs, the font tiles, and only 2 uniform palette files. `songs_fonts` would be more accurate |
| $97-$99 | b97..b99_photos | Photos | no change | Yes. Player cards plus songs |
| $9A | b9A_logos | Logos | no change | Partly. Center-ice tiles and maps, logo and photo palettes, cards 139-156, title and setup maps |
| $9B | b9B_screens | Screens | no change | **Weak.** Mostly pad input, Multi5 and the line editor. Title screen is in $9D |
| $9C | b9C_teams | Teams | no change | Yes. `teamdata94s`, stats screens, also the SPC upload/sfx code |
| $9D | b9D_roster | Roster + Scouting | b9D_roster_scouting | Yes. Also the playoff screen, game setup, title screen |
| $9E | b9E_game | Game | no change | Yes. Assignments, collisions |
| $9F | b9F_flow | Flow | no change | Yes. Opening, StartGame, Gameloop, period and pause flow |

## Places where Grok's own "same name in both" rule isn't followed

- **Playoffs:** '93 $8A gets "Playoffs", but '94 $9D holds the playoff screen, MakeTree and NewPO and doesn't get the label. Following the rule would make it `b9D_roster_scouting_playoffs`.
- **Refs:** '93 $87 is "Refs", but '94 has ref tiles and maps too ($95 RefTiles/RefsMapHor, $96 RefsMap) with no Refs label.
- **Title:** "Title" isn't in Grok's shared set. Grok matches '93 $85 to '94 $9B, but neither bank holds the title screen code ('93 $88 and '94 $9D do).
- **Fonts:** in '93 $8D the font is a small part of the bank, while '94 $96 is mostly songs. The label matches on paper but describes neither bank well.

Net effect if applied: 11 renames in NHLPA93SNES, 2 in NHL94SNES.
