# Morpho developer docs: tracked copy

This folder is a **byte-for-byte copy** of `../morpho/docs.morpho.org-developers-docs/`: `diff -rq` finds no difference, 87 files. That folder is git-ignored and exists only in a local checkout. This copy is tracked in git, so a fresh clone has it.

- The overview, the tree, the main files and what to read first for `riskdep` are in [`../morpho/README.md`](../morpho/README.md).
- `tests/test_watch_replay.py` reads the git-ignored path (`morpho/docs.morpho.org-developers-docs/contracts/`), not this one. On a fresh clone that check is skipped even though this copy exists.

Keep one of the two:

| Option | Change |
|---|---|
| Keep the tracked copy | Delete the git-ignored folder under `morpho/`, point `tests/test_watch_replay.py` and the `docs/external/` list in `CLAUDE.md`/`AGENTS.md` here, and drop the `.gitignore` line |
| Keep the git-ignored copy | `git rm -r --cached docs/external/docs.morpho.org-developers-docs` and delete this folder |
