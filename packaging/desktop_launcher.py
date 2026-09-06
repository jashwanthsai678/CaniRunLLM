"""Entry point for the standalone (PyInstaller) build.

The pip-installed `canirunllm` console script requires an explicit
subcommand (`canirunllm scan`, `canirunllm search ...`) because that's
the right default for a developer tool. A double-clicked desktop .exe
gets no command-line arguments at all, so this wrapper defaults to
`scan` in that case, and keeps the console window open with a visible
error (instead of a flash-and-vanish crash) if anything goes wrong
before the dashboard server starts.
"""

import sys


def main():

    if len(sys.argv) == 1:
        sys.argv.append("scan")

    from canirunllm.cli import main as cli_main

    try:
        cli_main()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 - must not vanish silently
        print()
        print("CanIRunLLM ran into a problem and had to stop.")
        print(f"Details: {exc}")
        input("Press Enter to close this window...")
        raise


if __name__ == "__main__":
    main()
