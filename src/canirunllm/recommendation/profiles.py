from dataclasses import dataclass
from enum import Enum


class WorkloadProfile(str, Enum):
    GENERAL_CHAT = "GENERAL_CHAT"
    CODING = "CODING"
    RAG = "RAG"
    REASONING = "REASONING"


@dataclass(frozen=True)
class WorkloadRequirements:
    """What a workload cares about when ranking model candidates.

    minimum_recommended_context is a practical floor, not a hard
    requirement — models below it are scored lower, not excluded.

    weights must sum to 1.0 across: fit, memory_efficiency,
    context, runtime, confidence.
    """

    profile: WorkloadProfile
    minimum_recommended_context: int
    weights: dict[str, float]


WORKLOAD_REQUIREMENTS: dict[WorkloadProfile, WorkloadRequirements] = {

    WorkloadProfile.GENERAL_CHAT: WorkloadRequirements(
        profile=WorkloadProfile.GENERAL_CHAT,
        minimum_recommended_context=4096,
        weights={
            "fit": 0.35,
            "memory_efficiency": 0.25,
            "context": 0.10,
            "runtime": 0.15,
            "confidence": 0.15,
        },
    ),

    WorkloadProfile.CODING: WorkloadRequirements(
        profile=WorkloadProfile.CODING,
        minimum_recommended_context=16384,
        weights={
            "fit": 0.30,
            "memory_efficiency": 0.15,
            "context": 0.25,
            "runtime": 0.15,
            "confidence": 0.15,
        },
    ),

    WorkloadProfile.RAG: WorkloadRequirements(
        profile=WorkloadProfile.RAG,
        minimum_recommended_context=32768,
        weights={
            "fit": 0.25,
            "memory_efficiency": 0.10,
            "context": 0.35,
            "runtime": 0.15,
            "confidence": 0.15,
        },
    ),

    WorkloadProfile.REASONING: WorkloadRequirements(
        profile=WorkloadProfile.REASONING,
        minimum_recommended_context=8192,
        weights={
            "fit": 0.35,
            "memory_efficiency": 0.20,
            "context": 0.15,
            "runtime": 0.15,
            "confidence": 0.15,
        },
    ),
}


def resolve_workload(task: str) -> WorkloadProfile:

    try:
        return WorkloadProfile(task.strip().upper())
    except ValueError:
        known = ", ".join(profile.value for profile in WorkloadProfile)
        raise ValueError(
            f"Unknown workload task: {task!r}. Known tasks: {known}"
        )
