from dataclasses import dataclass

from canirunllm.models.model import ModelSpec
from canirunllm.models.results import ModelCheckResult
from canirunllm.models.hardware import HardwareProfile

from canirunllm.compatibility.engine import (
    CompatibilityResult,
    check_compatibility,
)
from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.confidence import ConfidenceLevel
from canirunllm.compatibility.config import MemoryConfig

from canirunllm.recommendation.tier import (
    RecommendationTier,
    TIER_STARS,
    TIER_ORDER,
)

from canirunllm.recommendation.profiles import (
    WorkloadRequirements,
    WORKLOAD_REQUIREMENTS,
    resolve_workload,
)

from canirunllm.recommendation.scoring import (
    score_fit,
    score_memory_efficiency,
    score_context,
    score_runtime,
    score_confidence,
    combine_scores,
)

from canirunllm.recommendation.results import (
    RecommendationScore,
    RecommendationResult,
    RecommendationEngineResult,
)

from canirunllm.performance.prediction import predict_performance


@dataclass
class RankedModel:
    model: ModelSpec
    compatibility: CompatibilityResult
    tier: RecommendationTier
    stars: int


def _vram_coverage_ratio(
    compatibility: CompatibilityResult,
) -> float:
    """Fraction of the estimated requirement that fits in the
    largest single GPU's usable VRAM. >= 1.0 means it fits
    entirely; values near 0 mean almost everything must be
    offloaded elsewhere."""

    if compatibility.required_memory_bytes <= 0:
        return 1.0

    return (
        compatibility.available_vram_bytes
        / compatibility.required_memory_bytes
    )


def determine_recommendation_tier(
    compatibility: CompatibilityResult,
) -> RecommendationTier:

    if compatibility.overall_verdict == OverallVerdict.CANNOT_RUN:

        if compatibility.memory_verdict == MemoryVerdict.NO_FIT:
            # Memory is fundamentally insufficient no matter the runtime.
            return RecommendationTier.CANNOT_RUN

        # Memory would fit, but the runtime itself is the blocker.
        # A different runtime could plausibly still run this model.
        return RecommendationTier.NOT_RECOMMENDED

    if compatibility.overall_verdict == OverallVerdict.NEEDS_VALIDATION:
        return RecommendationTier.POSSIBLE

    if compatibility.overall_verdict == OverallVerdict.CAN_RUN_WITH_OFFLOAD:

        if compatibility.memory_strategy == "MULTI_GPU":
            # Distributed across GPUs the user already owns.
            return RecommendationTier.GOOD

        # CPU_OFFLOAD: the less of the model that fits in VRAM,
        # the more it leans on much slower system RAM.
        if _vram_coverage_ratio(compatibility) >= 0.5:
            return RecommendationTier.GOOD

        return RecommendationTier.NOT_RECOMMENDED

    if compatibility.overall_verdict == OverallVerdict.CAN_RUN:

        if _vram_coverage_ratio(compatibility) >= 1.3:
            return RecommendationTier.BEST_MATCH

        return RecommendationTier.GOOD

    return RecommendationTier.POSSIBLE


def rank_models(
    results: list[ModelCheckResult],
) -> list[RankedModel]:

    ranked = []

    for item in results:

        tier = determine_recommendation_tier(item.compatibility)

        ranked.append(
            RankedModel(
                model=item.model,
                compatibility=item.compatibility,
                tier=tier,
                stars=TIER_STARS[tier],
            )
        )

    ranked.sort(
        key=lambda entry: (
            TIER_ORDER[entry.tier],
            -_vram_coverage_ratio(entry.compatibility),
        )
    )

    return ranked


