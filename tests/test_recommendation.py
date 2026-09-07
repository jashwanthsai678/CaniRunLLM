from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.confidence import ConfidenceLevel

from canirunllm.models.model import ModelSpec
from canirunllm.models.results import ModelCheckResult

from canirunllm.recommendation.tier import RecommendationTier
from canirunllm.recommendation.engine import (
    determine_recommendation_tier,
    rank_models,
)


def make_result(
    overall_verdict,
    memory_verdict,
    memory_strategy,
    required_gb,
    available_vram_gb,
):
    return CompatibilityResult(
        overall_verdict=overall_verdict,
        confidence=ConfidenceLevel.HIGH,
        memory_verdict=memory_verdict,
        runtime_verdict=RuntimeVerdict.SUPPORTED,
        required_memory_bytes=int(required_gb * 1024**3),
        available_vram_bytes=int(available_vram_gb * 1024**3),
        available_ram_bytes=0,
        memory_strategy=memory_strategy,
        reason="test",
    )


def make_model(name="Test-Model"):
    return ModelSpec(
        name=name,
        family=name,
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
        runtime="llama.cpp",
    )


def test_can_run_with_generous_headroom_is_best_match():

    result = make_result(
        OverallVerdict.CAN_RUN,
        MemoryVerdict.FIT,
        "SINGLE_GPU",
        required_gb=5,
        available_vram_gb=10,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.BEST_MATCH


def test_can_run_with_tight_headroom_is_good():

    result = make_result(
        OverallVerdict.CAN_RUN,
        MemoryVerdict.FIT,
        "SINGLE_GPU",
        required_gb=5,
        available_vram_gb=5.5,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.GOOD


def test_multi_gpu_offload_is_good():

    result = make_result(
        OverallVerdict.CAN_RUN_WITH_OFFLOAD,
        MemoryVerdict.MULTI_GPU,
        "MULTI_GPU",
        required_gb=14,
        available_vram_gb=8,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.GOOD


def test_light_cpu_offload_is_good():

    result = make_result(
        OverallVerdict.CAN_RUN_WITH_OFFLOAD,
        MemoryVerdict.CPU_OFFLOAD,
        "CPU_OFFLOAD",
        required_gb=10,
        available_vram_gb=6,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.GOOD


def test_heavy_cpu_offload_is_not_recommended():

    result = make_result(
        OverallVerdict.CAN_RUN_WITH_OFFLOAD,
        MemoryVerdict.CPU_OFFLOAD,
        "CPU_OFFLOAD",
        required_gb=18,
        available_vram_gb=4,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.NOT_RECOMMENDED


def test_needs_validation_is_possible():

    result = make_result(
        OverallVerdict.NEEDS_VALIDATION,
        MemoryVerdict.FIT,
        "SINGLE_GPU",
        required_gb=5,
        available_vram_gb=10,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.POSSIBLE


def test_no_fit_is_cannot_run():

    result = make_result(
        OverallVerdict.CANNOT_RUN,
        MemoryVerdict.NO_FIT,
        "NONE",
        required_gb=40,
        available_vram_gb=8,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.CANNOT_RUN


def test_unsupported_runtime_despite_fit_is_not_recommended():

    result = make_result(
        OverallVerdict.CANNOT_RUN,
        MemoryVerdict.FIT,
        "SINGLE_GPU",
        required_gb=5,
        available_vram_gb=10,
    )

    assert determine_recommendation_tier(result) == RecommendationTier.NOT_RECOMMENDED


def test_rank_models_orders_best_tier_first():

    best = ModelCheckResult(
        model=make_model("Best"),
        compatibility=make_result(
            OverallVerdict.CAN_RUN,
            MemoryVerdict.FIT,
            "SINGLE_GPU",
            required_gb=5,
            available_vram_gb=10,
        ),
    )

    cannot_run = ModelCheckResult(
        model=make_model("Impossible"),
        compatibility=make_result(
            OverallVerdict.CANNOT_RUN,
            MemoryVerdict.NO_FIT,
            "NONE",
            required_gb=40,
            available_vram_gb=8,
        ),
    )

    possible = ModelCheckResult(
        model=make_model("Uncertain"),
        compatibility=make_result(
            OverallVerdict.NEEDS_VALIDATION,
            MemoryVerdict.FIT,
            "SINGLE_GPU",
            required_gb=5,
            available_vram_gb=10,
        ),
    )

    ranked = rank_models([cannot_run, possible, best])

    assert [entry.model.name for entry in ranked] == [
        "Best",
        "Uncertain",
        "Impossible",
    ]

    assert ranked[0].tier == RecommendationTier.BEST_MATCH
    assert ranked[0].stars == 5
    assert ranked[-1].tier == RecommendationTier.CANNOT_RUN
    assert ranked[-1].stars == 1


def test_rank_models_orders_by_headroom_within_same_tier():

    tight_fit = ModelCheckResult(
        model=make_model("Tight"),
        compatibility=make_result(
            OverallVerdict.CAN_RUN,
            MemoryVerdict.FIT,
            "SINGLE_GPU",
            required_gb=5,
            available_vram_gb=5.5,
        ),
    )

    generous_fit = ModelCheckResult(
        model=make_model("Generous"),
        compatibility=make_result(
            OverallVerdict.CAN_RUN,
            MemoryVerdict.FIT,
            "SINGLE_GPU",
            required_gb=5,
            available_vram_gb=6.0,
        ),
    )

    ranked = rank_models([tight_fit, generous_fit])

    assert ranked[0].tier == ranked[1].tier == RecommendationTier.GOOD

    assert [entry.model.name for entry in ranked] == [
        "Generous",
        "Tight",
    ]


def test_rank_models_attaches_a_performance_prediction():

    runnable = ModelCheckResult(
        model=make_model("Runnable"),
        compatibility=make_result(
            OverallVerdict.CAN_RUN,
            MemoryVerdict.FIT,
            "SINGLE_GPU",
            required_gb=5,
            available_vram_gb=10,
        ),
    )

    cannot_run = ModelCheckResult(
        model=make_model("Impossible"),
        compatibility=make_result(
            OverallVerdict.CANNOT_RUN,
            MemoryVerdict.NO_FIT,
            "NONE",
            required_gb=40,
            available_vram_gb=8,
        ),
    )

    ranked = rank_models([runnable, cannot_run])

    by_name = {entry.model.name: entry for entry in ranked}

    assert by_name["Runnable"].performance is not None
    assert by_name["Runnable"].performance.generation_speed is not None
    assert by_name["Runnable"].performance.generation_speed.low > 0

    assert by_name["Impossible"].performance is not None
    assert by_name["Impossible"].performance.generation_speed is None
