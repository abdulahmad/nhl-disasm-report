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
- **SNES subjects**: view *routine groups*: every subfolder of `src/routines` is a "file" (nested subfolders nest at depth +1) and every `.asm` directly in that folder is a routine named by its file stem. Group bands are contiguous runs in bank-include (ROM) order, so a folder interleaved across banks appears as multiple bands rather than one mega-band. View *banks*: every `src/banks/*.asm` include list is a "file" in org/ROM order; each `incsrc` of a routine `.asm` is a routine (stem), and non-`incsrc` stretches show as `(inline …)` / `(incbin …)`. Comparison matching for SNES routines is by `.asm` stem only.
- **Comparison**: any other Genesis game (matched to its files), or an SNES game as *routine groups* or *banks*.


- **Categories** (`v=cat` in the URL hash; 93G and 94G only for now): a sortable, filterable table of every code routine with a heuristic category and subcategory, confidence, and a placement flag (yellow / red) when the routine looks out of place in its source file. Per-category totals, per-file flag counts and top offenders sit above the table. Click a row to jump to that routine in the file view. Other subject games show "not categorised yet". On a whole-ROM view for a categorised game, an optional **tint ROM by category** checkbox colours the bar by category instead of by comparison match.

**Placement rule (deterministic).** For each source file, the dominant category (by total lines) and its dominant subcategory are computed. A routine is **yellow** if its category matches the file dominant but its subcategory differs from both that dominant subcategory and its ±3 neighbours in the file, or if its category is a secondary but sizeable share of the file (≥15% of lines and ≥2 routines). It is **red** if its category differs from both the file dominant and its neighbours (isolated foreign routine). Whole single-category files are unflagged; RAM/equate files are ignored; low-confidence hits are capped at yellow. The hierarchy (colours, file defaults, placement knobs) lives in `tools/categories.json` and is editable; the classifier is `tools/classify_routines.js` (Node), invoked by `generate.py`.

- **Layout** (`v=layout&a=93G&b=94G` in the URL hash): two games' whole-ROM layouts side by side. No origin comparison — each file band is coloured by a stable hash of the file stem with the game year suffix stripped (so `stats93` / `stats94` share a colour). Nesting indentation and parent brackets are on (same as the ROM view's nesting mode). Routines are subtle subdivisions within each file band. Hover for file, range, depth and routine; click opens that file in the file view for that game. Each side has its own game selector (SNES offers banks or groups). Bar height scales with line count; **Normalise heights** (`&norm=1`) makes both bars the same height.

- **Whole ROM** (`v=rom` in the URL hash; for SNES `v=rom:banks` (true ROM order) or `v=rom:groups`): the whole ROM as one tall vertical bar, top to bottom in ROM/include order. Each file is a band (white boundary line, with the file name and address beside it where there is room), split into its routines. Heights are by line count, not bytes. Colours and legend are the same as in the file view. Hover a routine for its file, name, matches and line count. Click it to open that routine in the file view. A **Show nesting** checkbox (on by default; `&nest=0` in the hash turns it off) indents each file band to the right by its include depth (15px per level, bar narrows accordingly) and draws a thin vertical bracket in the parent file's colour beside its descendants. Parent files that also contain code keep their own segments at their depth; included files sit indented under them in ROM/include order.

