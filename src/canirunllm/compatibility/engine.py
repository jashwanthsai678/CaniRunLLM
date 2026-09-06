from dataclasses import dataclass

from canirunllm.models.hardware import HardwareProfile
from canirunllm.models.model import ModelSpec

from canirunllm.compatibility.config import MemoryConfig
from canirunllm.compatibility.requirements import (
    estimate_memory_requirement,
)

from canirunllm.compatibility.memory_planner import (
    MemoryPlan,
    create_memory_plan,
)

from canirunllm.compatibility.verdict import (
    MemoryVerdict,
)

from canirunllm.compatibility.runtime import (
    RuntimeCapabilities,
    RuntimeVerdict,
    check_runtime_compatibility,
    get_runtime_capabilities,
)

from canirunllm.compatibility.decision import (
    determine_overall_verdict,
    OverallVerdict,
)

from canirunllm.compatibility.confidence import (
    determine_confidence,
    ConfidenceLevel,
)


@dataclass
class CompatibilityResult:
    overall_verdict: OverallVerdict
    confidence: ConfidenceLevel

    memory_verdict: MemoryVerdict
    runtime_verdict: RuntimeVerdict

    required_memory_bytes: int
    available_vram_bytes: int
    available_ram_bytes: int

    memory_strategy: str
    reason: str


def determine_memory_strategy(
    memory_plan: MemoryPlan,
    runtime_capabilities: RuntimeCapabilities,
) -> str:

    if memory_plan.can_fit_single_gpu:
        return "SINGLE_GPU"

    if (
        memory_plan.can_fit_multi_gpu
        and runtime_capabilities.supports_multi_gpu
    ):
        return "MULTI_GPU"

    if (
        memory_plan.can_fit_with_cpu_offload
        and runtime_capabilities.supports_cpu_offload
    ):
        return "CPU_OFFLOAD"

    return "NONE"


def check_compatibility(
    hardware: HardwareProfile,
    model: ModelSpec,
    config: MemoryConfig | None = None,
) -> CompatibilityResult:

    requirement = estimate_memory_requirement(
        model,
        config,
    )

    required_memory = (
        requirement.total_required_bytes
    )

    runtime_verdict = check_runtime_compatibility(model)

    runtime_capabilities = get_runtime_capabilities(
        model.runtime
    )

    memory_plan = create_memory_plan(
        hardware,
        required_memory,
        config,
    )

    memory_strategy = determine_memory_strategy(
        memory_plan,
        runtime_capabilities,
    )

    if memory_strategy == "SINGLE_GPU":

        memory_verdict = MemoryVerdict.FIT
        reason = (
            "Model fits in available VRAM on a single "
            "GPU including KV cache, overhead, and "
            "safety margin."
        )

    elif memory_strategy == "MULTI_GPU":

        memory_verdict = MemoryVerdict.MULTI_GPU
        reason = (
            "Model does not fit on a single GPU but may "
            "fit by distributing weights across multiple "
            "GPUs."
        )

    elif memory_strategy == "CPU_OFFLOAD":

        memory_verdict = MemoryVerdict.CPU_OFFLOAD
        reason = (
            "Model does not fit entirely in VRAM but may "
            "run using RAM offloading."
        )

    else:

        memory_verdict = MemoryVerdict.NO_FIT
        reason = (
            "Required memory exceeds available VRAM + RAM "
            "across all supported memory strategies."
        )

    overall_verdict = determine_overall_verdict(
        memory_verdict,
        runtime_verdict,
    )

    confidence = determine_confidence(
        memory_verdict,
        runtime_verdict,
        overall_verdict,
    )

    return CompatibilityResult(
        overall_verdict=overall_verdict,
        confidence=confidence,
        memory_verdict=memory_verdict,
        runtime_verdict=runtime_verdict,
        required_memory_bytes=required_memory,
        available_vram_bytes=memory_plan.largest_gpu_free_bytes,
        available_ram_bytes=memory_plan.available_ram_bytes,
        memory_strategy=memory_strategy,
        reason=reason,
    )
