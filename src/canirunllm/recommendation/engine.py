from dataclasses import dataclass

from canirunllm.models.model import ModelSpec
from canirunllm.models.results import ModelCheckResult
from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.decision import OverallVerdict

from canirunllm.recommendation.tier import (
    RecommendationTier,
    TIER_STARS,
    TIER_ORDER,
)


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
