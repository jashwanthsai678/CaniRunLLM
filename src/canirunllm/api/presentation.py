"""Translates raw core objects into human-readable product language.

This is deliberately kept server-side (Python), not JavaScript: the
frontend must never re-derive compatibility meaning on its own. It
only renders the strings and flags this module produces.

Nothing here recalculates compatibility — it only interprets fields
that CompatibilityResult/RankedModel already computed.
"""

from dataclasses import dataclass

from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.models.model import ModelSpec
from canirunllm.recommendation.engine import RankedModel
from canirunllm.recommendation.tier import RecommendationTier


GB = 1024 ** 3

FAVORABLE_TIERS = {RecommendationTier.BEST_MATCH, RecommendationTier.GOOD}

# (friendly label, icon) — icon is a UI-neutral token, not an emoji,
# so the frontend controls the actual glyph/color.
VERDICT_LABELS: dict[OverallVerdict, tuple[str, str]] = {
    OverallVerdict.CAN_RUN: ("Runs comfortably", "check"),
    OverallVerdict.CAN_RUN_WITH_OFFLOAD: ("Runs, but slower", "warn"),
    OverallVerdict.NEEDS_VALIDATION: ("Needs more info to confirm", "unknown"),
    OverallVerdict.CANNOT_RUN: ("Not enough resources", "cross"),
}


@dataclass
class ReasonItem:
    ok: bool
    text: str


@dataclass
class RunCommandInfo:
    runtime: str
    command: str
    note: str


def friendly_verdict(overall_verdict: OverallVerdict) -> tuple[str, str]:
    return VERDICT_LABELS[overall_verdict]


def build_reasons(
    model: ModelSpec,
    compatibility: CompatibilityResult,
) -> list[ReasonItem]:
    """Human-readable checklist explaining a verdict — built only from
    fields the compatibility engine already computed, never invented."""

    reasons: list[ReasonItem] = []

    required_gb = compatibility.required_memory_bytes / GB
    vram_gb = compatibility.available_vram_bytes / GB
    ram_gb = compatibility.available_ram_bytes / GB

    strategy = compatibility.memory_strategy

    if strategy == "SINGLE_GPU":
        reasons.append(ReasonItem(
            True,
            f"Model weights fit within your available GPU memory "
            f"(~{vram_gb:.1f} GB free).",
        ))

    elif strategy == "MULTI_GPU":
        reasons.append(ReasonItem(
            True,
            "Model fits by splitting across your multiple GPUs.",
        ))
        reasons.append(ReasonItem(
            False,
            "Splitting a model across GPUs depends on the runtime "
            "supporting it correctly, and can be slower than a single "
            "GPU that fits the whole model.",
        ))

    elif strategy == "CPU_OFFLOAD":
        reasons.append(ReasonItem(
            True,
            f"Model doesn't fully fit in GPU memory, but fits when "
            f"combined with system RAM (~{ram_gb:.1f} GB available).",
        ))
        reasons.append(ReasonItem(
            False,
            "Running part of the model on CPU/RAM is typically much "
            "slower than running fully on GPU.",
        ))

    else:
        reasons.append(ReasonItem(
            False,
            f"This model needs about {required_gb:.1f} GB, but your "
            f"machine currently has ~{vram_gb:.1f} GB free GPU memory "
            f"and ~{ram_gb:.1f} GB free RAM.",
        ))

    if compatibility.runtime_verdict == RuntimeVerdict.SUPPORTED:
        reasons.append(ReasonItem(
            True,
            f"Runtime '{model.runtime}' is supported.",
        ))
    elif compatibility.runtime_verdict == RuntimeVerdict.UNKNOWN:
        reasons.append(ReasonItem(
            False,
            "This model doesn't specify a runtime, so compatibility "
            "can't be fully confirmed.",
        ))
    else:
        reasons.append(ReasonItem(
            False,
            f"Runtime '{model.runtime}' is not one of the runtimes "
            "this tool currently recognizes.",
        ))

    return reasons