- **Include tree** (`v=tree&a=94G&b=95G` in the URL hash; last in the view list): two panes, each with its own game picker, defaulting to 92G (left) and 93G (right) when the tree is entered with no `a`/`b` given, showing that game's source as built. The root is the build's top-level file (the same one the files view walks: `hockey.asm`, `hockey93.asm`, `nhl94.asm`, `nhl95.asm`, `nhl96.asm`, `nhlpa93snes.asm`, `nhl94snes.asm`). Under each file, its routines (every label that starts a routine in the files view) and its included files are listed in the exact order they appear in that file, recursively. Genesis includes follow the files view rule (`include` of a `.asm`, `macros/` and `stubinc/` skipped; `IF` blocks are not evaluated, so both arms are listed). SNES follows the build: root → each `incsrc`'d `.asm` (`inc/` and `macros/` skipped) → for each `src/banks/*.asm`, its `incsrc` lines in order; a `src/routines/<group>/x.asm` is a routine named `x` (one line, as in the rest of the report), any other included `.asm` (`data/…`) is shown as a leaf `[data]` file; `incbin` and inline stretches are not shown. Each routine line shows the start of its comment, cut to one line: the `;` comment on the label line plus the pure comment lines straight after it; if the label line has none, the comment block straight above the label (no blank line between). Separator-only lines (`;-----`, `>>>>`) are dropped. For an SNES routine file the comment of its stem label (else the first label) is used.
  - **Bold** = the routine also exists in the other pane's game; plain = it does not. Existence uses the same name matching as the rest of the report (label name or `name_map` lineage alias, against the routines in the other game's tree; SNES by stem).
  - **Yellow** (also bold) = it exists in the other game, but in none of the matching files. **Matching file rule:** compare the file's last path part without the extension, lowercased, cut at the game year (`92`–`96`) together with anything after it. So `stats93.asm` = `stats94.asm`, `engine/logic95.asm` = `logic94.asm` = `engine/logic96_ass.asm` (96G split files match their base), `hockey.asm` (92G) = `hockey94.asm`. Directories are ignored. An SNES routine's file is its `src/routines/<group>/` folder (the report's SNES "file"), so SNES `routines/logic/` = Genesis `logic94.asm`; the bank it is included from is not used for matching.
  - Both trees sit in one pane and scroll together. Any line with children (a file, or a routine with labels) has a triangle (▾ / ▸) that collapses or expands it. It opens with only the root expanded (its direct children visible); every other file and every routine starts collapsed. A triangle on a node that has a match in the other game (the same match click-to-align uses) also expands / collapses that match; expanding it also expands its ancestors. Nodes with no match (and labels) toggle only their own side.
  - The tree lists `name = value` equates (written with a space or tab after `=`) as routine-like rows, as the report did before `2f02f6c`, so RAM files such as `ram.asm` / `ram93.asm` expand. Everywhere else (files view, categories, ROM views, unit counts) those equates are skipped as documented below.
  - **Labels:** under each routine, its local labels (`.x` / `@x` at the start of a line) in source order, with the start of a same-line comment. A local label after an include and before the next routine has no routine above it in the tree and is not shown. SNES: inside each routine `.asm`, every label other than the routine's own (other global labels and `.x` labels), in source order. Labels get no comparison styling.
  - **Toggles** (both columns): *show routines* (on), *show labels* (on), *hide matching routines* (off; when on, hides bold routines that are in a matching file, but keeps yellow ones, since those are a difference). Changing a toggle resets the alignment. If an alignment target is hidden by *hide matching routines*, it is shown until the next toggle change.
  - **expand all** / **collapse all** apply to both columns (collapse all returns to only the root expanded); both reset the alignment.
  - **State on refresh:** the expanded nodes, the alignment shift and the scroll position are kept in `localStorage` per game pair (`ndr.tree.<A>|<B>`), by stable node ids (file path; for a routine, its file + name), so they survive a regenerate where the names are unchanged. The toggles are kept in `ndr.treeTO`.
  - A legend above the columns explains bold / yellow / plain and how files, routines and labels look. Click a matching name (a bold / yellow routine, or a file that has a matching file in the other game by the rule above) to align: collapsed ancestors are expanded on both sides, then the other column is shifted down (top padding) so the match sits on the same row as the clicked line, which stays where it was on screen (the clicked column is padded instead when the match is further down). Both lines flash. Clicking another match re-aligns; **reset align** or clicking the root line removes the shift. The match is the other game's routine with the same name if there is one, else one in a matching file, else the first; for a file, the first file in the other tree with the same key (roots are not matched). The generator stores both (`cmp.<id>.r`, `cmp.<id>.f`).
  - Hover a routine for an instant tooltip: its full comment and the file(s) it lives in in the other game, or `not in <game>`. The info line counts routines, bold and yellow for each side. Data: `tree` in each `docs/data/<id>.js` (`nodes`, then per other game `cmp.<id>` with the matching files per routine and the yellow routine indexes), built by `tools/generate.py`.

**Address ranges and nesting.** The file dropdown and the whole-ROM labels show each file's ROM range (`$start-$end`, hex), indented by include depth (`└` = included from the file above). A file that only includes others (e.g. 95G `engine95.asm`) is listed with no routines, so the nesting still shows. Hub files that mix their own code with includes (92G `hockey.asm`, 93G `hockey93.asm`) are split into separate bands at depth 0 for each of their own code segments, interleaved in true ROM order with the included files at depth 1. `stubinc/` is skipped (standalone test builds, not part of the ROM). How a range is worked out, in order (the tooltip names the source):
1. the include comment (`; $XXXXXX` or `; $XXXXXX-$YYYYYY`);
2. else `docs/function_origins.csv` (file, address, size: min address to max address+size-1), where a repo has one (95G);
3. a missing end = the next file's start - 1; a file that includes others is widened to cover them.
SNES banks use their `org` line and assume the LoROM bank runs to `$xxFFFF`. SNES routine groups are not contiguous, so they list the banks they occur in. Anything else shows as `$??????-?` (unknown). The `lst/` files in the repos are IDA dumps with no build addresses, so they are not used.

Each file shows a proportional bar and a legend: the share of lines whose routine matches each comparison file (or a set of files), with grey for NEW/unmatched. Every routine gets a coloured header. Hover over a header or a bar segment for an immediate tooltip with its matches in **all** comparison targets. The URL hash (`#s=94G&v=files&c=93G&f=5`) keeps the current view, so you can link to it. The last hash is also stored in `localStorage` (`ndr.hash`): opening the page with no hash restores the last view, games and file; a hash in the URL always wins.

The footer lists the commit SHA of every source repo used.

## Matching method and caveats

- A routine matches a comparison file when one of its names (lowercased), or a name linked to it through the name maps, is defined as a label in that file. The weight is the routine's line count. A routine that matches several files splits its weight across them.
- Lineage aliases come from `docs/name_map.csv` in the source repos: the `old,new` columns (93G, 94G) and the `old_name,name` columns (95G, 96G). They are joined in one union-find graph, so a chain of renames (92 → 93 → 94 → 95) links up. The SNES maps (address → name) carry no lineage, so they are not used. 92G has no map.
- **Name-based only.** No code is compared. A shared generic name (`loop`, a table name) can link code that is not related. Equates and RAM labels (`equ`/`=`/`rs` lines) are skipped, but a RAM or data label written as a plain label still counts as a "routine".
- **Grey does not always mean new code.** It can also mean a rename that no name map records, or code that came from somewhere the report does not cover.
- SNES routines match on the `.asm` file stem only (not every label inside the file).
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
4. Optional check: `cd docs && python3 -m http.server 8765`, then open `http://localhost:8765/#s=94G&v=files&c=93G` or `http://localhost:8765/#s=94G&v=cat`, or `http://localhost:8765/#v=layout&a=93G&b=94G`, or `http://localhost:8765/#v=tree&a=94G&b=95G`.
5. `git add docs && git commit -m "Regenerate report"`. Put the source SHAs from the generator output in the message body. Then `git push origin main`. Never force-push.
6. Never edit, commit to, or push to the source repos (`.cache/src/*`). They are read-only inputs.

Change the viewer in `tools/template.html`, the parsing and matching in `tools/generate.py`, and the category rules in `tools/categories.json` / `tools/classify_routines.js`, then regenerate and commit the code and `docs/` as separate commits. Routine addresses for the categories table come from `tools/routine_addrs.json` (optional overlay) so regenerate stays deterministic without local assembler listings.
