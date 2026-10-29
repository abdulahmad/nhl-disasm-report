# Handoff: nhl-disasm-report

## Status (2026-10-20)

- The report is regenerated from the latest `main` of all seven source repos (92G, 93G, 94G, 95G, 96G, 93S, 94S). The generated files are `docs/index.html` and `docs/data/<game>.js`; the same source SHAs give byte-identical output.
- Regenerate with `python3 tools/generate.py` (fetches each source repo at `origin/main` into `.cache/src`, read-only; `--offline` reuses the cache). Open a PR and merge it each time a source repo changes layout or names.
- Last sources: NHL94SNES `4919d57`, NHLPA93SNES `961fc06`, NHL94Genesis `efaafe0`.

## Open

- The report must be regenerated after the NHL94SNES comment pass finishes (see that repo's `docs/HANDOFF.md`; about 1,640 labels were still uncommented).
- 94S matches 93S by routine group; 94S folders follow the 94G files, so many 94S routines show as placed differently from 93S. That is expected, not a bug.
- SNES *groups* / `rom:groups` / a groups layout pane / a groups include-tree pane re-sort modules to the other game's include order (`targets.*.seq`). 93S vs 92G is `main`, `hockey`, `logic`, `middle`, `penalty`, `video`, then SNES-only modules. Banks view stays ROM order. Routines inside a group stay in ROM order.
