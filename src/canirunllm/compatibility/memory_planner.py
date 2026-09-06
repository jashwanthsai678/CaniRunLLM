from dataclasses import dataclass

from canirunllm.models.hardware import HardwareProfile
from canirunllm.compatibility.config import MemoryConfig


@dataclass
class MemoryPlan:
    required_bytes: int

    largest_gpu_free_bytes: int
    total_gpu_free_bytes: int
    available_ram_bytes: int

    usable_gpu_bytes: int
    usable_ram_bytes: int

    can_fit_single_gpu: bool
    can_fit_multi_gpu: bool
    can_fit_with_cpu_offload: bool

    gpu_count: int


def create_memory_plan(
    hardware: HardwareProfile,
    required_bytes: int,
    config: MemoryConfig | None = None,
) -> MemoryPlan:

    if config is None:
        config = MemoryConfig()

    gpu_free = [
        gpu.memory_free_bytes
        for gpu in hardware.gpus
    ]

    largest_gpu = max(gpu_free, default=0)
    total_gpu = sum(gpu_free)

    ram = hardware.memory.available_bytes

    gpu_reservation = int(
        largest_gpu * config.gpu_reserved_percent / 100
    )

    ram_reservation = int(
        ram * config.ram_reserved_percent / 100
    )

    usable_gpu = max(
        0,
        largest_gpu - gpu_reservation
    )

    usable_ram = max(
        0,
        ram - ram_reservation
    )

    usable_total_gpu = max(
        0,
        total_gpu - gpu_reservation
    )

    return MemoryPlan(
        required_bytes=required_bytes,

        largest_gpu_free_bytes=largest_gpu,
        total_gpu_free_bytes=total_gpu,
        available_ram_bytes=ram,

        usable_gpu_bytes=usable_gpu,
        usable_ram_bytes=usable_ram,

        can_fit_single_gpu=(
            required_bytes <= usable_gpu
        ),

        can_fit_multi_gpu=(
            len(gpu_free) > 1
            and required_bytes <= usable_total_gpu
        ),

        can_fit_with_cpu_offload=(
            required_bytes <= usable_total_gpu + usable_ram
        ),

        gpu_count=len(gpu_free),
    )
