"""Draft registry entries for every candidate from discover_new_models.py.

Reads a candidates JSON file (see discover_new_models.py for the shape),
calls draft_candidate() for each, and writes scripts/drafts/SUMMARY.md
summarizing what was drafted, what was skipped, and what needs manual
attention before merging into registry/models.json + SOURCES.md.

A failure on one candidate (gated repo, no matching GGUF files, HTTP error)
is recorded and skipped rather than aborting the whole batch.

Usage:
    python scripts/draft_all_candidates.py candidates.json
"""

import argparse
import json

from _hf_common import DRAFTS_DIR, FetchError, draft_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("candidates_file", help="JSON file produced by discover_new_models.py")
    parser.add_argument("--quants", nargs="+", default=["Q4_K_M", "Q8_0"], help="Quantizations to look for")
    args = parser.parse_args()

    with open(args.candidates_file, "r", encoding="utf-8") as file:
        candidates = json.load(file)

    drafted = []
    skipped = []

    for candidate in candidates:
        repo_id = candidate["repo_id"]
        family = candidate["family"]
        gguf_repo = candidate.get("gguf_repo")
        print(f"Drafting {family} ({repo_id}) ...")
        try:
            _, _, warnings = draft_candidate(
                repo_id=repo_id,
                family=family,
                gguf_repo=gguf_repo,
                quants=args.quants,
                caller="scripts/draft_all_candidates.py",
            )
            drafted.append({"family": family, "repo_id": repo_id, "warnings": warnings})
        except FetchError as error:
            print(f"  SKIPPED: {error}")
            skipped.append({"family": family, "repo_id": repo_id, "reason": str(error)})

    DRAFTS_DIR.mkdir(exist_ok=True)
    summary_lines = [
        "# Registry candidate scan summary",
        "",
        "Nothing under `registry/` was modified. Review each draft below, "
        "fill in any `REVIEW` markers, resolve any caveats, then move the "
        "entries into `registry/models.json` and the stub into "
        "`registry/SOURCES.md` by hand.",
        "",
        f"## Drafted ({len(drafted)})",
        "",
    ]
    for entry in drafted:
        summary_lines.append(f"- **{entry['family']}** (`{entry['repo_id']}`)")
        for warning in entry["warnings"]:
            summary_lines.append(f"  - CAVEAT: {warning}")
    if not drafted:
        summary_lines.append("- (none)")

    summary_lines += ["", f"## Skipped ({len(skipped)})", ""]
    for entry in skipped:
        summary_lines.append(f"- **{entry['family']}** (`{entry['repo_id']}`): {entry['reason']}")
    if not skipped:
        summary_lines.append("- (none)")

    summary_path = DRAFTS_DIR / "SUMMARY.md"
    with open(summary_path, "w", encoding="utf-8") as file:
        file.write("\n".join(summary_lines) + "\n")

    print(f"\n{len(drafted)} drafted, {len(skipped)} skipped. Summary at {summary_path}")


if __name__ == "__main__":
    main()
