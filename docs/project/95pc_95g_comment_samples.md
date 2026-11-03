# Samples: "95G:" notes on 95PC functions

Nothing has been applied yet. These are samples for review.

## The rule

* **Which functions get a note:** a 95PC function with a PC name that does the job of a 95G routine with a different name. A function that already has the 95G or 94G name needs no note.
* **What the note looks like:** one line, `; 95G: <file> <routine> (<what is the same / what differs>)`. It goes right above the function's `; C:` line, or above its label when there is no C line. It sits under the function's own description if it has one; otherwise I add a one-line description too.
* **Why this form:** the line is plain asm text, so the bytes don't change. The report can read it later (an alias that links the two without a rename). A function standing for several 95G routines lists them all.

## Samples

### 1. The trade screen (`front/trade.asm`)

Before:
```
; C: src/c/front/trade/TradeHitTest.c (TradeScreen)
%ifdef CBUILD
%include "c/front/trade/TradeHitTest.TradeScreen.inc"
%else
TradeScreen:
```
After:
```
; The Trade Players screen of a league: both rosters side by side, one player picked on each side.
; 95G: front/trade95 TradePlayers (the same screen; the PC swaps one player for one, with no CheckTrade rules or GM decision)
; C: src/c/front/trade/TradeHitTest.c (TradeScreen)
%ifdef CBUILD
...
```

### 2. Picking the award winners (`front/awards.asm`)

One PC function does the job of a family of 95G routines:
```
; End of season: the winner of each award from the season stats.
; 95G: front/awards95 FindAwardFinalists, ScanHart .. ScanConnSmythe, HartScore .. VezinaScore (one scorer per award there, one function here)
PickAwardWinners:
```

### 3. The award screens (`front/awards.asm`)

```
; One screen per award, with the winner's photo and name.
; 95G: front/awards95 SeasonAwards, AwardsLoop (95G shows the three finalists before the winner)
; C: src/c/front/awards/PickAwardWinners.c (ShowAwardScreens)
```

### 4. The playoff tree (`front/playoff.asm`)

```
; The EASN playoff tree screen.
; 95G: engine/playoff95 PlayoffScreen (the same tree; 95G scrolls it a page at a time)
; C: src/c/front/playoff/PlayoffTreeScreen.c
```

### 5. The game summary (`front/summary.asm`)

```
; The game summary: goals and penalties, one page per period (p1, p2, p3, overtime).
; 95G: front/summary95 ScoringSummaryScreen, PenaltySummaryScreen (two scrolling lists there, one paged screen here)
GameSummaryScreen:
```

### 6. The credits (`front/title.asm`)

```
; The credits after the title.
; 95G: front/title95 CreditsPrintRow, CreditsLineScroll (scrolling credits under the title)
; C: ...
ShowCredits:
```

## Before I apply them

* Each "what differs" clause comes from reading both bodies. I've checked samples 1 and 2 (the trade and awards pilot). For 3 to 6, the clauses come from the 95G headers and the PC strings, and I'd check each body before writing it.
* I expect about 30 to 50 notes in all: awards, trade, create player, playoffs, season, summary, stats, title and the shootout. Most of the PC front end (desk, dialogs, league files) has no 95G partner and gets no note.
