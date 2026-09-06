from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.engine import CompatibilityResult
from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.confidence import ConfidenceLevel

from canirunllm.performance.prediction import (
    predict_performance,
    PredictionSource,
)


def make_model(parameters=7_000_000_000):
    return ModelSpec(
        name="Test",
        family="Test",
        parameters=parameters,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
        runtime="llama.cpp",
    )


def make_compatibility(overall_verdict, memory_strategy):
    return CompatibilityResult(
        overall_verdict=overall_verdict,
        confidence=ConfidenceLevel.HIGH,
        memory_verdict=MemoryVerdict.FIT,
        runtime_verdict=RuntimeVerdict.SUPPORTED,
        required_memory_bytes=int(5 * 1024**3),
        available_vram_bytes=int(10 * 1024**3),
        available_ram_bytes=int(20 * 1024**3),
        memory_strategy=memory_strategy,
        reason="test",
    )


def test_cannot_run_produces_no_speed_range():

    model = make_model()
    compatibility = make_compatibility(
        OverallVerdict.CANNOT_RUN,
        "NONE",
    )

    prediction = predict_performance(model, compatibility)

    assert prediction.generation_speed is None
    assert prediction.confidence == ConfidenceLevel.LOW
    assert prediction.source == PredictionSource.MODELLED_ESTIMATE
    assert len(prediction.explanation) > 0


def test_single_gpu_produces_a_valid_range():

    model = make_model(parameters=7_000_000_000)
    compatibility = make_compatibility(
        OverallVerdict.CAN_RUN,
        "SINGLE_GPU",
    )

    prediction = predict_performance(model, compatibility)

    assert prediction.generation_speed is not None
    assert prediction.generation_speed.low > 0
    assert prediction.generation_speed.high > prediction.generation_speed.low
    assert prediction.generation_speed.unit == "tok/s"
    assert prediction.confidence == ConfidenceLevel.LOW


def test_cpu_offload_is_slower_than_single_gpu_for_same_model():

    model = make_model(parameters=7_000_000_000)

    single_gpu = predict_performance(
        model,
        make_compatibility(OverallVerdict.CAN_RUN, "SINGLE_GPU"),
    )
    cpu_offload = predict_performance(
        model,
        make_compatibility(
            OverallVerdict.CAN_RUN_WITH_OFFLOAD, "CPU_OFFLOAD"
        ),
    )

    assert cpu_offload.generation_speed.high < single_gpu.generation_speed.low


def test_multi_gpu_is_between_single_gpu_and_cpu_offload():

    model = make_model(parameters=7_000_000_000)

    single_gpu = predict_performance(
        model,
        make_compatibility(OverallVerdict.CAN_RUN, "SINGLE_GPU"),
    )
    multi_gpu = predict_performance(
        model,
        make_compatibility(
            OverallVerdict.CAN_RUN_WITH_OFFLOAD, "MULTI_GPU"
        ),
    )
    cpu_offload = predict_performance(
        model,
        make_compatibility(
            OverallVerdict.CAN_RUN_WITH_OFFLOAD, "CPU_OFFLOAD"
        ),
    )

    assert multi_gpu.generation_speed.low < single_gpu.generation_speed.low
    assert multi_gpu.generation_speed.low > cpu_offload.generation_speed.low


def test_larger_models_predict_lower_speed_than_smaller_models():

    small_model = make_model(parameters=4_000_000_000)
    large_model = make_model(parameters=70_000_000_000)

    compatibility = make_compatibility(OverallVerdict.CAN_RUN, "SINGLE_GPU")

    small_prediction = predict_performance(small_model, compatibility)
    large_prediction = predict_performance(large_model, compatibility)

    assert (
        large_prediction.generation_speed.high
        < small_prediction.generation_speed.low
    )
