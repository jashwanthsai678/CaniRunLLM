from canirunllm.models.hardware import (
    HardwareProfile,
    CPUInfo,
    MemoryInfo,
    GPUInfo,
    OSInfo,
)
from canirunllm.models.model import ModelSpec

from canirunllm.recommendation.engine import RecommendationEngine
from canirunllm.recommendation.profiles import (
    WorkloadProfile,
    WORKLOAD_REQUIREMENTS,
    resolve_workload,
)
from canirunllm.recommendation.tier import RecommendationTier


def make_hardware(vram_gb, ram_gb):

    return HardwareProfile(
        cpu=CPUInfo(
            name="Test CPU",
            architecture="x86_64",
            physical_cores=8,
            logical_cores=16,
            frequency_mhz=3000,
        ),
        memory=MemoryInfo(
            total_bytes=int(ram_gb * 1024**3),
            available_bytes=int(ram_gb * 1024**3),
            used_bytes=0,
            usage_percent=0,
        ),
        os=OSInfo(
            system="Windows",
            release="11",
            version="Test",
            machine="x86_64",
        ),
        gpus=[
            GPUInfo(
                name="Test GPU",
                memory_total_bytes=int(vram_gb * 1024**3),
                memory_used_bytes=0,
                memory_free_bytes=int(vram_gb * 1024**3),
                utilization_percent=0,
            )
        ],
    )


def make_model(
    name,
    parameters=7_000_000_000,
    context_length=8192,
    runtime="llama.cpp",
):
    return ModelSpec(
        name=name,
        family=name,
        parameters=parameters,
        architecture="Test",
        quantization="Q4",
        context_length=context_length,
        runtime=runtime,
        num_layers=32,
        num_kv_heads=8,
        head_dim=128,
    )


def test_resolve_workload_accepts_known_tasks():

    assert resolve_workload("coding") == WorkloadProfile.CODING
    assert resolve_workload("RAG") == WorkloadProfile.RAG
    assert resolve_workload("general_chat") == WorkloadProfile.GENERAL_CHAT


def test_resolve_workload_rejects_unknown_task():

    try:
        resolve_workload("not-a-real-task")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_workload_weights_sum_to_one():

    for requirements in WORKLOAD_REQUIREMENTS.values():
        assert abs(sum(requirements.weights.values()) - 1.0) < 1e-9


def test_recommendations_are_deterministic():

    hardware = make_hardware(vram_gb=16, ram_gb=32)
    models = [make_model("Alpha"), make_model("Beta"), make_model("Gamma")]

    engine = RecommendationEngine()

    first = engine.recommend(hardware, models, task="coding")
    second = engine.recommend(hardware, models, task="coding")

    assert [r.model.name for r in first.recommendations] == [
        r.model.name for r in second.recommendations
    ]
    assert [r.score.overall for r in first.recommendations] == [
        r.score.overall for r in second.recommendations
    ]


def test_cannot_run_models_are_excluded_from_recommendations():

    hardware = make_hardware(vram_gb=1, ram_gb=1)

    huge_model = make_model("Huge", parameters=200_000_000_000)

    engine = RecommendationEngine()

    result = engine.recommend(hardware, [huge_model], task="general_chat")

    assert result.recommendations == []
    assert len(result.excluded) == 1
    assert result.excluded[0].model.name == "Huge"
    assert result.excluded[0].rank is None


def test_unsupported_runtime_model_is_not_top_ranked_against_supported_one():

    hardware = make_hardware(vram_gb=16, ram_gb=32)

    supported = make_model("Supported", runtime="llama.cpp")
    unsupported = make_model("Unsupported", runtime="some-custom-runtime")

    engine = RecommendationEngine()

    result = engine.recommend(
        hardware,
        [unsupported, supported],
        task="general_chat",
    )

    # Both fit in memory (overall != CANNOT_RUN would require runtime
    # UNSUPPORTED -> CANNOT_RUN per the compatibility engine), so the
    # unsupported-runtime model is excluded rather than ranked at all.
    names_in_recommendations = [
        r.model.name for r in result.recommendations
    ]
    assert "Unsupported" not in names_in_recommendations


