from canirunllm.hardware.scanner import scan_hardware


def test_hardware_scan():
    hardware = scan_hardware()

    assert "cpu" in hardware
    assert "memory" in hardware
    assert "os" in hardware

    assert hardware["memory"]["total_bytes"] > 0