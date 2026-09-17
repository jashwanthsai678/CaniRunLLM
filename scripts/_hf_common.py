"""Shared Hugging Face fetch/draft helpers used by fetch_new_models.py,
discover_new_models.py, and draft_all_candidates.py.

Nothing in this module writes to registry/models.json or registry/SOURCES.md
directly — see fetch_new_models.py's module docstring for why.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HF_BASE = "https://huggingface.co"
HF_API = "https://huggingface.co/api"
DRAFTS_DIR = Path(__file__).parent / "drafts"
REGISTRY_PATH = Path(__file__).parent.parent / "src" / "canirunllm" / "registry" / "models.json"

# config.json keys that signal an architecture this project's memory/KV-cache
# formulas don't model (see registry/SOURCES.md for prior exclusions).
MOE_KEYS = ("num_experts", "num_local_experts", "num_experts_per_tok", "moe_intermediate_size")
MLA_KEYS = ("kv_lora_rank", "q_lora_rank", "qk_rope_head_dim", "qk_nope_head_dim")


class FetchError(Exception):
    """Raised for per-candidate failures that callers may want to skip past."""


def http_get_json(url: str) -> dict | list:
    request = urllib.request.Request(url, headers={"User-Agent": "canirunllm-registry-fetcher"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def fetch_config(repo_id: str) -> dict:
    url = f"{HF_BASE}/{repo_id}/raw/main/config.json"
    try:
        return http_get_json(url)
    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise FetchError(
                f"{repo_id} is gated (401). Needs a public mirror, "
                f"e.g. an unsloth/ or bartowski/ re-upload, as the repo_id."
            )
        raise FetchError(f"Failed to fetch config.json for {repo_id}: HTTP {error.code}")


def architecture_warnings(config: dict) -> list[str]:
    warnings = []
    if any(config.get(key) for key in MOE_KEYS):
        warnings.append(
            "MoE architecture detected (found one of "
            f"{MOE_KEYS}) — this project's formulas assume dense models. "
            "Verify before adding."
        )
    if any(config.get(key) for key in MLA_KEYS):
        warnings.append(
            "MLA attention detected (found one of "
            f"{MLA_KEYS}) — KV-cache size formula assumes standard MHA/GQA. "
            "Verify before adding."
        )
    if config.get("sliding_window"):
        warnings.append(
            f"sliding_window={config.get('sliding_window')} present — "
            "context/KV-cache math does not model sliding-window attention "
            "and will overestimate memory use (same caveat as Gemma-2)."
        )
    return warnings


def search_gguf_candidates(query: str, limit: int = 8) -> list[str]:
    url = f"{HF_API}/models?search={urllib.parse.quote(query)}&filter=gguf&limit={limit}"
    try:
        results = http_get_json(url)
    except urllib.error.HTTPError as error:
        print(f"  (GGUF search failed for '{query}': HTTP {error.code})", file=sys.stderr)
        return []
    return [item["id"] for item in results if "id" in item]


def fetch_file_tree(repo_id: str) -> list[dict]:
    url = f"{HF_API}/models/{repo_id}/tree/main"
    try:
        return http_get_json(url)
    except urllib.error.HTTPError as error:
        raise FetchError(f"Failed to list files for {repo_id}: HTTP {error.code}")


def match_quant_sizes(tree: list[dict], quants: list[str]) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for entry in tree:
        path = entry.get("path", "")
        if not path.lower().endswith(".gguf"):
            continue
        for quant in quants:
            if quant.lower() in path.lower() and quant not in sizes:
                size = entry.get("size")
                if size is not None:
                    sizes[quant] = size
    return sizes


def derive_head_dim(config: dict) -> int | None:
    if "head_dim" in config:
        return config["head_dim"]
    hidden_size = config.get("hidden_size")
    num_heads = config.get("num_attention_heads")
    if hidden_size and num_heads:
        return hidden_size // num_heads
    return None


def build_entry(
    family: str,
    architecture: str,
    quant: str,
    config: dict,
    file_size_bytes: int | None,
    parameters: int | str | None = None,
) -> dict:
    return {
        "name": f"{family}-{quant}",
        "family": family,
        "parameters": parameters or "REVIEW: not in config.json, check model card",
        "architecture": architecture,
        "quantization": quant,
        "context_length": config.get("max_position_embeddings", "REVIEW"),
        "runtime": "llama.cpp",
        "num_layers": config.get("num_hidden_layers"),
        "num_kv_heads": config.get("num_key_value_heads", config.get("num_attention_heads")),
        "head_dim": derive_head_dim(config),
        "kv_cache_dtype_bits": 16,
        "file_size_bytes": file_size_bytes,
    }


def build_sources_stub(
    family: str,
    base_repo: str,
    gguf_repo: str,
    config: dict,
    quant_sizes: dict[str, int],
    warnings: list[str],
    caller: str,
) -> str:
    lines = [f"## {family}", ""]
    lines.append(
        f"- `parameters`: REVIEW — not present in config.json, check the model "
        f"card for {base_repo} and fill in manually."
    )
    lines.append(
        f"- `context_length`, `num_layers`, `num_kv_heads`, `head_dim`: from "
        f"`config.json` at https://huggingface.co/{base_repo} "
        f"(num_hidden_layers={config.get('num_hidden_layers')}, "
        f"num_attention_heads={config.get('num_attention_heads')}, "
        f"num_key_value_heads={config.get('num_key_value_heads')}, "
        f"max_position_embeddings={config.get('max_position_embeddings')})."
    )
    if quant_sizes:
        sizes = ", ".join(f"{q} = {n / 1e9:.2f} GB" for q, n in quant_sizes.items())
        lines.append(
            f"- `file_size_bytes`: GGUF artifact sizes from "
            f"https://huggingface.co/{gguf_repo} ({sizes})."
        )
    else:
        lines.append(f"- `file_size_bytes`: REVIEW — no matching quant files found in {gguf_repo}.")
    for warning in warnings:
        lines.append(f"- CAVEAT: {warning}")
    lines.append(f"- Fetched {datetime.now(timezone.utc).date().isoformat()} by {caller}.")
    return "\n".join(lines) + "\n"


def load_existing_families() -> set[str]:
    if not REGISTRY_PATH.exists():
        return set()
    with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)
    return {entry["family"] for entry in data}


def write_draft(family: str, entries: list[dict], sources_stub: str) -> tuple[Path, Path]:
    DRAFTS_DIR.mkdir(exist_ok=True)
    entries_path = DRAFTS_DIR / f"{family}.json"
    with open(entries_path, "w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)
        file.write("\n")

    sources_path = DRAFTS_DIR / f"{family}.SOURCES.md"
    with open(sources_path, "w", encoding="utf-8") as file:
        file.write(sources_stub)

    return entries_path, sources_path


def draft_candidate(
    repo_id: str,
    family: str,
    gguf_repo: str | None,
    quants: list[str],
    caller: str,
    architecture: str | None = None,
    parameters: int | None = None,
) -> tuple[list[dict], str, list[str]]:
    """Fetch config + GGUF sizes for one candidate and write its draft files.

    Raises FetchError on failure (gated repo, HTTP error, etc.) so batch
    callers can catch it and continue to the next candidate.
    """
    config = fetch_config(repo_id)
    resolved_architecture = architecture or config.get("model_type", "REVIEW")
    warnings = architecture_warnings(config)

    quant_sizes: dict[str, int] = {}
    if gguf_repo:
        tree = fetch_file_tree(gguf_repo)
        quant_sizes = match_quant_sizes(tree, quants)
        missing = [q for q in quants if q not in quant_sizes]
        if missing:
            warnings.append(f"No GGUF file matched for quant(s): {', '.join(missing)} in {gguf_repo}.")

    entries = [
        build_entry(family, resolved_architecture, quant, config, quant_sizes.get(quant), parameters)
        for quant in quants
    ]
    sources_stub = build_sources_stub(
        family, repo_id, gguf_repo or "REVIEW", config, quant_sizes, warnings, caller
    )
    write_draft(family, entries, sources_stub)
    return entries, sources_stub, warnings
