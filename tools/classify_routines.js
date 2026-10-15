"use strict";
const fs = require("fs");
const path = require("path");


function loadNDR(docsDir, g) {
  const t = fs.readFileSync(path.join(docsDir, "data", g + ".js"), "utf8");
  return JSON.parse(t.slice(t.indexOf("(") + 1, t.lastIndexOf(")")));
}

function parseLst(path) {
  const addrs = new Map();
  if (!fs.existsSync(path)) return addrs;
  const text = fs.readFileSync(path, "utf8");
  for (const line of text.split(/\r?\n/)) {
    if (/^[0-9A-Fa-f]{8} [0-9A-Fa-f]{2,4} /.test(line)) continue;
    const m = line.match(/^([0-9A-Fa-f]{8})\s{8,}([A-Za-z_][\w.@]*)(?::)?(?:\t|;|=|\s*$)/);
    if (!m) continue;
    const addr = parseInt(m[1], 16);
    if (!addrs.has(m[2])) addrs.set(m[2], addr);
    const low = m[2].toLowerCase();
    if (!addrs.has(low)) addrs.set(low, addr);
  }
  return addrs;
}

function unitFileMap(d) {
  // Prefer deepest (leaf) file containing the unit
  const map = new Map();
  for (const f of d.views.files) {
    for (const ui of f.u) {
      const cur = map.get(ui);
      if (!cur || f.d >= cur.d) map.set(ui, { f: f.f, d: f.d, a: f.a, e: f.e });
    }
  }
  return map;
}

function lineCount(t) {
  if (!t) return 0;
  const parts = t.split(/\n/);
  // trailing empty line doesn't count extra if present
  if (parts.length && parts[parts.length - 1] === "") return parts.length - 1;
  return parts.length;
}

function firstComment(t) {
  const lines = (t || "").split(/\n/).slice(0, 8);
  return lines
    .map((l) => {
      const i = l.indexOf(";");
      return i >= 0 ? l.slice(i + 1) : "";
    })
    .join(" ")
    .toLowerCase();
}

// ---------- classification rules ----------
// Returns {category, subcategory, confidence, why}

let FILE_DEFAULTS = {};

