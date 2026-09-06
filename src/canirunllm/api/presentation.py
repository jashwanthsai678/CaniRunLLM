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


# Command templates for runtimes this tool actually knows about. These
# are illustrative examples, not verified working commands — this tool
# does not download, store, or locate model files on disk.
_RUNTIME_COMMAND_TEMPLATES: dict[str, tuple[str, str]] = {
    "llama.cpp": (
        "llama-cli -m /path/to/{filename} -c {context_length}",
        "Point this at the GGUF file you've downloaded for this "
        "model - this tool does not download or store model files.",
    ),
}


def build_run_command(model: ModelSpec) -> RunCommandInfo | None:

    if model.runtime is None:
        return None

    template = _RUNTIME_COMMAND_TEMPLATES.get(model.runtime.lower())

    if template is None:
        return None

    command_template, note = template

    command = command_template.format(
        filename=f"{model.name}.gguf",
        context_length=model.context_length,
    )

    return RunCommandInfo(
        runtime=model.runtime,
        command=command,
        note=note,
    )


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
