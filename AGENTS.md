# Agent rules

## Working rules (any tool)

Read, in this order, before any work: this file, `docs/RULES.md`, the Now block at the top of `docs/HANDOFF.md`, and the
stage of the shared plan that the Now block names (https://github.com/abdulahmad/nhl-disasm-report/blob/main/docs/ALIGNMENT.md; it is on the `claude/project-thread-ggw7zu` branch of nhl-disasm-report until merged).

* **Check:** `tools/gate.sh` (regenerates the report from the alignment branch and runs the order and pairing checks) before every commit. Moves and renames also run the pairing gate in nhl-disasm-report
  (`tools/gate.sh`); no count may rise. "It looks right" or "the model is confident" is never a check.
* **Unit:** one folder, one 94G file or one segment, small enough to finish in one session. A worker edits only that unit's
  files, the bank or include lines that point at them, and `docs/name_map.csv`.
* **Return:** a failed unit goes back alone, with the failing output, the file and line, the scope ("fix these files only")
  and the attempt number. At most 3 attempts, then the advisor. Never resend the batch.
* **Advisor** (top-tier model), only at three moments: before a stage plan is fixed, after the same failure twice, before a
  stage is called done.
* **Risk lanes:** moves and folds proven by the check and the gate go straight to the alignment branch. Renames that touch many
  files or other repos are listed for the owner to read. Never: retail-byte changes on `main`, force-push, edits to NHL92Genesis.
* **Learning edge:** every correction the owner makes and every confirmed cause of a failure becomes one line in
  `docs/RULES.md`, in the same commit.
* **Handoff:** before stopping, update the Now block in `docs/HANDOFF.md` and push. Never leave uncommitted work: an unfinished
  unit is pushed and marked WIP. Nothing lives only in one tool's chat or memory.
* **Branch:** alignment work collects on `claude/project-thread-ggw7zu` in every repo. `main` gets it when the owner merges. Exception (Abdul, 2026-11-03): in this repo only, agents may merge that branch into `main` once tools/gate.sh passes, so the live page is current.
* Which model does which job is set in `.cursor/rules/main.mdc` and `.claude/agents/`, not here.

