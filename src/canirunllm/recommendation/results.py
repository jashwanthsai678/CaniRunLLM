from dataclasses import dataclass, field

from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.confidence import ConfidenceLevel
from canirunllm.performance.prediction import PerformancePrediction

from canirunllm.recommendation.profiles import WorkloadProfile
from canirunllm.recommendation.tier import RecommendationTier


@dataclass
class RecommendationScore:
    fit: float
    memory_efficiency: float
    context: float
    runtime: float
    confidence: float
    overall: float


@dataclass
class RecommendationResult:
    model: ModelSpec
    compatibility: CompatibilityResult
    memory_strategy: str
    tier: RecommendationTier
    confidence: ConfidenceLevel
    score: RecommendationScore
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rank: int | None = None
    performance: PerformancePrediction | None = None


@dataclass
class RecommendationEngineResult:
    workload: WorkloadProfile
    recommendations: list[RecommendationResult]
    excluded: list[RecommendationResult]
