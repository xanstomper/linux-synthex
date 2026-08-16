# Scaffold — empty placeholder directories

These directories exist on disk as **placeholders** but contain **no
tracked files**, so they are **not** on GitHub (git doesn't track empty
directories). Each is an intentionally-created empty folder for planned
content — not missing files. To materialize one on GitHub, add at least
one file inside it.

## Rationale / how to use

- They were scaffolded when the project was set up (e.g. `agent/providers`,
  `gui/ui/pages`, `security/pam`, `desktop/synthex-adaptive-ui`).
- Empty dirs don't show on GitHub and don't count in file totals.
- To keep a directory (with no content yet) on GitHub, commit a file in it
  (a `README.md` or `.gitkeep`); consider whether that's truly wanted.

## Count
99 empty directories on disk (a dedup of `docs/COMPONENT-CATALOG.md` scope).
