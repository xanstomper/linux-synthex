# Contributing & CI (New-era, 2026.10)

Concise guide for the **current** (AIOS-era) repo. The older, fuller
`docs/developer/contributing.md` still applies for community conduct and
roles; this adds the **engineering gate** that matters for the AIOS and
the build.

## The non-negotiable guard

```bash
configs/tests/verify.sh; echo $?
```

- Must output `RESULT: 17 passed, 0 failed` and exit `0`.
- Add this to your CI / pre-commit hook.
- Any PR touching `configs/`, `packages/`, `build/repo/`, or the AIOS
  daemons must keep it green.

Suggested pre-push hook:

```bash
#!/bin/sh
if ! (cd "$(git rev-parse --show-toplevel)" && bash configs/tests/verify.sh); then
  echo "verify.sh failed — fix before pushing" ; exit 1 ; fi
```

## Contribution checklist

| Item | Command / file |
|---|---|
| Lint bash | `bash -n <file>` |
| Compile python | `python3 -m py_compile <file.py>` |
| Compile daemons | `cargo check --workspace` (fast), then `cargo build --workspace --release` |
| Build a spec | `rpmbuild -ba --nodeps <spec>` or `build_batch.sh <spec>` |
| Re-index repo | see `docs/BUILD.md` |
| Full AIOS verify | `configs/tests/verify.sh` |
| Bump docs | `docs/` (update the map + the relevant feature doc) |

## What "done" means for a change

1. It compiles / lints.
2. `verify.sh` passes.
3. `%files` mirror `%install` for any changed spec.
4. The relevant `docs/*.md` updated (or the index touched).
5. For runtime changes, show a **real** output (not just "works").

## Areas that need a Fedora container

- Rebuilding any pending package (`docs/PENDING.md`).
- Building the ISO (`docs/ISO.md`).
- Rebuilding COSMIC/rust-toolchains.

Do not mark those "fixed" purely with a host-side `verify.sh` green.

## Branching / PR flow

1. Fork + branch off `main`.
2. Make the change on the branch.
3. Run the checks above.
4. Open a PR. Reference the feature doc.
5. CI runs `verify.sh`; if it fails, the PR is blocked.

## Code standards (short)

- Shell: POSIX-ish; avoid `%meson`/`%py3_*` in specs unless the macro
  exists (see `docs/ENV.md`).
- Python: stdlib where possible; no external deps for `update-sync`.
- Rust: `cargo fmt` + `cargo clippy` (when the workspace builds).
- Docs: prefer `docs/*.md` root for new content; port legacy into it.

## See also
- `docs/developer/contributing.md` — full project-wide contributing guide.
- `docs/TESTING.md` — how to test everything.
- `docs/PENDING.md` — what’s intentionally unbuilt.