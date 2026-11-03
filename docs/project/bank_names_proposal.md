# SNES bank names: aligned proposal (v2)

Preview only. Nothing in either repo has been renamed.

## Rules

1. **Dominant content first.** Tags are ordered by bytes. A bank gets a tag for anything that is about 20% or more of it, or that is the bank's distinctive code.
2. **Cross-naming.** Every tag used in one game is also used in the other. It goes on the bank that holds the most of that content, provided there's at least about 1 KB of it. So if '93 names *refs*, '94 names its ref bank too, and the reverse.
3. **One vocabulary:** engine, game, flow, hud, sound, songs, samples, spriteframes, rink, logos, teams, scouting, stats, setup, playoffs, title, refs, replay, fonts, crowd, photos.

Only two tags appear in one game alone. `photos` exists only in '94. `crowd` is under the floor in '93, where `showcrowd` is about 450 bytes.

Measurement: for '93, the address gaps in `docs/file-map.md`. For '94, the incbin ranges, plus code size estimated from the source. '94's `teamdata94s` is a generated file and wasn't measured, so $9B-$9F are approximate.

## Tag pairs (where each tag lives in each game)

| Tag | '93 bank | '94 bank |
|---|---|---|
| engine | $80 | $80 |
| game (AI, assignments, collisions) | $80 | $9E |
| flow (game loop, periods, clock) | $8F | $9F |
| hud (scoreboard, ticker, clock display) | $8F | $9F |
| sound (SPC driver) | $86 | $80 (`SoundDriver`) |
| songs | $86 | $96, $8F, $97 |
| samples | $81, $82 | $8E, $8F, $90-$96 |
| spriteframes | $84-$8F | $82-$8E |
| rink | $82, $83 | $81, $9A |
| logos | $8C (NHLPA logo) | $81, $94 |
| teams | $83 | $9C |
| scouting | $84 | $9D |
| stats | $84 | $9B, $9C |
| setup | $88 | $9D, $93 (setup backdrop tiles) |
| playoffs | $88 | $9D |
| title | $85 | $91 (title sprites/tiles) |
| refs | $89 | $95 |
| replay | $89 | $9B |
| fonts | $8D | $92 |
| crowd | (under 1 KB) | $90 |
| photos | (none) | $97-$9A |

## NHLPA Hockey '93 SNES

| Bank | Measured contents | Current | Proposed |
|---|---|---|---|
| $80 | game logic 68%, core engine 14% | b80_engine | **b80_engine_game** |
| $81 | samples 100% | b81_samples | b81_samples (no change) |
| $82 | samples 44%, rink 34%, frame tables 16% | b82_samples_rink | b82_samples_rink (no change) |
| $83 | team data 55%, rink map/palette 33% | b83_teams | **b83_teams_rink** |
| $84 | sprite frames 70%, scouting 16%, stats/attrib display 3% | b84_sprites_scouting | **b84_spriteframes_scouting_stats** |
| $85 | sprite frames 69%, title backdrop 29% | b85_sprites_title | **b85_spriteframes_title** |
| $86 | SPC driver + music + sfx 95% | b86_sound | **b86_sound_songs** |
| $87 | sprite frames 82% | b87_sprites_refs | **b87_spriteframes** |
| $88 | sprite frames 53%, team banners + setup 25%+, playoffs/password/title code | b88_sprites_teamblocks | **b88_spriteframes_setup_playoffs** |
| $89 | sprite frames 80%, refs 12%, replay code | b89_sprites_replay | **b89_spriteframes_refs_replay** |
| $8A | sprite frames 94% | b8A_sprites | **b8A_spriteframes** |
| $8B | sprite frames 94% | b8B_sprites | **b8B_spriteframes** |
| $8C | sprite frames 93%, NHLPA logo | b8C_sprites | **b8C_spriteframes_logos** |
| $8D | sprite frames 80%, big font 7% | b8D_sprites | **b8D_spriteframes_fonts** |
| $8E | sprite frames 95% | b8E_sprites | **b8E_spriteframes** |
| $8F | sprite frames 53%, scoreboard/ticker/clock + flow code | b8F_frontend | **b8F_spriteframes_hud_flow** |

## NHL '94 SNES

| Bank | Measured contents | Current | Proposed |
|---|---|---|---|
| $80 | engine code, SPC sound driver | b80_engine | **b80_engine_sound** |
| $81 | logos 64%, rink 34% | b81_rink_logos | b81_rink_logos (no change) |
| $82-$8D | sprite frames 98-99% | b8X_spriteframes | no change |
| $8E | sprite frames 68%, samples 28% | b8E_spriteframes | **b8E_spriteframes_samples** |
| $8F | samples 73%, title song 25% | b8F_sound | **b8F_samples_songs** |
| $90 | samples 48%, crowd 26%, songs 23% | b90_gfx_sound | **b90_samples_crowd** |
| $91 | samples 66%, title 17%, cards 16% | b91_gfx_sound | **b91_samples_title** |
| $92 | samples 70%, letter/font sprites 15%, rink map 13% | b92_gfx_sound | **b92_samples_fonts** |
| $93 | samples 64%, setup backdrop 13% | b93_gfx_sound | **b93_samples_setup** |
| $94 | samples 65%, EA/title logos 25% | b94_gfx_sound | **b94_samples_logos** |
| $95 | samples 62%, refs 18% | b95_gfx_sound | **b95_samples_refs** |
| $96 | songs 50%, samples 20%, fonts 7% (uniforms are 2 palettes) | b96_uniforms | **b96_songs_samples** |
| $97 | photos 69%, songs 26% | b97_photos | **b97_photos_songs** |
| $98-$99 | photos 85-91% | b9X_photos | no change |
| $9A | photos 33%, center-ice rink tiles/maps 24% | b9A_logos | **b9A_photos_rink** |
| $9B | stats screens, replay, crowd meter, password, line editor | b9B_screens | **b9B_stats_replay** |
| $9C | team data, stats screens, SPC upload code | b9C_teams | **b9C_teams_stats** |
| $9D | game setup, playoffs, scouting, roster, title screen | b9D_roster | **b9D_setup_playoffs_scouting** |
| $9E | game logic ~74% | b9E_game | b9E_game (no change) |
| $9F | game loop, periods, scoreboard printing | b9F_flow | **b9F_flow_hud** |

Renames needed: 14 in NHLPA93SNES (all but $81 and $82) and 17 in NHL94SNES.

## Judgment calls

- `password` and `lines` are left out of the vocabulary. They'd add a fourth tag to '93 $88 and '94 $9B. If you want them, they pair as password ($88 / $9B) and lines ($8F / $9B).
- '94 $81 stays `rink_logos` to avoid a rename, though logos are the larger share.
- Three-tag names ('93 $84, $88, $89, $8F and '94 $9D) are the cost of the cross-naming rule. Dropping the 1 KB floor to cover small scraps would make them longer.
