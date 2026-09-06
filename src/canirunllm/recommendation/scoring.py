from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.confidence import ConfidenceLevel

from canirunllm.models.model import ModelSpec

from canirunllm.recommendation.profiles import WorkloadRequirements


FIT_SCORE_BY_VERDICT = {
    OverallVerdict.CAN_RUN: 1.0,
    OverallVerdict.CAN_RUN_WITH_OFFLOAD: 0.6,
    OverallVerdict.NEEDS_VALIDATION: 0.3,
    OverallVerdict.CANNOT_RUN: 0.0,
}

RUNTIME_SCORE_BY_VERDICT = {
    RuntimeVerdict.SUPPORTED: 1.0,
    RuntimeVerdict.UNKNOWN: 0.4,
    RuntimeVerdict.UNSUPPORTED: 0.0,
}

CONFIDENCE_SCORE_BY_LEVEL = {
    ConfidenceLevel.HIGH: 1.0,
    ConfidenceLevel.MEDIUM: 0.6,
    ConfidenceLevel.LOW: 0.3,
}


def score_fit(compatibility: CompatibilityResult) -> float:
    return FIT_SCORE_BY_VERDICT[compatibility.overall_verdict]


def score_memory_efficiency(compatibility: CompatibilityResult) -> float:
    """How comfortably the estimated requirement sits inside the
    largest single GPU's usable VRAM. 1.5x headroom or more scores
    a full 1.0; 0 headroom (or reliance on offload) trends to 0."""

    if compatibility.required_memory_bytes <= 0:
        return 1.0

    ratio = (
        compatibility.available_vram_bytes
        / compatibility.required_memory_bytes
    )

    return max(0.0, min(1.0, ratio / 1.5))


def score_context(
    model: ModelSpec,
    requirements: WorkloadRequirements,
) -> float:
    """How well the model's supported context length covers what
    the workload typically needs. Below the recommended floor,
    the score degrades linearly rather than being excluded outright."""

    if requirements.minimum_recommended_context <= 0:
        return 1.0

    ratio = model.context_length / requirements.minimum_recommended_context

    return max(0.0, min(1.0, ratio))


def score_runtime(compatibility: CompatibilityResult) -> float:
    return RUNTIME_SCORE_BY_VERDICT[compatibility.runtime_verdict]


def score_confidence(compatibility: CompatibilityResult) -> float:
    return CONFIDENCE_SCORE_BY_LEVEL[compatibility.confidence]


def combine_scores(
    fit: float,
    memory_efficiency: float,
    context: float,
    runtime: float,
    confidence: float,
    requirements: WorkloadRequirements,
) -> float:

    weights = requirements.weights

    return (
        weights["fit"] * fit
        + weights["memory_efficiency"] * memory_efficiency
        + weights["context"] * context
        + weights["runtime"] * runtime
        + weights["confidence"] * confidence
    )