def test_workload_changes_ranking_via_context():

    hardware = make_hardware(vram_gb=16, ram_gb=32)

    short_context = make_model("ShortContext", context_length=4096)
    long_context = make_model("LongContext", context_length=32768)

    engine = RecommendationEngine()

    rag_result = engine.recommend(
        hardware,
        [short_context, long_context],
        task="rag",
    )

    assert rag_result.recommendations[0].model.name == "LongContext"

    chat_result = engine.recommend(
        hardware,
        [short_context, long_context],
        task="general_chat",
    )

    chat_scores = {
        r.model.name: r.score.overall
        for r in chat_result.recommendations
    }
    rag_scores = {
        r.model.name: r.score.overall
        for r in rag_result.recommendations
    }

    # The context gap between the two models should matter more for RAG
    # (which weights context heavily) than for general chat.
    chat_gap = chat_scores["LongContext"] - chat_scores["ShortContext"]
    rag_gap = rag_scores["LongContext"] - rag_scores["ShortContext"]

    assert rag_gap > chat_gap


def test_memory_strategy_affects_ranking():

    single_gpu_hardware = make_hardware(vram_gb=16, ram_gb=32)
    offload_hardware = make_hardware(vram_gb=2, ram_gb=32)

    model = make_model("SameModel")

    engine = RecommendationEngine()

    single_gpu_result = engine.recommend(
        single_gpu_hardware,
        [model],
        task="general_chat",
    )
    offload_result = engine.recommend(
        offload_hardware,
        [model],
        task="general_chat",
    )

    single_gpu_entry = single_gpu_result.recommendations[0]
    offload_entry = offload_result.recommendations[0]

    assert single_gpu_entry.memory_strategy == "SINGLE_GPU"
    assert offload_entry.memory_strategy == "CPU_OFFLOAD"
    assert single_gpu_entry.score.overall > offload_entry.score.overall
    assert single_gpu_entry.tier == RecommendationTier.BEST_MATCH
    assert offload_entry.tier in {
        RecommendationTier.GOOD,
        RecommendationTier.NOT_RECOMMENDED,
    }


def test_confidence_is_exposed_and_reasons_are_non_empty():

    hardware = make_hardware(vram_gb=16, ram_gb=32)
    model = make_model("Test")

    engine = RecommendationEngine()

    result = engine.recommend(hardware, [model], task="general_chat")

    entry = result.recommendations[0]

    assert entry.confidence is not None
    assert len(entry.reasons) > 0


def test_excluded_models_still_carry_an_explanatory_reason():

    hardware = make_hardware(vram_gb=1, ram_gb=1)
    huge_model = make_model("Huge", parameters=200_000_000_000)

    engine = RecommendationEngine()

    result = engine.recommend(hardware, [huge_model], task="general_chat")

    assert len(result.excluded[0].reasons) > 0


def test_recommendations_carry_a_performance_prediction():

    hardware = make_hardware(vram_gb=16, ram_gb=32)
    model = make_model("Test")

    engine = RecommendationEngine()

    result = engine.recommend(hardware, [model], task="general_chat")

    entry = result.recommendations[0]

    assert entry.performance is not None
    assert entry.performance.generation_speed is not None
    assert entry.performance.generation_speed.low > 0


def test_excluded_models_carry_a_performance_prediction_with_no_speed():

    hardware = make_hardware(vram_gb=1, ram_gb=1)
    huge_model = make_model("Huge", parameters=200_000_000_000)

    engine = RecommendationEngine()

    result = engine.recommend(hardware, [huge_model], task="general_chat")

    entry = result.excluded[0]

    assert entry.performance is not None
    assert entry.performance.generation_speed is None
