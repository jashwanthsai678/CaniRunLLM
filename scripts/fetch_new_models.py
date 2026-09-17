"""Draft a new model registry entry from Hugging Face metadata.

This does NOT write to ``registry/models.json`` or ``registry/SOURCES.md``
directly. The registry is hand-curated on purpose (see SOURCES.md) — some
architectures (MoE, MLA, sliding-window attention) aren't modeled by this
project's KV-cache math and need a human judgment call before being added.

Instead, this script fetches ``config.json`` for a base model plus GGUF file
sizes for a quantized repo, flags anything that looks unsupported, and writes
a draft entry + citation stub under ``scripts/drafts/`` for manual review.

Usage:
    python scripts/fetch_new_models.py Qwen/Qwen3-4B-Instruct-2507 \\
        --gguf-repo Qwen/Qwen3-4B-Instruct-2507-GGUF \\
        --quants Q4_K_M Q8_0

If --gguf-repo is omitted, the script searches the HF Hub for a likely GGUF
repo and lists candidates instead of guessing.

For scanning many models at once, see discover_new_models.py and
draft_all_candidates.py.
"""

import argparse
import sys

from _hf_common import (
    FetchError,
    draft_candidate,
    load_existing_families,
    search_gguf_candidates,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo_id", help="Base model repo, e.g. Qwen/Qwen3-4B-Instruct-2507")
    parser.add_argument("--family", help="Family name to use in the registry (default: repo_id's last segment)")
    parser.add_argument("--architecture", help="Architecture label (default: config.json's model_type)")
    parser.add_argument("--gguf-repo", help="GGUF repo to pull quant file sizes from")
    parser.add_argument("--parameters", type=int, help="Total parameter count, if known")
    parser.add_argument("--quants", nargs="+", default=["Q4_K_M", "Q8_0"], help="Quantizations to look for")
    parser.add_argument("--force", action="store_true", help="Proceed even if the family already exists in models.json")
    args = parser.parse_args()

    family = args.family or args.repo_id.split("/")[-1]

    existing = load_existing_families()
    if family in existing and not args.force:
        raise SystemExit(f"'{family}' already exists in models.json. Use --force to draft anyway.")

    gguf_repo = args.gguf_repo
    if not gguf_repo:
        print(f"No --gguf-repo given, searching for candidates matching '{family}' ...")
        candidates = search_gguf_candidates(f"{family} GGUF")
        if candidates:
            print("  Candidates found (pick one and re-run with --gguf-repo):")
            for candidate in candidates:
                print(f"    {candidate}")
        else:
            print("  No candidates found.")

    print(f"Fetching config.json for {args.repo_id} ...")
    try:
        entries, _, warnings = draft_candidate(
            repo_id=args.repo_id,
            family=family,
            gguf_repo=gguf_repo,
            quants=args.quants,
            caller="scripts/fetch_new_models.py",
            architecture=args.architecture,
            parameters=args.parameters,
        )
    except FetchError as error:
        raise SystemExit(str(error))

    for warning in warnings:
        print(f"  WARNING: {warning}", file=sys.stderr)

    print(f"Draft registry entries written to scripts/drafts/{family}.json")
    print(f"Draft SOURCES.md stub written to scripts/drafts/{family}.SOURCES.md")
    print(
        "\nNothing in registry/ was modified. Review the draft, fill in any "
        "REVIEW markers, then move the entries into models.json and the stub "
        "into SOURCES.md by hand."
    )


if __name__ == "__main__":
    main()
