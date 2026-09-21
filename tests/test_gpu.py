import subprocess
from unittest.mock import MagicMock, patch

from canirunllm.hardware.gpu import _parse_gpu_line, get_gpu_info


def test_parse_gpu_line_converts_mib_to_bytes_and_percent():
    parsed = _parse_gpu_line("NVIDIA GeForce RTX 3050, 4096, 150, 3946, 5")

    assert parsed["name"] == "NVIDIA GeForce RTX 3050"
    assert parsed["memory_total_bytes"] == 4096 * 1024 * 1024
    assert parsed["memory_used_bytes"] == 150 * 1024 * 1024
    assert parsed["memory_free_bytes"] == 3946 * 1024 * 1024
    assert parsed["utilization_percent"] == 5.0


def test_get_gpu_info_returns_empty_when_nvidia_smi_not_on_path():
    with patch("canirunllm.hardware.gpu.shutil.which", return_value=None):
        assert get_gpu_info() == []


def test_get_gpu_info_returns_empty_when_subprocess_fails():
    with patch("canirunllm.hardware.gpu.shutil.which", return_value="/usr/bin/nvidia-smi"), \
         patch("canirunllm.hardware.gpu.subprocess.run", side_effect=subprocess.TimeoutExpired("nvidia-smi", 5)):
        assert get_gpu_info() == []


def test_get_gpu_info_returns_empty_when_nvidia_smi_not_found_at_runtime():
    with patch("canirunllm.hardware.gpu.shutil.which", return_value="/usr/bin/nvidia-smi"), \
         patch("canirunllm.hardware.gpu.subprocess.run", side_effect=FileNotFoundError()):
        assert get_gpu_info() == []


def test_get_gpu_info_parses_single_gpu_output():
    fake_result = MagicMock()
    fake_result.stdout = "NVIDIA GeForce RTX 3050 Laptop GPU, 4096, 150, 3946, 5\n"

    with patch("canirunllm.hardware.gpu.shutil.which", return_value="/usr/bin/nvidia-smi"), \
         patch("canirunllm.hardware.gpu.subprocess.run", return_value=fake_result):
        gpus = get_gpu_info()

    assert len(gpus) == 1
    assert gpus[0]["name"] == "NVIDIA GeForce RTX 3050 Laptop GPU"
    assert gpus[0]["memory_total_bytes"] == 4096 * 1024 * 1024


def test_get_gpu_info_parses_multiple_gpus():
    fake_result = MagicMock()
    fake_result.stdout = (
        "NVIDIA GeForce RTX 3050, 4096, 100, 3996, 2\n"
        "NVIDIA GeForce RTX 4090, 24576, 500, 24076, 10\n"
    )

    with patch("canirunllm.hardware.gpu.shutil.which", return_value="/usr/bin/nvidia-smi"), \
         patch("canirunllm.hardware.gpu.subprocess.run", return_value=fake_result):
        gpus = get_gpu_info()

    assert len(gpus) == 2
    assert gpus[0]["name"] == "NVIDIA GeForce RTX 3050"
    assert gpus[1]["name"] == "NVIDIA GeForce RTX 4090"


def test_get_gpu_info_skips_malformed_lines_instead_of_crashing():
    fake_result = MagicMock()
    fake_result.stdout = (
        "not,a,valid,gpu,line,with,too,many,fields\n"
        "NVIDIA GeForce RTX 3050, 4096, 100, 3996, 2\n"
    )

    with patch("canirunllm.hardware.gpu.shutil.which", return_value="/usr/bin/nvidia-smi"), \
         patch("canirunllm.hardware.gpu.subprocess.run", return_value=fake_result):
        gpus = get_gpu_info()

    assert len(gpus) == 1
    assert gpus[0]["name"] == "NVIDIA GeForce RTX 3050"


def test_get_gpu_info_returns_empty_for_blank_output():
    fake_result = MagicMock()
    fake_result.stdout = "\n"

    with patch("canirunllm.hardware.gpu.shutil.which", return_value="/usr/bin/nvidia-smi"), \
         patch("canirunllm.hardware.gpu.subprocess.run", return_value=fake_result):
        assert get_gpu_info() == []
