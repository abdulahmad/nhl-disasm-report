# BG scroll / PPU names: 93S vs 94S by usage

The two columns in the screenshot are not the same kind of symbol, so they should not be paired row by row.

* **Left (93S `ram93s.asm` lines 45-70)**: SNES hardware register equates (`INIDISP = $2100` .. `VMDATAH = $2119`).
  No RAM, no bytes.
* **Right (94S `ram94s.asm` lines 74-106)**: RAM variables (`$07xx`), mostly shadows the NMI copies to those registers.

94S has the exact same register equates, same names and values, in `src/inc/snes_regs.asm`. The report
does not index that file (0 hits for `snes_regs` in `docs/data/94S.js`), so in the RAM view the 93S register
block lines up against the 94S shadow block. That is the whole reason they look like a pairing.

## 1. Register equates (BG1SC .. VMDATAH, MOSAIC, INIDISP): EXACT match, nothing to do

Same name, same address, same register, used the same way (`sta.w BG1HOFS` twice for low/high, etc.) in both games.

## 2. 94S scroll shadows vs 93S: how each game drives BGnHOFS / BGnVOFS

| | 93S | 94S |
|---|---|---|
| storage | none: no RAM shadow. Each VBlank handler writes the registers directly | 6 words `BG1HScroll`..`BG3VScroll` ($07D6-$07E1) |
| who writes the PPU | the VBlank variant for the screen: `VBlank` (rink, BG2), `VBlank_Cram` (playoffs, BG1H = `Hscroll&7`), `VBlank_VScroll` (title, BG1V = `d0`), plus `InitPPU` / `TeamRosterScreen` zeroing | one place every NMI: `NMI_HookReturn` loop copies the 6 words to $210D-$2112; plus `IRQ_BG1Scroll` mid-frame (BG1VOFS from `BG3VScroll`) |
| BG4 | `InitPPU` zeroes BG4HOFS/VOFS once; never set again | never written (shadow list stops at BG3; only `BG4SC` in the intro) |
| reset | `InitPPU`: all BG1-4 H/V = 0 | `ResetPPURegs`: H = 0, V = $FFFF for BG1-3 |

### Per variable

| 94S | 93S counterpart by usage | verdict |
|---|---|---|
| `BG2HScroll` | value 93S `VBlank` writes to BG2HOFS: `Hscroll + $C0` | EXACT job (94S `updatescroll_rows .4`, same formula, same BG), but 93S has no variable to rename |
| `BG2VScroll` | value 93S `VBlank` writes to BG2VOFS: `vramrow*8 | (Vscroll&7)` | EXACT job, same as above |
| `BG1HScroll` | 93S playoff `VBlank_Cram` writes `Hscroll&7`; 94S playoffs write `Hscroll-$100` (also used as a counter by `TitleWindowWipe`) | same register, different screens/values: NO variable match |
| `BG1VScroll` | 93S title `VBlank_VScroll` writes BG1VOFS from scratch `d0` | role similar (title scroll), but `d0` is a general scratch: NO match |
| `BG3HScroll`, `BG3VScroll` | 93S never scrolls BG3 after `InitPPU` | NO match (94S-only; BG3VScroll also feeds the IRQ split) |
| `IniDispShadow` ($0762) | none. 93S hard-writes `INIDISP_FBLANK` at the top of each transfer VBlank and `vb2` restores `brightness` | NO match. 94S uses it as the "screen blanked" flag (bit 7 checked by DMAToVRAM, FillVRAM, MapPartToVRAM, DMAToCGRAM) |
| `brightness` ($0AD3) | 93S `brightness` ($04) | EXACT, already the same name: fade level 0-15 stepped by the fade code, written to INIDISP in vblank (93S `vb2`, 94S `BrightnessHook`) |
| `CGDMA*`, `FrameHook*`, `NMIHook*`, `IRQHook`, `IRQVTime/HTime` | none: 93S has a fixed VBlank vector per screen, a DMA list (`DMAList`/`DMAlistend`) and `hcount` IRQs | NO match (94S engine rewrite) |
| `ClipTopUnused`, `ClipBottomUnused` | none | NO match (written once, never read) |

Genesis has no counterpart for any of these names: the VDP scroll lives in VSRAM and the H-scroll table in
VRAM, written from `Hscroll`/`Vscroll` by the VBlank code. The usage match for the rink is at the
`Hscroll` / `Vscroll` / `vramrow` level, which all four games already share by name.

## Renames / ordering that follow

* **No renames.** The only exact usage matches (BG2 rink scroll) have no named 93S variable, and `brightness`
  already matches.
* The 94S comments on `BG2HScroll` / `BG2VScroll` already say "as 93S BG2HOFS / BG2VOFS value", which is right.
* Optional, build-safe tidy (equates only): move the 93S register block out of `ram93s.asm` into
  `src/inc/snes_regs.asm` like 94S, or have the report index 94S `snes_regs.asm`, so the RAM view stops
  pairing registers with shadows. Not done; say if you want it.
