# 93S vs 94S: matches among the unmatched symbols in the include-tree screenshots

Source: NHLPA93SNES `src/ram93s.asm`, NHL94SNES `src/ram94s.asm` and the routines that use them; report data
from nhl-disasm-report `docs/data/93S.js` / `94S.js` (tree compare 93S vs 94S).

## 1. fadeout / fadein

What the report does now: 93S RAM `fadein` / `fadeout` are shown as matched (yellow: matched, but not in a
matching file) because their lowercased names equal the 94S **routine** stems `FadeIn` / `FadeOut`
(`routines/snes/`). That is a name collision between a RAM variable and a routine, but they are related by purpose.

What the code says:

| 93S | 94S | how they line up |
|---|---|---|
| `fadein` ($08) | `fadestep` ($0AD1), positive values | **EXACT** same encoding. 93S vb2: >1 = count down a delay, 1 = raise `brightness` to 15 then clear. 94S NMI_Tick: >1 = `dec fadestep`, 1 = `inc brightness` to 15 then clear. 93S steps every 4th frame, 94S every frame. |
| `fadeout` ($06) | `fadestep` = $FFFF (negative values) | **LIKELY**. 93S vb2: nonzero = lower `brightness` every 4th frame to 0, then clear. 94S: $FFFF = lower `brightness` each frame to 0, then clear `fadestep`. Note: nothing in 93S ever sets `fadeout` (only vb2 reads and clears it), so 93S never fades out this way. |
| sta `fadein` inline (setupice, TitleScreen, setoptions, setvideo) | routine `FadeIn` (sets fadestep = 5 + installs BrightnessHook) | same job; 93S writes the variable directly, 94S calls a routine |
| none (fadeout never set) | routine `FadeOut` | 94S only in practice |
| none | routine `WaitFadeOut` (loop until brightness = 0) | 94S only |
| `brightness` | `brightness` (+ `BrightnessHook` writes it to INIDISP) | already matched by name |

So the routine match FadeIn/FadeOut is right in spirit (same feature), but the real data counterpart of
`fadein`/`fadeout` is `fadestep`, which the report shows as unmatched. One 94S word does both 93S jobs, so no
single rename makes all three line up.

## 2. Other unmatched symbols in the screenshots

Already matched by name (not unmatched): `gm*`, `sflags`, `sfpz`, `sfspdir`, `sfssdir`, `sfwrap`, `sfslock`,
`sf2*`, `Vscroll`, `vramrow`, `brightness`, `palbuffer`.

93S unmatched in the screenshot: `DMAlistend`, the addframe `spr*` vars, `SattHi`, `sfpj`, `sfscrl`.

| 93S | 94S | conf. | evidence |
|---|---|---|---|
| `sfscrl` ($0020 in sflags) | raw `#$0020` on `sflags` in `replay/ReplayMode.asm` (5 places) | **EXACT** | Same bit, same use: cleared on replay entry (93S :48, 94S :47), set when the d-pad scrolls by hand / free camera (93S :135, 94S :390), cleared on exit and on unlock (93S :232/:267, 94S :380/:561/:677). 94S has no equate for it, and its comments call it "scroll lock", which is `sfslock` ($0040). |
| `sfpj` ($0002) | `pausepad` | LIKELY (replaced) | Both say which controller paused. 93S `getpzjoy` tests `sfpj` to pick ReadJoy1/2; 94S `getpzjoy` reads `pausepad` (a pad index, up to 5 pads). 94S never touches sflags bit $0002. |
| `DMAlistend` | `DMAQueueTail` | LIKELY | 93S: end offset of the 7-byte DMAList that VBlank sends and empties. 94S: write index of the 8-byte DMAQueue ring. (`DMAList` ↔ `DMAQueue` likewise; both are also unmatched.) |
| `sprcount` | `OAMNext` | LIKELY | "next OAM entry" in both; 93S index, 94S byte offset into OAMDrawBuf. 93S's 128-entry check on sprcount is 94S `SpritesLeft`. |
| `sprox` / `sproy` | `PieceX` / `PieceY` | LIKELY | Both are the current piece's x/y offset read from the frame record, then turned into the OAM x/y. |
| `sprtile` | `PieceTile` | LIKELY | Tile of the current piece that goes to OAM +2 (93S from the VRAM cache, 94S piece word + first tile). |
| `sprpal` (+ `sprpriority`) | `sprattr` | POSSIBLE | 93S ORs sprpal, sprpriority, sprpattr and the flips into the attribute byte; 94S passes one attribute word `sprattr` (priority, palette). `sprpattr` (per-piece flip bits $C0) has no 94S var. |
| `sprbigslot` / `sprslot` | `BlockRuns` / `TileRuns` | POSSIBLE | Same split of sprite VRAM into a 16x16 area and an 8x8 area; 93S uses a rotor, 94S a free-run list. `sprbigslotend` / `sprslotend` have no counterpart. |
| `sprslotlife` | `CacheUseMark` | POSSIBLE | How long cached tiles live: 93S frames after last use ($12), 94S use bits shifted out each frame (start 2). |
| `sprframetime` | `FrameCacheOf` (+ `FrameCacheTile`, `FrameCacheUse`) | POSSIBLE | Per sprite frame cache lookup. 93S: 4 bytes per frame (last-sent clock, VRAM tile); 94S: per frame its cache entry, which holds tile and use bits. |
| `sprslottime` | `FrameCacheUse` | POSSIBLE | 93S ages each VRAM slot; 94S ages each cache entry. |
| `Satt` (not in the shot) | `OAMDrawBuf` / `OAMShowBuf` | POSSIBLE | 93S one OAM shadow; 94S two buffers (pointers) and `OAMReady`. |
| `SattHi` | none | NO MATCH | 94S keeps the high table inside the OAM buffer, written through `OAMHiPtr` / `OAMHiShift` / `OAMHiMasks`. 93S's code-local `.himask` table is the counterpart of `OAMHiMasks`. |
| `sprpieces` | none (register `r0`) | NO MATCH | 94S DrawSpritePieces keeps "pieces left" in scratch r0; `PieceNext` is the next record offset, a different job. |

94S only (no 93S counterpart): `OAMReady`, `OAMShowBuf`, `OAMLastEnd`, `OAMHideEnd`, `OAMHiPtr`, `OAMHiShift`,
`SpritesReserved`, `SpriteVRAM`, `SpriteBlockTiles`, `DrawFrameNum`, `FrameByNumber`, `PieceSize`, `PieceNext`,
`FrameCacheCount`, `FrameCacheAddr`, `FrameCacheBank`, `FrameCacheNum`, `FrameCacheAlloc`, `FrameTilesFail`,
`BlockRunPrev`, `TileRunPrev`, `UnusedSineTable` (its own comment: no counterpart in 93S/94G/Genesis),
`ResetStub` (empty rtl), `WaitFadeOut`.

The sprite engine rows are role matches only: 94S rewrote the engine (double-buffered OAM, frame tile cache with
run allocators), so none of them is a safe rename.

## Safe follow-ups (not done)

1. 94S: add `sfscrl = $0020` beside `sfslock` in ram94s.asm, use it in ReplayMode.asm's 5 `#$0020` / sflags
   lines and fix their "scroll lock" comments. Byte-identical; gives the report a real match.
2. 94S `fadestep` comment: note 93S splits it into `fadein` (positive) and `fadeout` ($FFFF).
3. Report: either keep the RAM-to-routine name match for fadein/FadeIn, or only match RAM rows with RAM rows.
