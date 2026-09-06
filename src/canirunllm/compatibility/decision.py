from enum import Enum

from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict


class OverallVerdict(str, Enum):
    CAN_RUN = "CAN_RUN"
    CAN_RUN_WITH_OFFLOAD = "CAN_RUN_WITH_OFFLOAD"
    NEEDS_VALIDATION = "NEEDS_VALIDATION"
    CANNOT_RUN = "CANNOT_RUN"


def determine_overall_verdict(
    memory_verdict: MemoryVerdict,
    runtime_verdict: RuntimeVerdict,
) -> OverallVerdict:

    # Memory is fundamentally insufficient.
    if memory_verdict == MemoryVerdict.NO_FIT:
        return OverallVerdict.CANNOT_RUN

    # Runtime is explicitly unsupported.
    if runtime_verdict == RuntimeVerdict.UNSUPPORTED:
        return OverallVerdict.CANNOT_RUN

    # Everything fits and runtime is known to be supported.
    if (
        memory_verdict == MemoryVerdict.FIT
        and runtime_verdict == RuntimeVerdict.SUPPORTED
    ):
        return OverallVerdict.CAN_RUN

    # Memory requires multi-GPU distribution or RAM offloading.
    if (
        memory_verdict in {
            MemoryVerdict.MULTI_GPU,
            MemoryVerdict.CPU_OFFLOAD,
        }
        and runtime_verdict == RuntimeVerdict.SUPPORTED
    ):
        return OverallVerdict.CAN_RUN_WITH_OFFLOAD

    # We don't have enough information to make a confident claim.
    return OverallVerdict.NEEDS_VALIDATION
