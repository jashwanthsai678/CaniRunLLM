from dataclasses import dataclass

from canirunllm.models.hardware import HardwareProfile
from canirunllm.models.model import ModelSpec

from canirunllm.compatibility.config import MemoryConfig
from canirunllm.compatibility.requirements import (
    estimate_memory_requirement,
)


@dataclass
class CompatibilityResult:
    verdict: str
    required_memory_bytes: int
    available_vram_bytes: int
    available_ram_bytes: int
    reason: str


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

    total_vram = sum(
        gpu.memory_free_bytes
        for gpu in hardware.gpus
    )

    available_ram = (
        hardware.memory.available_bytes
    )

    if required_memory <= total_vram:

        return CompatibilityResult(
            verdict="FIT",
            required_memory_bytes=required_memory,
            available_vram_bytes=total_vram,
            available_ram_bytes=available_ram,
            reason=(
                "Model fits in available VRAM "
                "including KV cache, overhead, "
                "and safety margin."
            ),
        )

    if required_memory <= (
        total_vram + available_ram
    ):

        return CompatibilityResult(
            verdict="OFFLOAD",
            required_memory_bytes=required_memory,
            available_vram_bytes=total_vram,
            available_ram_bytes=available_ram,
            reason=(
                "Model may run using RAM offloading."
            ),
        )

    return CompatibilityResult(
        verdict="NO_FIT",
        required_memory_bytes=required_memory,
        available_vram_bytes=total_vram,
        available_ram_bytes=available_ram,
        reason=(
            "Required memory exceeds "
            "available VRAM + RAM."
        ),
    )
