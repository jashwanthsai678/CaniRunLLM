from dataclasses import dataclass, field
from enum import Enum

from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.confidence import ConfidenceLevel


class PredictionSource(str, Enum):
    MODELLED_ESTIMATE = "MODELLED_ESTIMATE"


@dataclass(frozen=True)
class PerformanceRange:
    low: float
    high: float
    unit: str

    def __str__(self) -> str:
        return f"{self.low:.0f}-{self.high:.0f} {self.unit}"


@dataclass
class PerformancePrediction:
    generation_speed: PerformanceRange | None
    confidence: ConfidenceLevel
    source: PredictionSource
    explanation: list[str] = field(default_factory=list)


# Coarse parameter-count buckets for a plausible *range* of generation
# speed on a GPU that fits the model on a single device. These are not
# derived from any specific hardware's memory bandwidth or compute
# throughput (that data does not exist in HardwareProfile yet) — they
# only reflect the rough inverse relationship between parameter count
# and generation speed observed broadly across consumer GPUs.
_PARAMETER_BUCKETS: list[tuple[float, tuple[float, float]]] = [
    (4_000_000_000, (40.0, 80.0)),
    (8_000_000_000, (25.0, 50.0)),
    (16_000_000_000, (15.0, 30.0)),
    (32_000_000_000, (8.0, 18.0)),
    (float("inf"), (3.0, 10.0)),
]

# How much a memory strategy other than a clean single-GPU fit is
# expected to cost in generation speed. Multi-GPU pays a communication
# overhead; CPU/RAM offload pays a much larger memory-bandwidth penalty.
_STRATEGY_MULTIPLIERS: dict[str, tuple[float, float]] = {
    "SINGLE_GPU": (1.0, 1.0),
    "MULTI_GPU": (0.5, 0.8),
    "CPU_OFFLOAD": (0.1, 0.25),
}


def _base_range_for_parameters(parameters: int) -> tuple[float, float]:

    for threshold, bucket in _PARAMETER_BUCKETS:
        if parameters <= threshold:
            return bucket

    return _PARAMETER_BUCKETS[-1][1]


def predict_performance(
    model: ModelSpec,
    compatibility: CompatibilityResult,
) -> PerformancePrediction:
    """Rough, clearly-labeled estimate of generation speed.

    This is a coarse heuristic, not a physics-based model — it has no
    access to GPU memory bandwidth or compute throughput. Confidence
    is therefore always LOW until real benchmark data (a later phase)
    can calibrate or replace it.
    """

    if compatibility.overall_verdict == OverallVerdict.CANNOT_RUN:
        return PerformancePrediction(
            generation_speed=None,
            confidence=ConfidenceLevel.LOW,
            source=PredictionSource.MODELLED_ESTIMATE,
            explanation=[
                "No performance prediction: this configuration is not "
                "expected to run on this hardware/runtime.",
            ],
        )

    low, high = _base_range_for_parameters(model.parameters)

    multiplier_low, multiplier_high = _STRATEGY_MULTIPLIERS.get(
        compatibility.memory_strategy,
        (1.0, 1.0),
    )

    return PerformancePrediction(
        generation_speed=PerformanceRange(
            low=low * multiplier_low,
            high=high * multiplier_high,
            unit="tok/s",
        ),
        confidence=ConfidenceLevel.LOW,
        source=PredictionSource.MODELLED_ESTIMATE,
        explanation=[
            f"Based on a parameter-count bucket for "
            f"{model.parameters:,} parameters.",
            f"Adjusted for memory strategy "
            f"'{compatibility.memory_strategy}'.",
            "Coarse heuristic only — no GPU compute-throughput or "
            "memory-bandwidth data is available yet. Confidence will "
            "improve once local benchmark data exists.",
        ],
    )
