from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.confidence import ConfidenceLevel

from canirunllm.recommendation.engine import RankedModel
from canirunllm.recommendation.tier import RecommendationTier
from canirunllm.performance.prediction import predict_performance

from canirunllm.api.presentation import (
    friendly_verdict,
    build_reasons,
    build_run_commands,
    pick_best_for_you,
    pick_alternative,
)


def make_model(name="Test-Model", runtime="llama.cpp", context_length=8192):
    return ModelSpec(
        name=name,
        family=name,
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=context_length,
        runtime=runtime,
    )


def make_compatibility(
    overall_verdict,
    memory_strategy,
    runtime_verdict=RuntimeVerdict.SUPPORTED,
    required_gb=5,
    vram_gb=10,
    ram_gb=20,
):
    return CompatibilityResult(
        overall_verdict=overall_verdict,
        confidence=ConfidenceLevel.HIGH,
        memory_verdict=MemoryVerdict.FIT,
        runtime_verdict=runtime_verdict,
        required_memory_bytes=int(required_gb * 1024**3),
        available_vram_bytes=int(vram_gb * 1024**3),
        available_ram_bytes=int(ram_gb * 1024**3),
        memory_strategy=memory_strategy,
        reason="test",
    )


def test_friendly_verdict_covers_every_overall_verdict():

    for verdict in OverallVerdict:
        label, icon = friendly_verdict(verdict)
        assert label
        assert icon in {"check", "warn", "unknown", "cross"}


def test_single_gpu_reasons_are_all_positive():

    model = make_model()
    compatibility = make_compatibility(OverallVerdict.CAN_RUN, "SINGLE_GPU")

    reasons = build_reasons(model, compatibility)

    assert all(r.ok for r in reasons)
    assert any("GPU memory" in r.text for r in reasons)
    assert any("supported" in r.text for r in reasons)


def test_cpu_offload_reasons_include_a_tradeoff_warning():

    model = make_model()
    compatibility = make_compatibility(
        OverallVerdict.CAN_RUN_WITH_OFFLOAD, "CPU_OFFLOAD"
    )

    reasons = build_reasons(model, compatibility)

    assert any(r.ok for r in reasons)
    assert any(not r.ok for r in reasons)
    assert any("slower" in r.text for r in reasons)


def test_no_fit_reasons_mention_actual_numbers():

    model = make_model()
    compatibility = make_compatibility(
        OverallVerdict.CANNOT_RUN,
        "NONE",
        required_gb=40,
        vram_gb=6,
        ram_gb=8,
    )

    reasons = build_reasons(model, compatibility)

    assert not reasons[0].ok
    assert "40.0 GB" in reasons[0].text
    assert "6.0 GB" in reasons[0].text
    assert "8.0 GB" in reasons[0].text


def test_unknown_runtime_reason_is_honest_about_uncertainty():

    model = make_model(runtime=None)
    compatibility = make_compatibility(
        OverallVerdict.NEEDS_VALIDATION,
        "SINGLE_GPU",
        runtime_verdict=RuntimeVerdict.UNKNOWN,
    )

    reasons = build_reasons(model, compatibility)

    assert any(not r.ok and "can't be fully confirmed" in r.text for r in reasons)


def test_run_commands_include_llama_cpp_and_ollama():

    model = make_model(runtime="llama.cpp")

    commands = build_run_commands(model)

    runtimes = [c.runtime for c in commands]
    assert "llama.cpp" in runtimes
    assert "Ollama" in runtimes

    llama_cpp_info = next(c for c in commands if c.runtime == "llama.cpp")
    assert model.name in llama_cpp_info.command
    assert "does not download or store model files" in llama_cpp_info.note


def test_run_commands_ollama_falls_back_honestly_for_unverified_model():

    model = make_model(name="Not-A-Real-Registry-Model", runtime="llama.cpp")

    commands = build_run_commands(model)

    ollama_info = next(c for c in commands if c.runtime == "Ollama")

    assert "ollama run" not in ollama_info.command
    assert "search" in ollama_info.command
    assert "haven't verified" in ollama_info.note


def test_run_commands_ollama_uses_verified_tag_when_known():

    model = make_model(name="Qwen3-8B-Q4_K_M", runtime="llama.cpp")

    commands = build_run_commands(model)

    ollama_info = next(c for c in commands if c.runtime == "Ollama")

    assert ollama_info.command == "ollama run qwen3:8b-q4_K_M"


def test_run_commands_empty_for_unknown_runtime():

    model = make_model(runtime="some-custom-runtime")

    assert build_run_commands(model) == []


def test_run_commands_empty_when_runtime_missing():

    model = make_model(runtime=None)

    assert build_run_commands(model) == []


def test_pick_best_for_you_returns_top_favorable_entry():

    model = make_model("Best")
    compatibility = make_compatibility(OverallVerdict.CAN_RUN, "SINGLE_GPU")

    ranked = [
        RankedModel(
            model=model,
            compatibility=compatibility,
            tier=RecommendationTier.BEST_MATCH,
            stars=5,
            performance=predict_performance(model, compatibility),
        )
    ]

    result = pick_best_for_you(ranked)

    assert result is not None
    assert result.model.name == "Best"


def test_pick_best_for_you_returns_none_when_top_is_unfavorable():

    model = make_model("Bad")
    compatibility = make_compatibility(OverallVerdict.CANNOT_RUN, "NONE")

    ranked = [
        RankedModel(
            model=model,
            compatibility=compatibility,
            tier=RecommendationTier.CANNOT_RUN,
            stars=1,
            performance=predict_performance(model, compatibility),
        )
    ]

    assert pick_best_for_you(ranked) is None


def test_pick_best_for_you_empty_list_returns_none():

    assert pick_best_for_you([]) is None


def test_pick_alternative_skips_the_excluded_model():

    failing = make_model("Failing")
    good = make_model("Good")

    failing_compat = make_compatibility(OverallVerdict.CANNOT_RUN, "NONE")
    good_compat = make_compatibility(OverallVerdict.CAN_RUN, "SINGLE_GPU")

    ranked = [
        RankedModel(model=failing, compatibility=failing_compat,
                    tier=RecommendationTier.CANNOT_RUN, stars=1,
                    performance=predict_performance(failing, failing_compat)),
        RankedModel(model=good, compatibility=good_compat,
                    tier=RecommendationTier.BEST_MATCH, stars=5,
                    performance=predict_performance(good, good_compat)),
    ]

    alternative = pick_alternative(ranked, exclude_model_name="Failing")

    assert alternative is not None
    assert alternative.name == "Good"


def test_pick_alternative_returns_none_if_nothing_favorable():

    only_model = make_model("OnlyOne")
    compatibility = make_compatibility(OverallVerdict.CANNOT_RUN, "NONE")

    ranked = [
        RankedModel(model=only_model, compatibility=compatibility,
                    tier=RecommendationTier.CANNOT_RUN, stars=1,
                    performance=predict_performance(only_model, compatibility)),
    ]

    assert pick_alternative(ranked, exclude_model_name="OnlyOne") is None
