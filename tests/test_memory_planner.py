from canirunllm.models.hardware import (
    HardwareProfile,
    CPUInfo,
    MemoryInfo,
    GPUInfo,
    OSInfo,
)

from canirunllm.compatibility.memory_planner import (
    create_memory_plan,
)
from canirunllm.compatibility.config import MemoryConfig


def create_hardware(gpu_free_gb: list[float], ram_gb: float):

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
                name=f"Test GPU {index}",
                memory_total_bytes=int(free_gb * 1024**3),
                memory_used_bytes=0,
                memory_free_bytes=int(free_gb * 1024**3),
                utilization_percent=0,
            )
            for index, free_gb in enumerate(gpu_free_gb)
        ],
    )


def test_small_model_fits_single_gpu():

    hardware = create_hardware([8, 8], ram_gb=32)

    plan = create_memory_plan(
        hardware,
        required_bytes=int(7 * 1024**3),
    )

    assert plan.can_fit_single_gpu is True
    assert plan.can_fit_multi_gpu is True
    assert plan.can_fit_with_cpu_offload is True


def test_model_too_big_for_single_gpu_but_fits_across_multiple():

    hardware = create_hardware([8, 8], ram_gb=32)

    plan = create_memory_plan(
        hardware,
        required_bytes=int(12 * 1024**3),
    )

    assert plan.can_fit_single_gpu is False
    assert plan.can_fit_multi_gpu is True
    assert plan.can_fit_with_cpu_offload is True


def test_single_gpu_machine_has_no_multi_gpu_option():

    hardware = create_hardware([8], ram_gb=32)

    plan = create_memory_plan(
        hardware,
        required_bytes=int(12 * 1024**3),
    )

    assert plan.can_fit_single_gpu is False
    assert plan.can_fit_multi_gpu is False
    assert plan.can_fit_with_cpu_offload is True


def test_model_exceeds_everything():

    hardware = create_hardware([8, 8], ram_gb=4)

    plan = create_memory_plan(
        hardware,
        required_bytes=int(64 * 1024**3),
    )

    assert plan.can_fit_single_gpu is False
    assert plan.can_fit_multi_gpu is False
    assert plan.can_fit_with_cpu_offload is False


def test_no_gpus_falls_back_to_ram_only():

    hardware = create_hardware([], ram_gb=32)

    plan = create_memory_plan(
        hardware,
        required_bytes=int(7 * 1024**3),
    )

    assert plan.largest_gpu_free_bytes == 0
    assert plan.total_gpu_free_bytes == 0
    assert plan.can_fit_single_gpu is False
    assert plan.can_fit_multi_gpu is False
    assert plan.can_fit_with_cpu_offload is True


def test_gpu_count_reflects_number_of_gpus():

    hardware = create_hardware([8, 8, 8], ram_gb=32)

    plan = create_memory_plan(
        hardware,
        required_bytes=int(7 * 1024**3),
    )

    assert plan.gpu_count == 3


def test_default_reservation_reduces_usable_memory():

    hardware = create_hardware([10], ram_gb=20)

    plan = create_memory_plan(
        hardware,
        required_bytes=int(1 * 1024**3),
    )

    assert plan.usable_gpu_bytes == int(9 * 1024**3)
    assert plan.usable_ram_bytes == int(18 * 1024**3)


def test_custom_reservation_percentages_are_applied():

    hardware = create_hardware([10], ram_gb=20)

    config = MemoryConfig(
        gpu_reserved_percent=20.0,
        ram_reserved_percent=25.0,
    )

    plan = create_memory_plan(
        hardware,
        required_bytes=int(1 * 1024**3),
        config=config,
    )

    assert plan.usable_gpu_bytes == int(8 * 1024**3)
    assert plan.usable_ram_bytes == int(15 * 1024**3)


def test_reservation_can_tip_a_borderline_model_from_fit_to_no_fit():

    hardware = create_hardware([10], ram_gb=0)

    required = int(9.5 * 1024**3)

    lenient_plan = create_memory_plan(
        hardware,
        required_bytes=required,
        config=MemoryConfig(gpu_reserved_percent=0.0),
    )

    strict_plan = create_memory_plan(
        hardware,
        required_bytes=required,
        config=MemoryConfig(gpu_reserved_percent=20.0),
    )

    assert lenient_plan.can_fit_single_gpu is True
    assert strict_plan.can_fit_single_gpu is False
