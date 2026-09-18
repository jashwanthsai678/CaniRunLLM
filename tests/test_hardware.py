from pathlib import Path

from canirunllm.hardware.disk import get_disk_info
from canirunllm.hardware.scanner import scan_hardware
from canirunllm.models.hardware import DiskInfo, HardwareProfile


def test_hardware_scan():
    hardware = scan_hardware()

    assert isinstance(hardware, HardwareProfile)
    assert hardware.cpu is not None
    assert hardware.memory is not None
    assert hardware.os is not None

    assert hardware.memory.total_bytes > 0


def test_hardware_scan_includes_disk():
    hardware = scan_hardware()

    assert isinstance(hardware.disk, DiskInfo)
    assert hardware.disk.total_bytes > 0
    assert hardware.disk.free_bytes >= 0
    assert hardware.disk.used_bytes >= 0


def test_get_disk_info_defaults_to_home_directory():
    info = get_disk_info()

    assert info["total_bytes"] > 0
    assert info["free_bytes"] >= 0
    assert info["used_bytes"] >= 0
    assert info["free_bytes"] <= info["total_bytes"]


def test_get_disk_info_accepts_explicit_path():
    info = get_disk_info(Path.cwd())

    assert info["total_bytes"] > 0
