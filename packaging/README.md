# Building the standalone desktop .exe

This produces a single `CanIRunLLM.exe` that a non-developer can
double-click with no Python installation required. It's a separate
build from the pip package (`pip install canirunllm`) — same core
code, different entry point (`desktop_launcher.py`) so that
double-clicking with zero arguments defaults to `canirunllm scan`
instead of printing a usage message.

## Build

```bash
pip install -e ".[packaging]"
pyinstaller packaging/canirunllm.spec --noconfirm --distpath dist_exe --workpath build_exe
```

Output: `dist_exe/CanIRunLLM.exe` — a single self-contained file
(~15 MB). It self-extracts to a temp directory at startup, which adds
a couple of seconds to first launch; this is normal PyInstaller
onefile behavior, not a bug.

## What happens when a user runs it

1. Double-click `CanIRunLLM.exe`.
2. A console window opens and shows the same friendly scan output as
   `canirunllm scan` on the command line (hardware detected, N models
   analyzed, a plain-language summary).
3. It prints a `Dashboard: http://127.0.0.1:8765` line and opens the
   default browser to that address automatically.
4. Closing the console window (or Ctrl+C) stops the local server.

If something goes wrong before the dashboard starts, the console
window stays open with the error message and waits for Enter before
closing, instead of flashing and vanishing — see
`desktop_launcher.py`.

## Distribution

The built `.exe` is not committed to this repository (it's a large
binary build artifact, `dist_exe/` is gitignored). It should be
uploaded to a GitHub Release instead, and linked to from the
marketing site's download button:

```bash
git tag v0.1.0
git push origin v0.1.0
# then create a release on GitHub for that tag and attach
# dist_exe/CanIRunLLM.exe as a release asset (via the web UI, or
# `gh release create v0.1.0 dist_exe/CanIRunLLM.exe` if the GitHub
# CLI is installed and authenticated).
```
