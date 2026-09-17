"""Scan watched Hugging Face orgs for models not yet in the registry.

Read-only: prints/writes a JSON list of candidates, each shaped like
    {"repo_id": "Qwen/Qwen3-4B-Instruct-2507", "family": "Qwen3-4B-Instruct-2507",
     "gguf_repo": "bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF" or null}

Nothing here fetches config.json or writes drafts — that's
draft_all_candidates.py, which consumes this script's output.

Usage:
    python scripts/discover_new_models.py --since-days 14 --output candidates.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from _hf_common import HF_API, http_get_json, load_existing_families, search_gguf_candidates

# Orgs whose new releases are worth checking. Extend this list as needed.
WATCHED_ORGS = [
    "Qwen",
    "meta-llama",
    "mistralai",
    "google",
    "deepseek-ai",
    "unsloth",
    "microsoft",
    "ibm-granite",
    "01-ai",
    "stabilityai",
]


def list_recent_models(org: str, since: datetime, limit: int = 30) -> list[dict]:
    url = f"{HF_API}/models?author={org}&sort=lastModified&direction=-1&limit={limit}"
    try:
        results = http_get_json(url)
    except Exception as error:  # noqa: BLE001 - best-effort scan, one org failing shouldn't stop the rest
        print(f"  (failed to list models for {org}: {error})", file=sys.stderr)
        return []

    recent = []
    for item in results:
        repo_id = item.get("id", "")
        if "gguf" in repo_id.lower() or "-awq" in repo_id.lower() or "-gptq" in repo_id.lower():
            continue  # we want base/instruct repos, not pre-quantized ones
        pipeline_tag = item.get("pipeline_tag")
        if pipeline_tag not in (None, "text-generation"):
            continue
        last_modified = item.get("lastModified")
        if not last_modified:
            continue
        modified_at = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
        if modified_at < since:
            continue
        recent.append(item)
    return recent


def already_known(family: str, existing_families: set[str]) -> bool:
    normalized = family.lower()
    return any(normalized == existing.lower() for existing in existing_families)


def guess_gguf_repo(family: str) -> str | None:
    candidates = search_gguf_candidates(f"{family} GGUF", limit=5)
    return candidates[0] if candidates else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since-days", type=int, default=14, help="Look back this many days (default: 14)")
    parser.add_argument("--orgs", nargs="+", default=WATCHED_ORGS, help="HF orgs/users to scan")
    parser.add_argument("--output", help="Write JSON candidate list here (default: print to stdout)")
    args = parser.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.since_days)
    existing_families = load_existing_families()

    candidates = []
    for org in args.orgs:
        print(f"Scanning {org} ...", file=sys.stderr)
        for item in list_recent_models(org, since):
            repo_id = item["id"]
            family = repo_id.split("/")[-1]
            if already_known(family, existing_families):
                continue
            print(f"  candidate: {repo_id}", file=sys.stderr)
            gguf_repo = guess_gguf_repo(family)
            candidates.append({"repo_id": repo_id, "family": family, "gguf_repo": gguf_repo})

    output_json = json.dumps(candidates, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(output_json + "\n")
        print(f"\n{len(candidates)} candidate(s) written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
