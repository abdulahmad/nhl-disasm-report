# NHL disassembly origin report

Static report (GitHub Pages: https://abdulahmad.github.io/nhl-disasm-report/) that shows, routine by routine, where code in one NHL disassembly came from in another:

| id | repo | platform |
|---|---|---|
| 92G | NHL92Genesis | Genesis |
| 93G | NHLPA93Genesis | Genesis |
| 94G | NHL94Genesis | Genesis |
| 95G | NHL95Genesis | Genesis |
| 96G | NHL96Genesis | Genesis |
| 93S | NHLPA93SNES | SNES |
| 94S | NHL94SNES | SNES |

## What it shows

Pick a **subject** game, a **view**, and a **comparison** game.

- **Genesis subjects**, view *files*: the source files in include order (a pre-order walk of `include` lines from the top-level file: `hockey.asm`, `hockey93.asm`, `nhl94.asm`, `nhl95.asm`, `nhl96.asm`). The ROM address shows when the include line has a `; $XXXXXX` comment. Each label starts a routine.
- **SNES subjects**: view *routine groups*: every subfolder of `src/routines` is a "file" and every `.asm` in it is a routine (name = file stem plus its global labels). View *banks*: every `src/banks/*.asm` include list is a "file" and what it `incsrc`s are its routines. That lets you check that bank names fit their contents. Lines in a bank file that are not `incsrc` (org, incbin) show as `(inline …)` / `(incbin …)` units, so a bank that is still incbin shows as not disassembled yet.
- **Comparison**: any other Genesis game (matched to its files), or an SNES game as *routine groups* or *banks*.


- **Categories** (`v=cat` in the URL hash; 93G and 94G only for now): a sortable, filterable table of every code routine with a heuristic category and subcategory, confidence, and a placement flag (yellow / red) when the routine looks out of place in its source file. Per-category totals, per-file flag counts and top offenders sit above the table. Click a row to jump to that routine in the file view. Other subject games show "not categorised yet". On a whole-ROM view for a categorised game, an optional **tint ROM by category** checkbox colours the bar by category instead of by comparison match.

**Placement rule (deterministic).** For each source file, the dominant category (by total lines) and its dominant subcategory are computed. A routine is **yellow** if its category matches the file dominant but its subcategory differs from both that dominant subcategory and its ±3 neighbours in the file, or if its category is a secondary but sizeable share of the file (≥15% of lines and ≥2 routines). It is **red** if its category differs from both the file dominant and its neighbours (isolated foreign routine). Whole single-category files are unflagged; RAM/equate files are ignored; low-confidence hits are capped at yellow. The hierarchy (colours, file defaults, placement knobs) lives in `tools/categories.json` and is editable; the classifier is `tools/classify_routines.js` (Node), invoked by `generate.py`.

- **Layout** (`v=layout&a=93G&b=94G` in the URL hash): two games' whole-ROM layouts side by side. No origin comparison — each file band is coloured by a stable hash of the file stem with the game year suffix stripped (so `stats93` / `stats94` share a colour). Nesting indentation and parent brackets are on (same as the ROM view's nesting mode). Routines are subtle subdivisions within each file band. Hover for file, range, depth and routine; click opens that file in the file view for that game. Each side has its own game selector (SNES offers banks or groups). Bar height scales with line count; **Normalise heights** (`&norm=1`) makes both bars the same height.

- **Whole ROM** (`v=rom` in the URL hash; for SNES `v=rom:banks` (true ROM order) or `v=rom:groups`): the whole ROM as one tall vertical bar, top to bottom in ROM/include order. Each file is a band (white boundary line, with the file name and address beside it where there is room), split into its routines. Heights are by line count, not bytes. Colours and legend are the same as in the file view. Hover a routine for its file, name, matches and line count. Click it to open that routine in the file view. A **Show nesting** checkbox (`&nest=1` in the hash) indents each file band to the right by its include depth (15px per level, bar narrows accordingly) and draws a thin vertical bracket in the parent file's colour beside its descendants. Parent files that also contain code keep their own segments at their depth; included files sit indented under them in ROM/include order.

