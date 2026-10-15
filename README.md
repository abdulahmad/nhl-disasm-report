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

Each file shows a proportional bar and a legend: the share of lines whose routine matches each comparison file (or a set of files), with grey for NEW/unmatched. Every routine gets a coloured header. Hover over a header or a bar segment to see its matches in **all** comparison targets. The URL hash (`#s=94G&v=files&c=93G&f=5`) keeps the current view, so you can link to it.

The footer lists the commit SHA of every source repo used.

## Matching method and caveats

- A routine matches a comparison file when one of its names (lowercased), or a name linked to it through the name maps, is defined as a label in that file. The weight is the routine's line count. A routine that matches several files splits its weight across them.
- Lineage aliases come from `docs/name_map.csv` in the source repos: the `old,new` columns (93G, 94G) and the `old_name,name` columns (95G, 96G). They are joined in one union-find graph, so a chain of renames (92 → 93 → 94 → 95) links up. The SNES maps (address → name) carry no lineage, so they are not used. 92G has no map.
- **Name-based only.** No code is compared. A shared generic name (`loop`, a table name) can link code that is not related. Equates and RAM labels (`equ`/`=`/`rs` lines) are skipped, but a RAM or data label written as a plain label still counts as a "routine".
- **Grey does not always mean new code.** It can also mean a rename that no name map records, or code that came from somewhere the report does not cover.
- SNES routines match on the file stem plus every global label in the file, so a file with many labels can match several files.
- Local labels (`.x`, `@x`) and anonymous labels are not routines; they stay in the routine above them.

## Regenerate

```sh
python3 tools/generate.py            # fetch origin/main of every source repo into .cache/src, write docs/
python3 tools/generate.py --offline  # reuse .cache/src as it is
```

Python 3 stdlib and `git` only. The source repos are shallow-cloned into `.cache/src` (gitignored) and are only read: nothing is committed or pushed to them. Output: `docs/index.html` plus one `docs/data/<id>.js` per subject game, loaded on demand (a script tag, so the page also works from `file://`). The same source SHAs give byte-identical output: iteration is sorted and the only "version" data is the SHAs.

## For agents

To publish a new version:

1. `git pull --ff-only origin main` in this repo.
2. `python3 tools/generate.py` (needs network; it updates `.cache/src` to each repo's `origin/main`).
3. Check it is deterministic: `sha256sum docs/index.html docs/data/* > /tmp/a && python3 tools/generate.py --offline && sha256sum docs/index.html docs/data/* | diff - /tmp/a`.
4. Optional check: `cd docs && python3 -m http.server 8765`, then open `http://localhost:8765/#s=94G&v=files&c=93G`.
5. `git add docs && git commit -m "Regenerate report"`. Put the source SHAs from the generator output in the message body. Then `git push origin main`. Never force-push.
6. Never edit, commit to, or push to the source repos (`.cache/src/*`). They are read-only inputs.

Change the viewer in `tools/template.html` and the parsing and matching in `tools/generate.py`, then regenerate and commit the code and `docs/` as separate commits.
