import subprocess
from unittest.mock import MagicMock, patch

from canirunllm.hardware.gpu import (
    _parse_gpu_line,
    _parse_rocm_smi_json,
    get_gpu_info,
)


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


def test_parse_rocm_smi_json_converts_single_card():
    raw = '''{"card0": {"Card series": "Radeon RX 7900 XTX",
                        "VRAM Total Memory (B)": "25757220864",
                        "VRAM Total Used Memory (B)": "500000000"}}'''

    parsed = _parse_rocm_smi_json(raw)

    assert len(parsed) == 1
    assert parsed[0]["name"] == "Radeon RX 7900 XTX"
    assert parsed[0]["memory_total_bytes"] == 25757220864
    assert parsed[0]["memory_used_bytes"] == 500000000
    assert parsed[0]["memory_free_bytes"] == 25757220864 - 500000000


def test_parse_rocm_smi_json_skips_cards_missing_memory_fields():
    raw = '{"card0": {"Card series": "Radeon RX 6600"}}'

    assert _parse_rocm_smi_json(raw) == []


def test_get_gpu_info_detects_amd_gpu_via_rocm_smi():
    fake_result = MagicMock()
    fake_result.stdout = (
        '{"card0": {"Card series": "Radeon RX 7900 XTX", '
        '"VRAM Total Memory (B)": "25757220864", '
        '"VRAM Total Used Memory (B)": "500000000"}}'
    )

    def which(name):
        return "/usr/bin/rocm-smi" if name == "rocm-smi" else None

    with patch("canirunllm.hardware.gpu.shutil.which", side_effect=which), \
         patch("canirunllm.hardware.gpu.subprocess.run", return_value=fake_result), \
         patch("canirunllm.hardware.gpu.platform.system", return_value="Linux"):
        gpus = get_gpu_info()

    assert len(gpus) == 1
    assert gpus[0]["name"] == "Radeon RX 7900 XTX"
    assert gpus[0]["memory_free_bytes"] == 25757220864 - 500000000


def test_get_gpu_info_returns_empty_when_rocm_smi_output_is_not_json():
    fake_result = MagicMock()
    fake_result.stdout = "not json at all"

    def which(name):
        return "/usr/bin/rocm-smi" if name == "rocm-smi" else None

    with patch("canirunllm.hardware.gpu.shutil.which", side_effect=which), \
         patch("canirunllm.hardware.gpu.subprocess.run", return_value=fake_result), \
         patch("canirunllm.hardware.gpu.platform.system", return_value="Linux"):
        assert get_gpu_info() == []


def test_get_gpu_info_reports_unified_memory_on_apple_silicon():
    fake_memory = MagicMock(total=16 * 1024**3, used=8 * 1024**3, available=8 * 1024**3)
    fake_display_result = MagicMock()
    fake_display_result.stdout = (
        '{"SPDisplaysDataType": [{"sppci_model": "Apple M2 Pro"}]}'
    )

    with patch("canirunllm.hardware.gpu.shutil.which", return_value=None), \
         patch("canirunllm.hardware.gpu.platform.system", return_value="Darwin"), \
         patch("canirunllm.hardware.gpu.platform.machine", return_value="arm64"), \
         patch("canirunllm.hardware.gpu.psutil.virtual_memory", return_value=fake_memory), \
         patch("canirunllm.hardware.gpu.subprocess.run", return_value=fake_display_result):
        gpus = get_gpu_info()

    assert len(gpus) == 1
    assert gpus[0]["name"] == "Apple M2 Pro"
    assert gpus[0]["is_unified_memory"] is True
    assert gpus[0]["memory_total_bytes"] == 16 * 1024**3
    assert gpus[0]["memory_free_bytes"] == 8 * 1024**3


def test_get_gpu_info_skips_apple_silicon_path_on_intel_mac():
    with patch("canirunllm.hardware.gpu.shutil.which", return_value=None), \
         patch("canirunllm.hardware.gpu.platform.system", return_value="Darwin"), \
         patch("canirunllm.hardware.gpu.platform.machine", return_value="x86_64"):
        assert get_gpu_info() == []
