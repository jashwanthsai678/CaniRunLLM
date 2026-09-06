from canirunllm.hardware.scanner import scan_hardware
from canirunllm.models.hardware import HardwareProfile


def test_hardware_scan():
    hardware = scan_hardware()

    assert isinstance(hardware, HardwareProfile)
    assert hardware.cpu is not None
    assert hardware.memory is not None
    assert hardware.os is not None

    assert hardware.memory.total_bytes > 0
