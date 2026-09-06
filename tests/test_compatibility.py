from canirunllm.models.hardware import (
    HardwareProfile,
    CPUInfo,
    MemoryInfo,
    GPUInfo,
    OSInfo,
)

from canirunllm.models.model import ModelSpec

from canirunllm.compatibility.engine import (
    check_compatibility,
)


def create_hardware(
    vram_gb: float,
    ram_gb: float,
):

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
                name="Test GPU",
                memory_total_bytes=int(vram_gb * 1024**3),
                memory_used_bytes=0,
                memory_free_bytes=int(vram_gb * 1024**3),
                utilization_percent=0,
            )
        ],
    )


def test_model_fits_in_vram():

    hardware = create_hardware(
        vram_gb=16,
        ram_gb=32,
    )

    model = ModelSpec(
        name="Test-7B",
        family="Test-7B",
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
        num_layers=32,
        num_kv_heads=8,
        head_dim=128,
    )

    result = check_compatibility(
        hardware,
        model,
    )

    assert result.verdict == "FIT"


def test_model_requires_offloading():

    hardware = create_hardware(
        vram_gb=2,
        ram_gb=16,
    )

    model = ModelSpec(
        name="Test-7B",
        family="Test-7B",
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
        num_layers=32,
        num_kv_heads=8,
        head_dim=128,
    )

    result = check_compatibility(
        hardware,
        model,
    )

    assert result.verdict == "OFFLOAD"
