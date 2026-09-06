from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.compatibility.confidence import (
    ConfidenceLevel,
    determine_confidence,
)


def test_can_run_with_fit_and_supported_is_high():

    confidence = determine_confidence(
        MemoryVerdict.FIT,
        RuntimeVerdict.SUPPORTED,
        OverallVerdict.CAN_RUN,
    )

    assert confidence == ConfidenceLevel.HIGH


def test_can_run_with_multi_gpu_is_medium():

    confidence = determine_confidence(
        MemoryVerdict.MULTI_GPU,
        RuntimeVerdict.SUPPORTED,
        OverallVerdict.CAN_RUN_WITH_OFFLOAD,
    )

    assert confidence == ConfidenceLevel.MEDIUM


def test_can_run_with_cpu_offload_is_medium():

    confidence = determine_confidence(
        MemoryVerdict.CPU_OFFLOAD,
        RuntimeVerdict.SUPPORTED,
        OverallVerdict.CAN_RUN_WITH_OFFLOAD,
    )

    assert confidence == ConfidenceLevel.MEDIUM


def test_needs_validation_is_low():

    confidence = determine_confidence(
        MemoryVerdict.FIT,
        RuntimeVerdict.UNKNOWN,
        OverallVerdict.NEEDS_VALIDATION,
    )

    assert confidence == ConfidenceLevel.LOW


def test_cannot_run_due_to_no_fit_is_high():

    confidence = determine_confidence(
        MemoryVerdict.NO_FIT,
        RuntimeVerdict.SUPPORTED,
        OverallVerdict.CANNOT_RUN,
    )

    assert confidence == ConfidenceLevel.HIGH


def test_cannot_run_due_to_unsupported_runtime_is_medium():

    confidence = determine_confidence(
        MemoryVerdict.FIT,
        RuntimeVerdict.UNSUPPORTED,
        OverallVerdict.CANNOT_RUN,
    )

    assert confidence == ConfidenceLevel.MEDIUM
