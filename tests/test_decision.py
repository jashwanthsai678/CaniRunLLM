from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.decision import (
    determine_overall_verdict,
    OverallVerdict,
)


def test_fit_and_supported_can_run():

    result = determine_overall_verdict(
        MemoryVerdict.FIT,
        RuntimeVerdict.SUPPORTED,
    )

    assert result == OverallVerdict.CAN_RUN


def test_multi_gpu_and_supported_can_run_with_offload():

    result = determine_overall_verdict(
        MemoryVerdict.MULTI_GPU,
        RuntimeVerdict.SUPPORTED,
    )

    assert result == OverallVerdict.CAN_RUN_WITH_OFFLOAD


def test_cpu_offload_and_supported_can_run_with_offload():

    result = determine_overall_verdict(
        MemoryVerdict.CPU_OFFLOAD,
        RuntimeVerdict.SUPPORTED,
    )

    assert result == OverallVerdict.CAN_RUN_WITH_OFFLOAD


def test_no_fit_is_always_cannot_run():

    for runtime_verdict in RuntimeVerdict:

        result = determine_overall_verdict(
            MemoryVerdict.NO_FIT,
            runtime_verdict,
        )

        assert result == OverallVerdict.CANNOT_RUN


def test_unsupported_runtime_is_always_cannot_run():

    for memory_verdict in MemoryVerdict:

        result = determine_overall_verdict(
            memory_verdict,
            RuntimeVerdict.UNSUPPORTED,
        )

        assert result == OverallVerdict.CANNOT_RUN


def test_unknown_runtime_needs_validation():

    result = determine_overall_verdict(
        MemoryVerdict.FIT,
        RuntimeVerdict.UNKNOWN,
    )

    assert result == OverallVerdict.NEEDS_VALIDATION