def _build_reasons_and_warnings(
    model: ModelSpec,
    compatibility: CompatibilityResult,
    requirements: WorkloadRequirements,
) -> tuple[list[str], list[str]]:

    reasons: list[str] = []
    warnings: list[str] = []

    if compatibility.overall_verdict == OverallVerdict.CANNOT_RUN:
        reasons.append(compatibility.reason)
        return reasons, warnings

    strategy_reason = {
        "SINGLE_GPU": "Fits within a single GPU's usable VRAM.",
        "MULTI_GPU": "Fits by distributing weights across multiple GPUs.",
        "CPU_OFFLOAD": "Fits using CPU/RAM offloading.",
    }.get(compatibility.memory_strategy)

    if strategy_reason is not None:
        reasons.append(strategy_reason)

    if compatibility.runtime_verdict == RuntimeVerdict.SUPPORTED:
        reasons.append(
            f"Runtime '{model.runtime}' is supported."
        )

    workload = requirements.profile.value

    if model.context_length >= requirements.minimum_recommended_context:
        reasons.append(
            f"Context length {model.context_length:,} meets the "
            f"{requirements.minimum_recommended_context:,} typically "
            f"recommended for {workload}."
        )
    else:
        warnings.append(
            f"Context length {model.context_length:,} is below the "
            f"{requirements.minimum_recommended_context:,} typically "
            f"recommended for {workload}."
        )

    if compatibility.memory_strategy == "CPU_OFFLOAD":
        warnings.append(
            "CPU/RAM offloading typically reduces performance "
            "significantly compared to running entirely on GPU."
        )

    if compatibility.memory_strategy == "MULTI_GPU":
        warnings.append(
            "Requires the runtime to correctly distribute the "
            "model across multiple GPUs."
        )

    if compatibility.runtime_verdict == RuntimeVerdict.UNKNOWN:
        warnings.append(
            "Runtime is unspecified; compatibility could not be "
            "validated against a known runtime."
        )

    if compatibility.runtime_verdict == RuntimeVerdict.UNSUPPORTED:
        warnings.append(
            f"Runtime '{model.runtime}' is not in the list of "
            "known-supported runtimes."
        )

    if compatibility.confidence == ConfidenceLevel.LOW:
        warnings.append(
            "Low confidence: insufficient information to strongly "
            "validate this configuration."
        )

    return reasons, warnings


class RecommendationEngine:
    """Ranks candidate models for a specific workload.

    Ranking itself is limited to what can be honestly derived from
    the compatibility engine today: memory fit, memory headroom,
    context adequacy, runtime support, and confidence. Each result
    also carries a coarse, clearly-labeled performance *prediction*
    (see canirunllm.performance) — it does not affect ranking, since
    it is a low-confidence heuristic rather than measured data.

    Quality and cost signals are not produced yet: there is no
    benchmark or pricing data in the system to honestly derive them
    from.
    """

    def recommend(
        self,
        hardware: HardwareProfile,
        models: list[ModelSpec],
        task: str = "general_chat",
        config: MemoryConfig | None = None,
    ) -> RecommendationEngineResult:

        workload = resolve_workload(task)
        requirements = WORKLOAD_REQUIREMENTS[workload]

        included: list[RecommendationResult] = []
        excluded: list[RecommendationResult] = []

        for model in models:

            compatibility = check_compatibility(
                hardware,
                model,
                config,
            )

            fit = score_fit(compatibility)
            memory_efficiency = score_memory_efficiency(compatibility)
            context = score_context(model, requirements)
            runtime = score_runtime(compatibility)
            confidence = score_confidence(compatibility)

            overall = combine_scores(
                fit,
                memory_efficiency,
                context,
                runtime,
                confidence,
                requirements,
            )

            reasons, warnings = _build_reasons_and_warnings(
                model,
                compatibility,
                requirements,
            )

            result = RecommendationResult(
                model=model,
                compatibility=compatibility,
                memory_strategy=compatibility.memory_strategy,
                tier=determine_recommendation_tier(compatibility),
                confidence=compatibility.confidence,
                score=RecommendationScore(
                    fit=fit,
                    memory_efficiency=memory_efficiency,
                    context=context,
                    runtime=runtime,
                    confidence=confidence,
                    overall=overall,
                ),
                reasons=reasons,
                warnings=warnings,
                performance=predict_performance(model, compatibility),
            )

            if compatibility.overall_verdict == OverallVerdict.CANNOT_RUN:
                excluded.append(result)
            else:
                included.append(result)

        included.sort(
            key=lambda entry: (
                -entry.score.overall,
                entry.model.name,
            )
        )

        for index, result in enumerate(included, start=1):
            result.rank = index

        return RecommendationEngineResult(
            workload=workload,
            recommendations=included,
            excluded=excluded,
        )