**Address ranges and nesting.** The file dropdown and the whole-ROM labels show each file's ROM range (`$start-$end`, hex), indented by include depth (`└` = included from the file above). A file that only includes others (e.g. 95G `engine95.asm`) is listed with no routines, so the nesting still shows. Hub files that mix their own code with includes (92G `hockey.asm`, 93G `hockey93.asm`) are split into separate bands at depth 0 for each of their own code segments, interleaved in true ROM order with the included files at depth 1. `stubinc/` is skipped (standalone test builds, not part of the ROM). How a range is worked out, in order (the tooltip names the source):
1. the include comment (`; $XXXXXX` or `; $XXXXXX-$YYYYYY`);
2. else `docs/function_origins.csv` (file, address, size: min address to max address+size-1), where a repo has one (95G);
3. a missing end = the next file's start - 1; a file that includes others is widened to cover them.
SNES banks use their `org` line and assume the LoROM bank runs to `$xxFFFF`. SNES routine groups are not contiguous, so they list the banks they occur in. Anything else shows as `$??????-?` (unknown). The `lst/` files in the repos are IDA dumps with no build addresses, so they are not used.

Each file shows a proportional bar and a legend: the share of lines whose routine matches each comparison file (or a set of files), with grey for NEW/unmatched. Every routine gets a coloured header. Hover over a header or a bar segment for an immediate tooltip with its matches in **all** comparison targets. The URL hash (`#s=94G&v=files&c=93G&f=5`) keeps the current view, so you can link to it.

The footer lists the commit SHA of every source repo used.

## Matching method and caveats

- A routine matches a comparison file when one of its names (lowercased), or a name linked to it through the name maps, is defined as a label in that file. The weight is the routine's line count. A routine that matches several files splits its weight across them.
- Lineage aliases come from `docs/name_map.csv` in the source repos: the `old,new` columns (93G, 94G) and the `old_name,name` columns (95G, 96G). They are joined in one union-find graph, so a chain of renames (92 → 93 → 94 → 95) links up. The SNES maps (address → name) carry no lineage, so they are not used. 92G has no map.
- **Name-based only.** No code is compared. A shared generic name (`loop`, a table name) can link code that is not related. Equates and RAM labels (`equ`/`=`/`rs` lines) are skipped, but a RAM or data label written as a plain label still counts as a "routine".
- **Grey does not always mean new code.** It can also mean a rename that no name map records, or code that came from somewhere the report does not cover.
- SNES routines match on the file stem plus every global label in the file, so a file with many labels can match several files.
- Local labels (`.x`, `@x`) and anonymous labels are not routines; they stay in the routine above them.
- **Categories are heuristic.** Labels, comments, file names and light code skims drive them; they are not a proven design document. Placement flags are deterministic given those labels, but a flag is only a hint that a routine may belong elsewhere.

## Regenerate

```sh
python3 tools/generate.py            # fetch origin/main of every source repo into .cache/src, write docs/
python3 tools/generate.py --offline  # reuse .cache/src as it is
```

Python 3 stdlib, `git`, and `node` (for `tools/classify_routines.js`) only. The source repos are shallow-cloned into `.cache/src` (gitignored) and are only read: nothing is committed or pushed to them. Output: `docs/index.html` plus one `docs/data/<id>.js` per subject game, loaded on demand (a script tag, so the page also works from `file://`). The same source SHAs give byte-identical output: iteration is sorted and the only "version" data is the SHAs.

## For agents

To publish a new version:

1. `git pull --ff-only origin main` in this repo.
2. `python3 tools/generate.py` (needs network; it updates `.cache/src` to each repo's `origin/main`).
3. Check it is deterministic: `sha256sum docs/index.html docs/data/* > /tmp/a && python3 tools/generate.py --offline && sha256sum docs/index.html docs/data/* | diff - /tmp/a`.
4. Optional check: `cd docs && python3 -m http.server 8765`, then open `http://localhost:8765/#s=94G&v=files&c=93G` or `http://localhost:8765/#s=94G&v=cat`, or `http://localhost:8765/#v=layout&a=93G&b=94G`.
5. `git add docs && git commit -m "Regenerate report"`. Put the source SHAs from the generator output in the message body. Then `git push origin main`. Never force-push.
6. Never edit, commit to, or push to the source repos (`.cache/src/*`). They are read-only inputs.

Change the viewer in `tools/template.html`, the parsing and matching in `tools/generate.py`, and the category rules in `tools/categories.json` / `tools/classify_routines.js`, then regenerate and commit the code and `docs/` as separate commits. Routine addresses for the categories table come from `tools/routine_addrs.json` (optional overlay) so regenerate stays deterministic without local assembler listings.