# Verified Ollama tags for specific registry entries — checked directly
# against https://ollama.com/library/<family>/tags at the time these
# were added. Only models actually confirmed here get an exact "ollama
# run" command; everything else gets an honest "search the library"
# fallback instead of a guessed tag. Ollama tag naming does not
# reliably match this project's model names (different orgs use
# "-instruct-", "-it-", "-mini-instruct-", or nothing at all before
# the quantization suffix), so this cannot be derived mechanically.
_OLLAMA_TAGS: dict[str, str] = {
    "Qwen3-4B-Q4_K_M": "qwen3:4b-q4_K_M",
    "Qwen3-4B-Q8_0": "qwen3:4b-q8_0",
    "Qwen3-8B-Q4_K_M": "qwen3:8b-q4_K_M",
    "Qwen3-8B-Q8_0": "qwen3:8b-q8_0",
    "Qwen3-14B-Q4_K_M": "qwen3:14b-q4_K_M",
    "Qwen3-14B-Q8_0": "qwen3:14b-q8_0",
    "Qwen3-32B-Q4_K_M": "qwen3:32b-q4_K_M",
    "Qwen3-32B-Q8_0": "qwen3:32b-q8_0",
    "Qwen2.5-0.5B-Instruct-Q4_K_M": "qwen2.5:0.5b-instruct-q4_K_M",
    "Qwen2.5-0.5B-Instruct-Q8_0": "qwen2.5:0.5b-instruct-q8_0",
    "Qwen2.5-1.5B-Instruct-Q4_K_M": "qwen2.5:1.5b-instruct-q4_K_M",
    "Qwen2.5-1.5B-Instruct-Q8_0": "qwen2.5:1.5b-instruct-q8_0",
    "Qwen2.5-Coder-7B-Instruct-Q4_K_M": "qwen2.5-coder:7b-instruct-q4_K_M",
    "Qwen2.5-Coder-7B-Instruct-Q8_0": "qwen2.5-coder:7b-instruct-q8_0",
    "Llama-3.1-8B-Instruct-Q4_K_M": "llama3.1:8b-instruct-q4_K_M",
    "Llama-3.1-8B-Instruct-Q8_0": "llama3.1:8b-instruct-q8_0",
    "Llama-3.2-3B-Instruct-Q4_K_M": "llama3.2:3b-instruct-q4_K_M",
    "Llama-3.2-3B-Instruct-Q8_0": "llama3.2:3b-instruct-q8_0",
    "Llama-3.2-1B-Instruct-Q4_K_M": "llama3.2:1b-instruct-q4_K_M",
    "Llama-3.2-1B-Instruct-Q8_0": "llama3.2:1b-instruct-q8_0",
    "Mistral-7B-Instruct-v0.3-Q4_K_M": "mistral:7b-instruct-q4_K_M",
    "Mistral-7B-Instruct-v0.3-Q8_0": "mistral:7b-instruct-q8_0",
    "Gemma-2-9B-it-Q4_K_M": "gemma2:9b-instruct-q4_K_M",
    "Gemma-2-9B-it-Q8_0": "gemma2:9b-instruct-q8_0",
    "Gemma-3-4B-it-Q4_K_M": "gemma3:4b-it-q4_K_M",
    "Gemma-3-4B-it-Q8_0": "gemma3:4b-it-q8_0",
    "Phi-3.5-mini-instruct-Q4_K_M": "phi3.5:3.8b-mini-instruct-q4_K_M",
    "Phi-3.5-mini-instruct-Q8_0": "phi3.5:3.8b-mini-instruct-q8_0",
    "Phi-4-Q4_K_M": "phi4:14b-q4_K_M",
    "Phi-4-Q8_0": "phi4:14b-q8_0",
    "DeepSeek-R1-Distill-Llama-8B-Q4_K_M": "deepseek-r1:8b-llama-distill-q4_K_M",
    "DeepSeek-R1-Distill-Llama-8B-Q8_0": "deepseek-r1:8b-llama-distill-q8_0",
    "TinyLlama-1.1B-Chat-v1.0-Q4_K_M": "tinyllama:1.1b-chat-v1-q4_K_M",
    "TinyLlama-1.1B-Chat-v1.0-Q8_0": "tinyllama:1.1b-chat-v1-q8_0",
}


def _build_llama_cpp_command(model: ModelSpec) -> RunCommandInfo:
    return RunCommandInfo(
        runtime="llama.cpp",
        command=f"llama-cli -m /path/to/{model.name}.gguf -c {model.context_length}",
        note=(
            "Point this at the GGUF file you've downloaded for this "
            "model - this tool does not download or store model files."
        ),
    )


def _build_ollama_command(model: ModelSpec) -> RunCommandInfo:

    tag = _OLLAMA_TAGS.get(model.name)

    if tag is not None:
        return RunCommandInfo(
            runtime="Ollama",
            command=f"ollama run {tag}",
            note=(
                "Downloads automatically the first time you run this "
                "command, if you don't already have it. Requires "
                "Ollama installed (ollama.com)."
            ),
        )

    family_query = model.family.lower().replace(" ", "-")

    return RunCommandInfo(
        runtime="Ollama",
        command=f"# search: https://ollama.com/search?q={family_query}",
        note=(
            "We haven't verified an exact Ollama tag for this specific "
            "model/quantization - search the library above to check "
            "what's available and confirm the closest match yourself."
        ),
    )


def build_run_commands(model: ModelSpec) -> list[RunCommandInfo]:
    """One entry per runtime this tool can give real guidance for.

    Never silently omitted: even an unverified Ollama match still
    returns an honest "go check" entry rather than nothing at all,
    so the user always has a concrete next step.
    """

    commands: list[RunCommandInfo] = []

    if model.runtime is not None and model.runtime.lower() == "llama.cpp":
        commands.append(_build_llama_cpp_command(model))
        # Any llama.cpp-compatible GGUF model is also a candidate for
        # Ollama, which runs on the same underlying engine.
        commands.append(_build_ollama_command(model))

    return commands


def pick_best_for_you(ranked: list[RankedModel]) -> RankedModel | None:

    if not ranked:
        return None

    top = ranked[0]

    if top.tier in FAVORABLE_TIERS:
        return top

    return None


def pick_alternative(
    ranked: list[RankedModel],
    exclude_model_name: str,
) -> ModelSpec | None:
    """The best currently-recommendable model other than the one being
    looked at — shown when that model can't run, so the user always
    has a next step instead of a dead end."""

    for entry in ranked:

        if entry.model.name == exclude_model_name:
            continue

        if entry.tier in FAVORABLE_TIERS:
            return entry.model

    return None