// Ordered name/comment rules: [regex on name, regex on comment, cat, sub, conf]
// Applied after file default; first match wins among overrides that are more specific.
const RULES = [
  // system
  [/^(VBjsr|IRQ7|vb2|ErrorStatus|Start|Reset|InitialSP)$/i, null, "system", "interrupts", "high"],
  [/^(SegaInit|h_s|cold_start|hot_start|reg_init|r_int1|japan|security|CHECK_VDP|reg_set|vreg_dt)$/i, null, "system", "boot/vectors", "high"],
  [/^(z80_clr|z801|z802|clr_wk|c_wk1|clr_col|c_col1|clr_vsc|c_vsc1|clr_psg|c_psg1|dma_fill|dma_fill_mode|z80_reg|new_reg_data|clr_col_data|clr_vsc_data|psg_dat)$/i, null, "system", "memory clears", "high"],
  [/^(SecurityCheck|ValidationRoutine|ValidationLoop|SkipIncrement|ContinueValidation|VDPErrorSetup|VRAMWriteLoop|Halt|Calc_Checksum)$/i, null, "system", "checksum/security", "high"],
  [/header|vector|sega id|cartridge/i, "comment", "system", "header", "high"],

  // video
  [/^(DoDMA|DoDMApro|DoDMA_nd2|DoFill|WaitDMA|DoDMAList|setVram|setVram_0|Vmaddr|dobitmap|setvideo|DumpSprites|DumpSprites2|SetScroll2)$/i, null, "video", "VDP/DMA", "high"],
  [/^(forceblack|forceblack2|forcefade|cramfade|CopyPaletteToCRAM|remap|setupIceRinkPal|setplayercolors)$/i, null, "video", "palettes/fades", "high"],
  [/^(Decompress|Opcode_|UnpackNibbles|UnpackPicture|LoadHomeTeamGfx|dobitmap)/i, null, "video", "tiles/decompression", "high"],
  [/^(addframe|addframe2|find3d|SprSort|defaultsprites|SetSframe|Reload\w+Tiles)/i, null, "video", "sprites", "high"],
  [/^(updatescroll|UpdateCameraPos|UpdateVertScrollReg|UpdateScoresScroll|ClampReplayView|SetCameraTop)/i, null, "video", "scrolling", "med"],
  [/^(RenderSmallFontChar|PrintFont|BigFont|SmallFont|QueuePadLabel|ButtonLabelCharTable|printbig|printsmall)/i, null, "video", "text/fonts", "high"],

  // sound
  [/(_pcm|_cmdstream|pcm_sample|SoundStream|fm_instrument)$/i, null, "data", "sound data", "high"],
  [/^(p_turnoff|p_music_vblank|p_initialZ80|play_sfx_or_music|stop_current_song|UploadCommandBuffer|ProcessOneMusic|command_jump|handle_command|ReleaseChannel|StopPCM|UpdateChannel|ClearAllTrack|Z80_Program|ResetZ80|SetChannelVolume|rtsfx|rtscmd)/i, null, "sound", "driver", "high"],
  [/^(song|ChooseSong|TeamSongs|RandomSongs|CheckLateGameSong|fmtune_)/i, null, "sound", "music", "high"],
  [/^(sfx|sfx_)/i, null, "sound", "sfx", "high"],
  [/^(KillCrowd|updatesound|Crowd_Noise|LoadCrowdRec|stopna2|UpdateCwdExcite|updatecrowdf)$/i, null, "sound", "crowd audio", "high"],
  [/pcm_sample|SoundStream|fm_instrument/i, null, "sound", "driver", "high"],

  // input
  [/^(doinput|Read[Jj]oy|ReadPad|jdtab|nodiag|orjoy|waitjoy|ProcessInputWithRepeat|getpzjoy|FigureJoy|faceoffinput|fightinput|lineinput|burst|holdplayer|Acheck|getGoalie|Detect4Way|Set4Way|ReadJoySwap)/i, null, "input", "controllers", "high"],
  [/4[Ww]ay|fourway|multitap|Pad4Way/i, null, "input", "multitap", "high"],
  [/^(startpause|Pausemode|SetupPauseScreen|seta2)/i, null, "input", "pause", "high"],

  // gameloop
  [/^(Begin|StartGame|StartPer|Gameloop|DoGameFrame|periodicevents|clockcont|ChkShortPeriods|ResetClock|GetPeriodTime|ClearShotData|restoreteams|demoread|EndDemoOnPress|PeriodOver|Intermission|GameOver|ExitToOpening|Opening)/i, null, "gameloop", "frame loop", "high"],
  [/faceoff|FaceOff|puckfaceoff|EndFaceoff|checkfo/i, null, "gameloop", "faceoffs", "high"],
  [/period|intermission|PeriodStats|SetupTeamForIntermission/i, null, "gameloop", "period/intermission", "med"],
  [/game state|new game|start a period/i, "comment", "gameloop", "game state", "med"],

  // ai
  [/^(ass|check4bench|SetPlList|TryAddPlayer|setplayer|Setplass|donothing|clrplayer)/i, null, "ai", "assignments", "high"],
  [/goalie|Goalie|ManualGoalie|getGoalie|puckgoalie|assgoalie/i, null, "ai", "goalie", "high"],
  [/^(SetLCmode|setlccords|getlchoice|lcfound|chk4lc|changeplayer|lineinput|StartFaceoffLine|WaitForFaceoffLine|UpdateFaceoffLine)/i, null, "ai", "line changes", "high"],
  [/strategy|assdef|assdefo|assdefd|compline/i, null, "ai", "strategy", "med"],

  // players
  [/^(updateplayers|updateanim|freezewindow|checkwindow|PlayerAcc|skate|SkatePath|holdplayer|RestoreBenchEnergy|CheckInjury|setInjury|FallDown|reenergizeteam)/i, null, "players", "skating", "med"],
  [/anim|SetSframe|setonetimeranim|RandomFaceoffAnim|FaceoffAnim|SetFaceoffAnim/i, null, "players", "animation", "med"],
  [/^(Bcheck|Sweepcheck|Findhittype|checkinglist|holdcheck|checkagr|checkfight|CCStart|newcheck|checkint|checkcx|checkplcoll|checkcoll|checkcheck|check4check|Acheck)$/i, null, "players", "checking", "med"],
  [/fight|Fight|assfight|gloves/i, null, "players", "fights", "high"],
  [/onetimer|OneTimer|one-timer/i, null, "players", "one-timers", "high"],

  // puck
  [/^(dopass|passto|passmode|setpassmode|OneTimerPass|passdir)/i, null, "puck", "passing", "high"],
  [/^(doshot|ShotMode|SetShotMode|prepshot|shotsets|shotdir|CalcAngleOffset|onetimershot|ChkShotStat)/i, null, "puck", "shooting", "high"],
  [/puck|Puck|possession|puckstick|puckglue|puckbody|puckvz|deflect|makepde|getpde|setpde/i, null, "puck", "movement", "med"],

  // collision
  [/wallcoll|checkwall|boards|cornercoll|checkcorner|wallcollduring/i, null, "collision", "boards/goal", "high"],
  [/checkgoal|PenGoal|goalp\b|CheckBump/i, null, "collision", "goals", "high"],
  [/puckcoll|checkpuckcoll|puckstick|puckglue|puckbody|puckgoalie/i, null, "collision", "puck-player", "high"],
  [/plcoll|player-player|checkplcoll|checkcoll|newcheck|checkcheck|CCStart/i, null, "collision", "player-player", "high"],

  // rules
  [/penalt|Penalty|AddPenalty|Stop4Pen|updatepentime|ProcessPenalty|releasepl|GetLowestPen|updatepwrplay|PenShot|pplpen|limitfo|PushRef|prefmes|ClearPenalty|InProgress|coinsearch|chkprogress/i, null, "rules", "penalties", "high"],
  [/offside|icing|chkoffside/i, null, "rules", "offsides/icing", "high"],
  [/shootout|Shootout|EndShootout|StartShootout|NextShooter/i, null, "rules", "shootout", "high"],

  // display
  [/^(showclock|printscores|PrintTeamName|PrintTeamLogo|ShowScores|EASNLogo|DrawEASN|USBoard|linebar|ClrHor|SetHor|uppads|showref|showzam|showcrowd|checksso|setsortcords|setffo)/i, null, "display", "scoreboard/clock", "high"],
  [/crowd|Crowd|HotCold|HotList|arena|ArenaAnim|RunArenaAnim/i, null, "display", "crowd/arena", "med"],
  [/rink|setupice|IceRink|updatescroll|show_rink/i, null, "display", "rink scroll", "med"],
  [/highlight|overlay|box$|ShowGoalBox|ShowInjuryBox|PenaltyShotBox|three.?star|ShowThreeStars/i, null, "display", "overlays/highlights", "med"],

  // frontend
  [/^(EASports|Opening|Title|Credits|titlescreen|TitleScreen)/i, null, "frontend", "title/credits", "high"],
  [/attract|splash|EASportsScreen/i, null, "frontend", "attract/splash", "high"],
  [/Menu|menu|InitMenu|DrawMenu|HandleMenu|UpdateMenu|PutTeamBlock|PrintMenu|vcountwait|MenuWait/i, null, "frontend", "menu engine", "high"],
  [/option|Option|GameSetUp|setoptions|SetupDemo|SetupStart|ChangeOption|PrintOption|FixMode|OptionLimit|ReadSetupPads|LoadSetupTiles/i, null, "frontend", "options/setup", "high"],
  [/team.?select|PickStartingGoalie|PutTeamBlock|TeamRoster|SelectLine/i, null, "frontend", "team select", "med"],
  [/PlayoffScreen|HandlePlayoff|DrawTreeArrow|maketree|ContinuePlayoffs|NewPO|GoNewPlayoffs|GoContinuePlayoffs/i, null, "season", "playoffs", "high"],

  // stats
  [/stat|Stat|ShowScores|DisplayGameInfo|PrintGameInfo|ScoringSummary|PenaltySummary|GameStatistics|PeriodStats|DisplayTeamStats|TeamStat|ClearGameStats|updatePPTeamTime|GetTeamRating/i, null, "stats", "game/period stats", "high"],
  [/^(PlayerCard|FeaturedPicture|ResetCardTimer|PlayerCardTimer|PlayerCardScreen|TeamPalettes|TeamPalettesEnd)$/i, null, "stats", "player cards", "high"],
  [/record|Record|NameEntry|NameLetter|NameLog|UserName|RecordHolder|HiScore|WriteName|ReadName/i, null, "stats", "records/name entry", "high"],
  [/scout|Scout|Scouting|Matchup|InitScouting|UpdateScouting|ScrollDisplay/i, null, "stats", "scouting", "high"],
  [/LineEditor|Attrib|attrib|GetNameandAttrib|Attribute|DrawLineIcon|DecodeTeamLines|EncodeTeamLines/i, null, "stats", "player cards", "med"],

  // season
  [/playoff|Playoff|SeriesScore|ResolveGames|AddPlayoffTeam|playoffseats|UpdatePlayoffLevel|DrawMatchup/i, null, "season", "playoffs", "high"],
  [/standings|season result|ReadTeamStats/i, null, "season", "standings", "med"],
  [/ResolveGames|ShowThreeStars|CalcStarScores|CalcTeamStar/i, null, "season", "season results", "high"],

  // replay
  [/replay|Replay|suba4|adda4|RestoreReplay|updatereplay|ShowReplay|EraseReplay|RevReplay|ClampReplay/i, null, "replay", "playback", "high"],
  [/record.*replay|replay.*record|sf2drec/i, "comment", "replay", "record", "med"],

  // save
  [/SRAM|BackupRAM|SaveRAM|Password|EncodePW|ReadPass|WritePass|ClrPass|PushBits|ValidateSRAM|MakeSRAMChecksum/i, null, "save", "sram", "high"],
  [/password|pass ?bit/i, null, "save", "passwords", "high"],

  // data
  [/^(SPF|SPA|TeamList|NumofTeams|Playerdata|Palettedata|Teamname|LineSets|ScoutReport|ScoreOdds|AllStars|Boston|Buffalo|Calgary|Chicago|Detroit|Edmonton|Hartford|LosAngeles|LongIsland|Minnesota|Montreal|NewJersey|NewYork|NYIslanders|NYRangers|Ottawa|Philadelphia|Pittsburgh|Quebec|SanJose|StLouis|TampaBay|Toronto|Vancouver|Winnipeg|Washington|Florida|Anaheim|Dallas|playoffseats|Credits|NoTiles|PlayoffSeatsEnd)$/i, null, "data", "team/roster", "high"],
  [/^SP[FAC]/i, null, "data", "frame tables", "high"],
  [/Map$|Sprites$|Img$|tiles|Tilelist|logo|FontMap|Bitmaps|Graphics|EASNmap|ScoresMap|Stanley|RonBarr|Framer|IceRink|RefsMap|CrowdFrame|ZamFrame|EnergyBar|Arrows|ReplayMap|HorRink|SetupMenu|LogoBox|HotList|Rinktile/i, null, "data", "graphics", "high"],
  [/Txt$|Text$|TextTbl|String|Names$|OptionNames|OptionValue|ScrollUpTxt|BlankValue|NATxt|HomeTxt|VisitorsTxt|EnterName|SelectName|LetterGrid|RecordTxt|RecGoals|PenShotBig|GoalBig|PPGoal|ShootoutModeBig|ScoutEmpty|ScoutBy|TwoSpaces|EvenAdv|Advantage/i, null, "data", "strings", "high"],
  [/pcm$|cmdstream$|SoundStream|fm_instrument|pcm_sample/i, null, "data", "sound data", "high"],
  [/Table$|Tbl$|List$|Data$|Offsets$|Positions|PosTable|Jump_table|BitWidth|PadDir|dirtab|priolist|cd0|ArenaFrames|ArenaAnims|ShootoutPath|TeamGfxList|TeamSongs|RandomSongs|FaceoffAnims|DefaultMenus|defmenuoptions|OptionLimits/i, null, "data", "frame tables", "med"],

  // misc helpers often in middle/video
  [/^(randomd0|randomd0s|sroot|waitx|waitxsr|WeightedRandom|sroot)/i, null, "system", "memory clears", "low"],
  [/^(InitializeGameStructures|GetRandomUnusedTeam|SuperAdd|SuperMult|SuperDiv|GetShifter|forcepldata|ResetBench|resetplstuff|clearTeamStats|setteams|InitTeamStructure|setupTeamBlocks|CopyTeamBlock|ReloadEnergy|ReloadCrowd|ReloadRef|ReloadFaceOff|defaultsprites2)/i, null, "gameloop", "game state", "med"],
];

