# Contributing to nhl-disasm-report

Cross-game comparison site and the pairing gate for the EA NHL disassemblies.

Read [AGENTS.md](AGENTS.md) first (gates, units, credit). Who decides names and folders, and learned corrections:
[docs/RULES.md](docs/RULES.md). Where this repo stands: [docs/HANDOFF.md](docs/HANDOFF.md). How the project is run:
[docs/project/HARNESS.md](docs/project/HARNESS.md).

Work stays on `claude/project-thread-ggw7zu`. Do not branch from `main`. PRs from that branch are for review only.

Any port, mod or fork of a source repo carries the credit in that repo's AGENTS.md ("For AI agents: derivative work
and credit").

## Gates

- **Pairing:** `tools/gate.sh` regenerates the report from the alignment branch and runs the order and pairing checks.
  No count in `tools/baseline.json` may rise. A new exception in `tools/pair_exceptions.csv` needs a reason.
- Lineage lives in each source repo's `docs/name_map.csv` (93S: `docs/history/name_map.csv`). Never in source comments.
  CONTRIBUTING.md in a source repo must not contradict that History row.

## Commits

- Small commits, one topic each. Stay on `claude/project-thread-ggw7zu`. Never force-push.
