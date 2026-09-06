from canirunllm.models.results import ModelCheckResult
from canirunllm.models.model import ModelSpec
from canirunllm.models.hardware import (
    HardwareProfile,
    CPUInfo,
    MemoryInfo,
    GPUInfo,
    OSInfo,
)
from canirunllm.compatibility.engine import check_compatibility


def test_model_check_result():
    model = ModelSpec(
        name="TestModel-Q4",
        family="TestModel",
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
        runtime="llama.cpp",
    )

    assert model.name == "TestModel-Q4"


def test_model_check_result_to_dict():

    hardware = HardwareProfile(
        cpu=CPUInfo(
            name="Test CPU",
            architecture="x86_64",
            physical_cores=8,
            logical_cores=16,
            frequency_mhz=3000,
        ),
        memory=MemoryInfo(
            total_bytes=32 * 1024**3,
            available_bytes=32 * 1024**3,
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
                memory_total_bytes=16 * 1024**3,
                memory_used_bytes=0,
                memory_free_bytes=16 * 1024**3,
                utilization_percent=0,
            )
        ],
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
        runtime="llama.cpp",
    )

    result = check_compatibility(hardware, model)

    check_result = ModelCheckResult(
        model=model,
        compatibility=result,
    )

    data = check_result.to_dict()

    assert data["model"]["name"] == "Test-7B"
    assert data["compatibility"]["memory_verdict"] == "FIT"
    assert data["compatibility"]["overall_verdict"] == "CAN_RUN"
    assert data["compatibility"]["confidence"] == "HIGH"
