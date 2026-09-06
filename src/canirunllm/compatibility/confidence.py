from enum import Enum

from canirunllm.compatibility.verdict import MemoryVerdict
from canirunllm.compatibility.runtime import RuntimeVerdict
from canirunllm.compatibility.decision import OverallVerdict


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def determine_confidence(
    memory_verdict: MemoryVerdict,
    runtime_verdict: RuntimeVerdict,
    overall_verdict: OverallVerdict,
) -> ConfidenceLevel:

    if overall_verdict == OverallVerdict.CAN_RUN:
        if (
            memory_verdict == MemoryVerdict.FIT
            and runtime_verdict == RuntimeVerdict.SUPPORTED
        ):
            return ConfidenceLevel.HIGH

    if overall_verdict == OverallVerdict.CAN_RUN_WITH_OFFLOAD:
        return ConfidenceLevel.MEDIUM

    if overall_verdict == OverallVerdict.NEEDS_VALIDATION:
        return ConfidenceLevel.LOW

    if overall_verdict == OverallVerdict.CANNOT_RUN:
        if memory_verdict == MemoryVerdict.NO_FIT:
            return ConfidenceLevel.HIGH

        return ConfidenceLevel.MEDIUM

    return ConfidenceLevel.LOW