function classifyOne(name, file, text) {
  const n = name;
  const comment = firstComment(text);
  const body = (text || "").toLowerCase();
  const fileBase = file.replace(/^.*\//, "");

  // Explicit RAM/equate file
  if (file === "ram93.asm" || file === "ram94.asm") {
    return { category: "other", subcategory: "RAM/IO equates (not ROM code)", confidence: "high", why: "ram equate file" };
  }

  // File-based specialty overrides first (94 split files, sound data, etc.)
  const fileRules = classifyByFileContext(n, file, comment, body);
  if (fileRules) return fileRules;

  // Name+comment rules
  for (const [nr, cr, cat, sub, conf] of RULES) {
    if (cr === "comment") {
      if (nr.test(comment) || nr.test(body.slice(0, 200))) {
        return { category: cat, subcategory: sub, confidence: conf, why: "comment rule" };
      }
    } else if (nr.test(n)) {
      return { category: cat, subcategory: sub, confidence: conf, why: "name rule" };
    }
  }

  // File default
  const fd = FILE_DEFAULTS[file];
  if (fd) {
    return { category: fd[0], subcategory: fd[1], confidence: fd[2], why: "file default" };
  }

  // hockey93/94 leftovers
  if (/^hockey9[34]\.asm$/i.test(file)) {
    return { category: "gameloop", subcategory: "frame loop", confidence: "low", why: "hockey file fallback" };
  }
  if (/^logic9[34]\.asm$/i.test(file) || file === "input94.asm") {
    return { category: "input", subcategory: "controllers", confidence: "low", why: "logic/input file fallback" };
  }
  if (file === "checks94.asm") {
    return { category: "players", subcategory: "checking", confidence: "low", why: "checks file fallback" };
  }
  if (file === "middle93.asm") {
    return { category: "video", subcategory: "VDP/DMA", confidence: "low", why: "middle file fallback" };
  }
  if (file === "setup94.asm") {
    return { category: "display", subcategory: "rink scroll", confidence: "low", why: "setup file fallback" };
  }
  if (file === "data94.asm") {
    return { category: "data", subcategory: "strings", confidence: "low", why: "data file fallback" };
  }
  if (/^stats9[34]\.asm$/i.test(file)) {
    return { category: "stats", subcategory: "game/period stats", confidence: "low", why: "stats file fallback" };
  }

  return { category: "other", subcategory: "unclassified", confidence: "low", why: "no rule matched" };
}

function classifyByFileContext(n, file, comment, body) {
  file = file.replace(/^.*\//, "");

  // High-priority semantic overrides (beat file buckets)
  if (/faceoff/i.test(n) && !/^SPA/i.test(n) && !/ReloadFaceOff|FaceOffMap|FaceOffSprites/i.test(n)) {
    if (/input|LineChange|ComputerLine|assfaceoff|SetFaceoffAnim/i.test(n) || /line change/i.test(comment)) {
      if (/LineChange|ComputerLine|getlchoice|SetLC/i.test(n))
        return { category: "ai", subcategory: "line changes", confidence: "high", why: "faceoff line change" };
    }
    return { category: "gameloop", subcategory: "faceoffs", confidence: "high", why: "faceoff semantic" };
  }
  if (/^assfight|^fightinput|checkfight|^SPFfight/i.test(n) || (/\bfight\b/i.test(n) && !/^SPA|^SPF/i.test(n))) {
    if (!/^SPF|^SPA/i.test(n))
      return { category: "players", subcategory: "fights", confidence: "high", why: "fight semantic" };
  }
  if (/goalie/i.test(n) && !/^SPF|^SPA|Tbl$|Table$/i.test(n)) {
    return { category: "ai", subcategory: "goalie", confidence: "high", why: "goalie semantic" };
  }

  if (file === "optsetup94.asm") {
    if (/Playoff/i.test(n)) return { category: "season", subcategory: "playoffs", confidence: "high", why: "playoff from options" };
    if (/Txt$|Values$|OptionNames|OptionLimits|BlankValue|NATxt|IslandersTxt|RangersTxt/i.test(n))
      return { category: "data", subcategory: "strings", confidence: "high", why: "option strings" };
    return { category: "frontend", subcategory: "options/setup", confidence: "high", why: "optsetup file" };
  }
  if (file === "fourway94.asm") {
    return { category: "input", subcategory: "multitap", confidence: "high", why: "fourway file" };
  }
  if (file === "attract94.asm") {
    if (/Goalie/i.test(n)) return { category: "frontend", subcategory: "team select", confidence: "med", why: "goalie pick" };
    if (/option|Option|VBlank_SetOptions|setoptions/i.test(n))
      return { category: "frontend", subcategory: "options/setup", confidence: "med", why: "options in attract" };
    if (/Playoff|Matchup|Bitmap|Roster/i.test(n))
      return { category: "season", subcategory: "playoffs", confidence: "med", why: "matchup in attract" };
    return { category: "frontend", subcategory: "attract/splash", confidence: "high", why: "attract file" };
  }
  if (file === "records94.asm") {
    return { category: "stats", subcategory: "records/name entry", confidence: "high", why: "records file" };
  }
  if (file === "period94.asm") {
    if (/Shootout/i.test(n)) return { category: "rules", subcategory: "shootout", confidence: "high", why: "shootout end" };
    if (/Arena|Camera/i.test(n)) return { category: "display", subcategory: "crowd/arena", confidence: "med", why: "arena in period" };
    return { category: "stats", subcategory: "game/period stats", confidence: "high", why: "period file" };
  }
  if (file === "shootout94.asm") {
    if (/Txt$|BigTxt$/i.test(n)) return { category: "data", subcategory: "strings", confidence: "high", why: "shootout text" };
    return { category: "rules", subcategory: "shootout", confidence: "high", why: "shootout file" };
  }
  if (file === "scout94.asm") {
    if (/Txt$|Text$|Empty|ByTxt|Space|Adv\d|HomeTxt|VisitorsTxt|EvenAdv/i.test(n))
      return { category: "data", subcategory: "strings", confidence: "high", why: "scout strings" };
    return { category: "stats", subcategory: "scouting", confidence: "high", why: "scout file" };
  }
  if (file === "menu94.asm" || file === "menu93.asm") {
    return { category: "frontend", subcategory: "menu engine", confidence: "high", why: "menu file" };
  }

  // sound data vs driver inside sound*.asm
  if (/^sound9[34]\.asm$/i.test(file)) {
    if (/(_pcm|_cmdstream|pcm_sample|SoundStream|fm_instrument|Patches)/i.test(n)) {
      return { category: "data", subcategory: "sound data", confidence: "high", why: "sound data label" };
    }
    if (/ReadPad|ReadJoy|PadDir|Joy/i.test(n)) {
      return { category: "input", subcategory: "controllers", confidence: "high", why: "pad read in sound file" };
    }
    if (/song|music|fmtune|ChooseSong/i.test(n)) {
      return { category: "sound", subcategory: "music", confidence: "high", why: "music in sound file" };
    }
    if (/sfx|SFX/i.test(n)) {
      return { category: "sound", subcategory: "sfx", confidence: "high", why: "sfx in sound file" };
    }
    return { category: "sound", subcategory: "driver", confidence: "med", why: "sound file" };
  }

  // frames = data
  if (/^frames9[34]\.asm$/i.test(file)) {
    return { category: "data", subcategory: "frame tables", confidence: "high", why: "frames file" };
  }

  // graphics = data
  if (/^graphics9[34]\.asm$/i.test(file)) {
    if (/Text|Script|String/i.test(n)) {
      return { category: "data", subcategory: "strings", confidence: "high", why: "text in graphics" };
    }
    return { category: "data", subcategory: "graphics", confidence: "high", why: "graphics file" };
  }

  // teamdata
  if (/^teamdata9[34]\.asm$/i.test(file)) {
    if (/Credits/i.test(n)) {
      return { category: "frontend", subcategory: "title/credits", confidence: "med", why: "credits in teamdata" };
    }
    return { category: "data", subcategory: "team/roster", confidence: "high", why: "teamdata file" };
  }

  // replay file mixed with player update
  if (file === "replay94.asm") {
    if (/updateplayers|updateanim|freezewindow|checkwindow/i.test(n)) {
      return { category: "players", subcategory: "skating", confidence: "high", why: "player update in replay file" };
    }
    if (/Camera|scroll/i.test(n)) {
      return { category: "display", subcategory: "rink scroll", confidence: "med", why: "camera in replay" };
    }
    return { category: "replay", subcategory: "playback", confidence: "high", why: "replay file" };
  }

  // input94 has puck/shot/pass too
  if (file === "input94.asm" || file === "logic93.asm") {
    if (/pass|Pass/i.test(n)) return { category: "puck", subcategory: "passing", confidence: "high", why: "pass routine" };
    if (/shot|Shot|doshot/i.test(n)) return { category: "puck", subcategory: "shooting", confidence: "high", why: "shot routine" };
    if (/ass|bench|penalty|faceoff|fight|goalie|def|stanley|score/i.test(n))
      return { category: "ai", subcategory: "assignments", confidence: "high", why: "assignment in logic/input" };
    if (/line|LC|lchoice|SetLC/i.test(n)) return { category: "ai", subcategory: "line changes", confidence: "high", why: "line change" };
    if (/check|hit|Sweep|Findhit|holdplayer|burst|changeplayer/i.test(n))
      return { category: "players", subcategory: "checking", confidence: "med", why: "check/hit in input" };
    if (/fight/i.test(n)) return { category: "players", subcategory: "fights", confidence: "high", why: "fight input" };
    if (/faceoff/i.test(n)) return { category: "gameloop", subcategory: "faceoffs", confidence: "high", why: "faceoff input" };
    if (/pause/i.test(n)) return { category: "input", subcategory: "pause", confidence: "high", why: "pause" };
    return { category: "input", subcategory: "controllers", confidence: "med", why: "input/logic file" };
  }

  // checks94 - pre-display checks, collisions, AI-ish
  if (file === "checks94.asm") {
    if (/offside|icing/i.test(n + comment)) return { category: "rules", subcategory: "offsides/icing", confidence: "high", why: "offsides/icing" };
    if (/goal/i.test(n)) return { category: "collision", subcategory: "goals", confidence: "med", why: "goal check" };
    if (/puck/i.test(n)) return { category: "puck", subcategory: "movement", confidence: "med", why: "puck check" };
    if (/coll|wall|board/i.test(n)) return { category: "collision", subcategory: "boards/goal", confidence: "med", why: "collision check" };
    if (/ass|assign|line|strategy|goalie/i.test(n)) return { category: "ai", subcategory: "strategy", confidence: "med", why: "ai check" };
    if (/check|hit|fight|injury|Fall/i.test(n)) return { category: "players", subcategory: "checking", confidence: "med", why: "checks file" };
    return { category: "players", subcategory: "checking", confidence: "low", why: "checks file default" };
  }

  // collide94
  if (file === "collide94.asm") {
    if (/puck/i.test(n)) return { category: "collision", subcategory: "puck-player", confidence: "high", why: "puck collision" };
    if (/wall|board|corner/i.test(n)) return { category: "collision", subcategory: "boards/goal", confidence: "high", why: "wall collision" };
    if (/goal/i.test(n)) return { category: "collision", subcategory: "goals", confidence: "high", why: "goal collision" };
    if (/fight|injury|Fall|check/i.test(n)) return { category: "collision", subcategory: "player-player", confidence: "high", why: "player collision" };
    if (/ass|Setpl|setplayer|personnel|bench|PenaltyShot|forcepl/i.test(n))
      return { category: "ai", subcategory: "assignments", confidence: "med", why: "assignment near collide" };
    return { category: "collision", subcategory: "player-player", confidence: "med", why: "collide file" };
  }

  // penalty file mixed display
  if (/^penalty9[34]\.asm$/i.test(file)) {
    if (/print|score|logo|EASN|USBoard|linebar|ClrHor|SetHor|Draw/i.test(n))
      return { category: "display", subcategory: "scoreboard/clock", confidence: "high", why: "scoreboard in penalty" };
    if (/Intermission|reenergiz|loadTeam|SetupTeam|AvgCline|getlinee/i.test(n))
      return { category: "gameloop", subcategory: "period/intermission", confidence: "med", why: "intermission in penalty" };
    if (/ShotStat|ChkShot/i.test(n)) return { category: "stats", subcategory: "game/period stats", confidence: "med", why: "shot stat" };
    return { category: "rules", subcategory: "penalties", confidence: "high", why: "penalty file" };
  }

  // display/video93
  if (file === "display94.asm" || file === "video93.asm") {
    if (/VBlank|IRQ|vb2/i.test(n)) return { category: "system", subcategory: "interrupts", confidence: "high", why: "vblank handler" };
    if (/DMA|DumpSprite|setvideo|SetScroll/i.test(n)) return { category: "video", subcategory: "VDP/DMA", confidence: "high", why: "vdp in display" };
    if (/scroll|Camera/i.test(n)) return { category: "display", subcategory: "rink scroll", confidence: "high", why: "scroll" };
    if (/crowd|Crowd|KillCrowd/i.test(n)) return { category: "display", subcategory: "crowd/arena", confidence: "high", why: "crowd" };
    if (/clock|pad|font|Label|ref|zam|ffo|sort|sso/i.test(n))
      return { category: "display", subcategory: "scoreboard/clock", confidence: "high", why: "hud" };
    if (/sound|updatesound/i.test(n)) return { category: "sound", subcategory: "driver", confidence: "med", why: "sound update in vblank" };
    if (/frame|find3d|addframe/i.test(n)) return { category: "video", subcategory: "sprites", confidence: "med", why: "sprite frame" };
    return { category: "display", subcategory: "scoreboard/clock", confidence: "med", why: "display/video file" };
  }

  // middle93 - video/input/math mix
  if (file === "middle93.asm") {
    if (/DMA|Vram|Fill|WaitDMA|Vmaddr|dobitmap|Decompress|Opcode_/i.test(n))
      return { category: "video", subcategory: "VDP/DMA", confidence: "high", why: "dma/decompress" };
    if (/fade|palette|CRAM|forceblack|remap/i.test(n))
      return { category: "video", subcategory: "palettes/fades", confidence: "high", why: "palette" };
    if (/Joy|joy|input|nodiag|waitjoy|orjoy|ProcessInput/i.test(n))
      return { category: "input", subcategory: "controllers", confidence: "high", why: "joy in middle" };
    if (/sfx|song/i.test(n)) return { category: "sound", subcategory: n.toLowerCase().includes("song") ? "music" : "sfx", confidence: "high", why: "sound helper" };
    if (/random|sroot|waitx|UnpackNibble|Weighted/i.test(n))
      return { category: "system", subcategory: "memory clears", confidence: "low", why: "utility in middle" };
    return { category: "video", subcategory: "VDP/DMA", confidence: "low", why: "middle fallback" };
  }

  // video94 is middle-like in 94
  if (file === "video94.asm") {
    if (/DMA|Vram|Fill|WaitDMA|Vmaddr|dobitmap|Decompress|Opcode_/i.test(n))
      return { category: "video", subcategory: "VDP/DMA", confidence: "high", why: "dma" };
    if (/fade|palette|CRAM|forceblack|remap/i.test(n))
      return { category: "video", subcategory: "palettes/fades", confidence: "high", why: "palette" };
    if (/Joy|joy|input|nodiag|waitjoy|orjoy|ProcessInput|ReadJoy/i.test(n))
      return { category: "input", subcategory: "controllers", confidence: "high", why: "joy in video94" };
    if (/sfx|song/i.test(n)) return { category: "sound", subcategory: /song/i.test(n) ? "music" : "sfx", confidence: "high", why: "sound helper" };
    if (/random|sroot|waitx|Unpack|Weighted/i.test(n))
      return { category: "system", subcategory: "memory clears", confidence: "low", why: "utility" };
    return { category: "video", subcategory: "VDP/DMA", confidence: "low", why: "video94 fallback" };
  }

  // setup94
  if (file === "setup94.asm") {
    if (/playoff|Playoff|Series|TreeArrow|DrawTeamBlocks/i.test(n))
      return { category: "season", subcategory: "playoffs", confidence: "high", why: "playoff screen" };
    if (/Opening|ExitToOpening|GameOver/i.test(n))
      return { category: "frontend", subcategory: "title/credits", confidence: "med", why: "opening" };
    if (/Intermission|PeriodOver/i.test(n))
      return { category: "gameloop", subcategory: "period/intermission", confidence: "high", why: "period/intermission" };
    if (/Scout|Scouting/i.test(n)) return { category: "stats", subcategory: "scouting", confidence: "high", why: "scout display" };
    if (/ice|rink|palette|Tiles|Map|sprites|SprSort|resetpl|clearTeam|setteams|InitTeam|setplayercolors/i.test(n))
      return { category: "display", subcategory: "rink scroll", confidence: "med", why: "ice/setup" };
    return { category: "display", subcategory: "rink scroll", confidence: "low", why: "setup fallback" };
  }

  // data94
  if (file === "data94.asm") {
    if (/Pass|Password|EncodePW|ReadPass|WritePass|ClrPass|PushBits/i.test(n))
      return { category: "save", subcategory: "passwords", confidence: "high", why: "password" };
    if (/Playoff|maketree|ContinuePlayoffs|NewPO|ResolveGames|AddPlayoff/i.test(n))
      return { category: "season", subcategory: "playoffs", confidence: "high", why: "playoff data/code" };
    if (/Star|InjuryBox|GoalBox|PenaltyShotBox|box$/i.test(n))
      return { category: "display", subcategory: "overlays/highlights", confidence: "high", why: "overlay box" };
    if (/Menu|menu|FigureJoy|InitializeGame/i.test(n))
      return { category: "frontend", subcategory: "menu engine", confidence: "med", why: "menu data" };
    if (/GetPlayerName|getname|FormatPlayer|GetTeam/i.test(n))
      return { category: "data", subcategory: "strings", confidence: "med", why: "name format" };
    if (/Txt$|Text|Table|Tbl/i.test(n)) return { category: "data", subcategory: "strings", confidence: "high", why: "string/table" };
    return { category: "data", subcategory: "strings", confidence: "low", why: "data94 fallback" };
  }

  // stats files
  if (/^stats9[34]\.asm$/i.test(file)) {
    if (/LineEditor|LineIcon|LineSlot|LineCursor|DecodeTeam|EncodeTeam|TeamRoster|PlayerList|Attrib|attrib|GoalieRow|SelectLine|DrawTeamScreen/i.test(n))
      return { category: "stats", subcategory: "player cards", confidence: "med", why: "line/attrib UI" };
    if (/CrowdMeter|crowd/i.test(n)) return { category: "display", subcategory: "crowd/arena", confidence: "med", why: "crowd meter" };
    if (/Playoff|playoff/i.test(n)) return { category: "season", subcategory: "playoffs", confidence: "med", why: "playoff stats" };
    if (/ScrollArrow|MenuWait|ClearMenu/i.test(n)) return { category: "frontend", subcategory: "menu engine", confidence: "low", why: "menu helper in stats" };
    return { category: "stats", subcategory: "game/period stats", confidence: "med", why: "stats file" };
  }

  // hockey core
  if (/^hockey9[34]\.asm$/i.test(file)) {
    if (/pause|Pause/i.test(n)) return { category: "input", subcategory: "pause", confidence: "high", why: "pause" };
    if (/replay|Replay|adda4|suba4/i.test(n)) return { category: "replay", subcategory: "playback", confidence: "high", why: "replay" };
    if (/crowd|CwdExcite|KillCrowd/i.test(n)) return { category: "sound", subcategory: "crowd audio", confidence: "med", why: "crowd" };
    if (/Song|song/i.test(n)) return { category: "sound", subcategory: "music", confidence: "high", why: "song" };
    if (/Injury|BenchEnergy|updateplayers|updateanim|window/i.test(n))
      return { category: "players", subcategory: "skating", confidence: "med", why: "player update" };
    if (/Camera|scroll/i.test(n)) return { category: "display", subcategory: "rink scroll", confidence: "med", why: "camera" };
    if (/demo|Demo/i.test(n)) return { category: "frontend", subcategory: "attract/splash", confidence: "med", why: "demo" };
    if (/clock|Clock|period|Period|Gameloop|DoGameFrame|StartPer|StartGame|Begin|ClearShot|restoreteams|GetPeriod|ChkShort|periodic/i.test(n))
      return { category: "gameloop", subcategory: /clock|period|Per/i.test(n) ? "period/intermission" : "frame loop", confidence: "high", why: "hockey core" };
    if (/VBjsr|IRQ/i.test(n)) return { category: "system", subcategory: "interrupts", confidence: "high", why: "interrupt" };
    return { category: "gameloop", subcategory: "frame loop", confidence: "low", why: "hockey fallback" };
  }

  // crowd94 - hot/cold is stats-ish, crowd noise is sound, corner coll is collision
  if (file === "crowd94.asm") {
    if (/Noise|LoadCrowd|stopna/i.test(n)) return { category: "sound", subcategory: "crowd audio", confidence: "high", why: "crowd noise" };
    if (/coll|corner|wall/i.test(n)) return { category: "collision", subcategory: "boards/goal", confidence: "high", why: "corner coll" };
    if (/Hot|Cold|Attribute/i.test(n)) return { category: "stats", subcategory: "player cards", confidence: "med", why: "hot/cold" };
    return { category: "display", subcategory: "crowd/arena", confidence: "med", why: "crowd file" };
  }

  // goalie94 - mix of goalie menu and arena anim
  if (file === "goalie94.asm") {
    if (/Goalie|goalie/i.test(n)) return { category: "ai", subcategory: "goalie", confidence: "high", why: "goalie" };
    if (/Arena|Camera|FaceoffAnim/i.test(n)) return { category: "display", subcategory: "crowd/arena", confidence: "med", why: "arena anim" };
    return { category: "ai", subcategory: "goalie", confidence: "low", why: "goalie file" };
  }

  // title94 - grab bag
  if (file === "title94.asm") {
    if (/Song|song/i.test(n)) return { category: "sound", subcategory: "music", confidence: "high", why: "songs" };
    if (/Shootout|Path|SkatePath|ShootoutShoot/i.test(n)) return { category: "rules", subcategory: "shootout", confidence: "high", why: "shootout path" };
    if (/Title|Credit|HiScore|UnpackPicture|LoadHomeTeam|TeamGfx|DrawPlayoff|boardFall|PlaceBoard/i.test(n))
      return { category: "frontend", subcategory: "title/credits", confidence: "med", why: "title" };
    if (/Record|Name|Log|CrowdRecord|Fgt|ScoreLeader|LineData|ClearWin/i.test(n))
      return { category: "stats", subcategory: "records/name entry", confidence: "med", why: "records helpers" };
    if (/FaceoffAnim|RandomFaceoff/i.test(n)) return { category: "gameloop", subcategory: "faceoffs", confidence: "med", why: "faceoff anim" };
    if (/PrintPlayer|Assists|Goals|Paren/i.test(n)) return { category: "stats", subcategory: "game/period stats", confidence: "med", why: "stat print" };
    return { category: "frontend", subcategory: "title/credits", confidence: "low", why: "title file" };
  }

  // cards94
  if (file === "cards94.asm") {
    if (/Record|NameLog|WriteName|ReadName|UpdateRecord/i.test(n))
      return { category: "stats", subcategory: "records/name entry", confidence: "high", why: "records in cards" };
    if (/wallcoll/i.test(n)) return { category: "collision", subcategory: "boards/goal", confidence: "high", why: "wall during check" };
    if (/Palette|Picture/i.test(n)) return { category: "data", subcategory: "graphics", confidence: "med", why: "card gfx data" };
    return { category: "stats", subcategory: "player cards", confidence: "high", why: "cards file" };
  }

  // assign94
  if (file === "assign94.asm") {
    return { category: "ai", subcategory: "assignments", confidence: "high", why: "assign file" };
  }

  // onetimer
  if (file === "onetimer94.asm") {
    if (/Pass/i.test(n)) return { category: "puck", subcategory: "passing", confidence: "high", why: "ot pass" };
    if (/shot|Shot/i.test(n)) return { category: "puck", subcategory: "shooting", confidence: "high", why: "ot shot" };
    if (/ass|Goalie|anim|Facing|PuckOn/i.test(n)) return { category: "players", subcategory: "one-timers", confidence: "high", why: "ot" };
    return { category: "players", subcategory: "one-timers", confidence: "med", why: "onetimer file" };
  }

  // sram
  if (/^sram9[34]\.asm$/i.test(file)) {
    if (/ReadPad|Pad/i.test(n)) return { category: "input", subcategory: "controllers", confidence: "high", why: "pad in sram" };
    if (/ClearVRAM|ClearRAM/i.test(n)) return { category: "system", subcategory: "memory clears", confidence: "med", why: "clear in sram" };
    return { category: "save", subcategory: "sram", confidence: "high", why: "sram file" };
  }

  // checksum / sega / main
  if (/^checksum9[34]\.asm$/i.test(file)) {
    return { category: "system", subcategory: "checksum/security", confidence: "high", why: "checksum file" };
  }
  if (/SegaInit\.asm$/i.test(file)) {
    if (/clr_|dma_fill|z80_clr|c_wk|c_col|c_vsc|c_psg/i.test(n))
      return { category: "system", subcategory: "memory clears", confidence: "high", why: "clear in SegaInit" };
    if (/security|japan|CHECK_VDP/i.test(n))
      return { category: "system", subcategory: "checksum/security", confidence: "high", why: "security in SegaInit" };
    return { category: "system", subcategory: "boot/vectors", confidence: "high", why: "SegaInit" };
  }
  if (/^main9[34]\.asm$/i.test(file)) {
    if (/RAMStart|InitialSP|ErrorStatus/i.test(n))
      return { category: "system", subcategory: "header", confidence: "high", why: "header equates" };
    if (/^Start$/i.test(n)) return { category: "system", subcategory: "boot/vectors", confidence: "high", why: "Start" };
    return { category: "system", subcategory: "boot/vectors", confidence: "med", why: "main file" };
  }

  return null;
}

function lookupAddr(addrs, name) {
  if (addrs.has(name)) return addrs.get(name);
  if (addrs.has(name.toLowerCase())) return addrs.get(name.toLowerCase());
  return null;
}

function buildRows(game, d, addrs) {
  const fm = unitFileMap(d);
  const rows = [];
  // first code unit per file gets file.a if no listing addr
  const firstCodeInFile = new Map();
  d.units.forEach((u, i) => {
    if (u.k !== "code") return;
    const meta = fm.get(i) || { f: "?", a: null };
    if (!firstCodeInFile.has(meta.f)) firstCodeInFile.set(meta.f, i);
  });

  d.units.forEach((u, i) => {
    if (u.k !== "code") return;
    const meta = fm.get(i) || { f: "?", a: null };
    const lines = lineCount(u.t);
    const cls = classifyOne(u.n, meta.f, u.t);
    let addr = lookupAddr(addrs, u.n);
    if (addr == null && firstCodeInFile.get(meta.f) === i && meta.a != null) {
      addr = meta.a;
    }
    rows.push({
      idx: i,
      address: addr != null ? "0x" + addr.toString(16).toUpperCase().padStart(addr > 0xffff ? 6 : 4, "0") : "",
      addrNum: addr != null ? addr : null,
      file: meta.f,
      routine: u.n,
      lines,
      category: cls.category,
      subcategory: cls.subcategory,
      confidence: cls.confidence,
      why: cls.why,
      text: u.t,
    });
  });
  return rows;
}

function syncLineage(rows93, rows94, mapPaths) {
  // Same routine name => same category/subcategory.
  // Prefer higher confidence; on tie prefer 94 (more split files) then keep both equal.
  const byName93 = new Map(rows93.map((r) => [r.routine, r]));
  const byName94 = new Map(rows94.map((r) => [r.routine, r]));
  const confRank = { high: 3, med: 2, low: 1 };
  let synced = 0;
  for (const [name, r93] of byName93) {
    const r94 = byName94.get(name);
    if (!r94) continue;
    if (r93.category === r94.category && r93.subcategory === r94.subcategory) continue;
    const c93 = confRank[r93.confidence] || 0;
    const c94 = confRank[r94.confidence] || 0;
    let winner, loser;
    if (c94 > c93) {
      winner = r94;
      loser = r93;
    } else if (c93 > c94) {
      winner = r93;
      loser = r94;
    } else {
      // prefer non-other, else 94
      if (r93.category === "other" && r94.category !== "other") {
        winner = r94;
        loser = r93;
      } else if (r94.category === "other" && r93.category !== "other") {
        winner = r93;
        loser = r94;
      } else {
        winner = r94;
        loser = r93;
      }
    }
    loser.category = winner.category;
    loser.subcategory = winner.subcategory;
    loser.confidence = winner.confidence;
    loser.why = (loser.why || "") + "|synced-from-lineage";
    synced++;
  }

  // Also apply name_map renames 93<->94 where old/new both exist
  function loadMap(p) {
    if (!fs.existsSync(p)) return [];
    return fs
      .readFileSync(p, "utf8")
      .trim()
      .split(/\n/)
      .slice(1)
      .map((l) => {
        const [old, neu] = l.split(",");
        return [old && old.trim(), neu && neu.trim()];
      })
      .filter(([a, b]) => a && b && !a.includes("/") && !b.includes("/"));
  }
  const maps = (mapPaths || []).flatMap(loadMap);
  for (const [oldN, newN] of maps) {
    const names = [oldN, newN];
    const present = [];
    for (const n of names) {
      if (byName93.has(n)) present.push(byName93.get(n));
      if (byName94.has(n)) present.push(byName94.get(n));
    }
    if (present.length < 2) continue;
    // pick best
    present.sort((a, b) => (confRank[b.confidence] || 0) - (confRank[a.confidence] || 0));
    const best = present[0];
    for (const r of present) {
      if (r.category !== best.category || r.subcategory !== best.subcategory) {
        r.category = best.category;
        r.subcategory = best.subcategory;
        r.confidence = best.confidence;
        r.why = (r.why || "") + "|synced-rename";
        synced++;
      }
    }
  }
  return synced;
}


function assignPlacement(rows) {
  const byFile = new Map();
  for (const r of rows) {
    if (!byFile.has(r.file)) byFile.set(r.file, []);
    byFile.get(r.file).push(r);
  }
  const IGNORE = new Set((PLACEMENT.ignore_files || []).map((f) => f.toLowerCase()));
  const WIN = PLACEMENT.neighbour_window || 3;
  const FRAC = PLACEMENT.secondary_line_fraction || 0.15;
  const MINR = PLACEMENT.secondary_min_routines || 2;

  for (const [file, flist] of byFile) {
    const base = file.replace(/^.*\//, "");
    if (IGNORE.has(base.toLowerCase()) || IGNORE.has(file.toLowerCase())) {
      for (const r of flist) {
        r.placement = "";
        r.placeWhy = "ignored equate";
      }
      continue;
    }
    const catLines = new Map();
    const catCount = new Map();
    let total = 0;
    for (const r of flist) {
      catLines.set(r.category, (catLines.get(r.category) || 0) + r.lines);
      catCount.set(r.category, (catCount.get(r.category) || 0) + 1);
      total += r.lines;
    }
    if (catLines.size <= 1) {
      for (const r of flist) {
        r.placement = "";
        r.placeWhy = "mono-file";
      }
      continue;
    }
    let domCat = null, domCatLines = -1;
    for (const [c, n] of [...catLines.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1)) {
      if (n > domCatLines || (n === domCatLines && (domCat === null || c < domCat))) {
        domCat = c;
        domCatLines = n;
      }
    }
    const subLines = new Map();
    for (const r of flist) {
      if (r.category !== domCat) continue;
      subLines.set(r.subcategory, (subLines.get(r.subcategory) || 0) + r.lines);
    }
    let domSub = null, domSubLines = -1;
    for (const [s, n] of [...subLines.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1)) {
      if (n > domSubLines || (n === domSubLines && (domSub === null || s < domSub))) {
        domSub = s;
        domSubLines = n;
      }
    }
    const sizeable = new Set();
    for (const [c, n] of catLines) {
      if (c === domCat) continue;
      if (n >= FRAC * total && (catCount.get(c) || 0) >= MINR) sizeable.add(c);
    }
    for (let i = 0; i < flist.length; i++) {
      const r = flist[i];
      const neigh = flist.slice(Math.max(0, i - WIN), i).concat(flist.slice(i + 1, i + 1 + WIN));
      const neighCats = [...new Set(neigh.map((x) => x.category))].sort();
      const neighSubs = new Set(neigh.map((x) => x.subcategory));
      let place = "";
      let why = "";
      if (r.category !== domCat && !neighCats.includes(r.category)) {
        place = "red";
        why = "isolated " + r.category + " in " + domCat + "-dominated file; neighbours=[" + neighCats.join(",") + "]";
      } else if (
        r.category === domCat &&
        r.subcategory !== domSub &&
        !neighSubs.has(r.subcategory)
      ) {
        place = "yellow";
        why = "sub " + r.subcategory + " ≠ file dom " + domSub + " and ≠ neighbours";
      } else if (sizeable.has(r.category)) {
        place = "yellow";
        why = "secondary sizeable category " + r.category + " in " + domCat + " file";
      }
      if (place === "red" && r.confidence === "low") {
        place = "yellow";
        why += " (capped: low confidence)";
      }
      r.placement = place;
      r.placeWhy = why;
    }
  }
}

function summarizeGame(rows) {
  const cats = {};
  for (const r of rows) {
    if (!cats[r.category]) cats[r.category] = { routines: 0, lines: 0, subs: {} };
    cats[r.category].routines++;
    cats[r.category].lines += r.lines;
    if (!cats[r.category].subs[r.subcategory])
      cats[r.category].subs[r.subcategory] = { routines: 0, lines: 0 };
    cats[r.category].subs[r.subcategory].routines++;
    cats[r.category].subs[r.subcategory].lines += r.lines;
  }
  const byFile = new Map();
  for (const r of rows) {
    if (!byFile.has(r.file)) byFile.set(r.file, []);
    byFile.get(r.file).push(r);
  }
  const files = [];
  for (const [file, flist] of [...byFile.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1))) {
    const catLines = new Map();
    let red = 0, yellow = 0;
    for (const r of flist) {
      catLines.set(r.category, (catLines.get(r.category) || 0) + r.lines);
      if (r.placement === "red") red++;
      else if (r.placement === "yellow") yellow++;
    }
    let dom = null, domN = -1;
    for (const [c, n] of [...catLines.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1))) {
      if (n > domN || (n === domN && (dom === null || c < dom))) { dom = c; domN = n; }
    }
    const subLines = new Map();
    for (const r of flist) {
      if (r.category !== dom) continue;
      subLines.set(r.subcategory, (subLines.get(r.subcategory) || 0) + r.lines);
    }
    let domSub = null, domSubN = -1;
    for (const [s, n] of [...subLines.entries()].sort((a, b) => (a[0] < b[0] ? -1 : 1))) {
      if (n > domSubN || (n === domSubN && (domSub === null || s < domSub))) { domSub = s; domSubN = n; }
    }
    const domFull = dom && domSub ? dom + " / " + domSub : dom;
    files.push({ file, dominant: dom, dominantFull: domFull, red, yellow, total: flist.length });
  }
  return {
    routines: rows.length,
    lines: rows.reduce((a, r) => a + r.lines, 0),
    low: rows.filter((r) => r.confidence === "low").length,
    yellow: rows.filter((r) => r.placement === "yellow").length,
    red: rows.filter((r) => r.placement === "red").length,
    categories: cats,
    files,
  };
}

// ---- CLI: classify games and write JSON for generate.py to merge ----
const ROOT = path.join(__dirname, "..");
const catsPath = path.join(__dirname, "categories.json");
const CAT = JSON.parse(fs.readFileSync(catsPath, "utf8"));
FILE_DEFAULTS = CAT.file_defaults || {};
const CAT_COLORS = CAT.colors || {};
const CAT_ORDER = CAT.order || Object.keys(CAT_COLORS);
const PLACEMENT = CAT.placement || {};

function parseArgs(argv) {
  const out = { docs: path.join(ROOT, "docs"), maps: [], games: ["93G", "94G"], lst: {}, out: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--docs") out.docs = argv[++i];
    else if (a === "--map") out.maps.push(argv[++i]);
    else if (a === "--games") out.games = argv[++i].split(",");
    else if (a === "--lst") { const [g, p] = argv[++i].split("="); out.lst[g] = p; }
    else if (a === "--out") out.out = argv[++i];
    else if (a === "--help") { console.log("usage: classify_routines.js --docs DIR --map path --games 93G,94G --out FILE"); process.exit(0); }
  }
  return out;
}

function rowsToCompact(rows) {
  // per unit index: [category, subcategory, confidence, placement] or null
  const byIdx = new Map(rows.map((r) => [r.idx, r]));
  return rows; // caller handles unit alignment
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.maps.length) {
    // default: cache name maps for the two games
    const cache = path.join(ROOT, ".cache", "src");
    for (const repo of ["NHLPA93Genesis", "NHL94Genesis"]) {
      const p = path.join(cache, repo, "docs", "name_map.csv");
      if (fs.existsSync(p)) args.maps.push(p);
    }
  }
  const all = {};
  const rowSets = {};
  const addrOverlayPath = path.join(__dirname, "routine_addrs.json");
  const addrOverlay = fs.existsSync(addrOverlayPath)
    ? JSON.parse(fs.readFileSync(addrOverlayPath, "utf8"))
    : {};
  for (const g of args.games) {
    const d = loadNDR(args.docs, g);
    const addrs = args.lst[g] ? parseLst(args.lst[g]) : new Map();
    rowSets[g] = buildRows(g, d, addrs);
    const ov = addrOverlay[g] || {};
    for (const r of rowSets[g]) {
      const a = ov[r.file + "|" + r.routine];
      if (a) {
        r.address = a;
        r.addrNum = parseInt(a, 16);
      }
    }
  }
  if (rowSets["93G"] && rowSets["94G"]) {
    syncLineage(rowSets["93G"], rowSets["94G"], args.maps);
  }
  for (const g of args.games) {
    assignPlacement(rowSets[g]);
    const d = loadNDR(args.docs, g);
    const byIdx = new Map(rowSets[g].map((r) => [r.idx, r]));
    // unit-aligned compact: null for non-code / uncategorised units
    const units = d.units.map((u, i) => {
      const r = byIdx.get(i);
      if (!r) return null;
      return {
        c: r.category,
        s: r.subcategory,
        n: r.confidence,
        p: r.placement || "",
        a: r.address || "",
        w: r.placeWhy || r.why || "",
        lines: r.lines,
        file: r.file,
        routine: r.routine,
      };
    });
    all[g] = {
      units,
      rows: rowSets[g].map((r) => ({
        i: r.idx,
        a: r.address || "",
        f: r.file,
        r: r.routine,
        l: r.lines,
        c: r.category,
        s: r.subcategory,
        n: r.confidence,
        p: r.placement || "",
        w: r.placeWhy || "",
      })),
      summary: summarizeGame(rowSets[g]),
    };
  }
  const out = {
    colors: CAT_COLORS,
    order: CAT_ORDER,
    placement_rule: [
      "For each source file, compute the dominant category (by total lines) and, within it, the dominant subcategory.",
      "Look at the address neighbourhood: the 3 routines before and after in the same file (ROM order).",
      "Yellow if category matches the file dominant but subcategory differs from both the file dominant subcategory and neighbours, or category is a secondary but sizeable category (>=15% of file lines and >=2 routines).",
      "Red if category differs from the file dominant and from neighbours (isolated foreign routine).",
      "Whole files of one category are fine (no flags). Ignore equate rows (ram*.asm). Low-confidence classifications are capped at yellow (never red).",
    ],
    games: all,
  };
  const text = JSON.stringify(out, null, 0) + "\n";
  if (args.out) fs.writeFileSync(args.out, text);
  else process.stdout.write(text);
  for (const g of args.games) {
    const s = all[g].summary;
    console.error(g + ": routines=" + s.routines + " lines=" + s.lines + " low=" + s.low + " yellow=" + s.yellow + " red=" + s.red);
  }
}

if (require.main === module) main();
module.exports = { classifyOne, buildRows, assignPlacement, syncLineage, loadNDR };
