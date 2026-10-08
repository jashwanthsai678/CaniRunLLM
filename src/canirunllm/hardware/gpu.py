import json
import platform
import shutil
import subprocess

import psutil

_NVIDIA_QUERY_FIELDS = "name,memory.total,memory.used,memory.free,utilization.gpu"
_TIMEOUT_SECONDS = 5


def _parse_gpu_line(line: str) -> dict:
    name, mem_total, mem_used, mem_free, utilization = (
        part.strip() for part in line.split(",")
    )

    return {
        "name": name,
        "memory_total_bytes": int(float(mem_total) * 1024 * 1024),
        "memory_used_bytes": int(float(mem_used) * 1024 * 1024),
        "memory_free_bytes": int(float(mem_free) * 1024 * 1024),
        "utilization_percent": float(utilization),
    }


def _get_nvidia_gpu_info() -> list[dict]:
    """NVIDIA GPUs, via nvidia-smi directly - no third-party GPU library
    involved.

    Previously used the GPUtil package, which is unmaintained and
    crashes on Python 3.12+: it does `from distutils import spawn`,
    and Python removed distutils from the standard library in 3.12.
    That crash happened at import time, before any command could even
    run - see a real report of this breaking every single command,
    including --help. Shelling out to nvidia-smi (installed alongside
    any NVIDIA driver, no separate Python package needed) removes that
    fragile dependency entirely.

    Returns [] if nvidia-smi isn't on PATH (no NVIDIA GPU/driver) or if
    anything about running it fails - never raises.
    """

    nvidia_smi = shutil.which("nvidia-smi")

    if nvidia_smi is None:
        return []

    try:
        result = subprocess.run(
            [
                nvidia_smi,
                f"--query-gpu={_NVIDIA_QUERY_FIELDS}",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return []

    gpu_info = []

    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            gpu_info.append(_parse_gpu_line(line))
        except (ValueError, IndexError):
            continue

    return gpu_info


def _parse_rocm_smi_json(raw: str) -> list[dict]:
    """rocm-smi --showproductname --showmeminfo vram --json emits one
    object per card, keyed by card id, e.g.:

        {"card0": {"Card series": "Radeon RX 7900 XTX",
                    "VRAM Total Memory (B)": "25753026560",
                    "VRAM Total Used Memory (B)": "512000000"}}
    """

    data = json.loads(raw)

    gpu_info = []

    for card in data.values():
        if not isinstance(card, dict):
            continue

        try:
            total = int(card["VRAM Total Memory (B)"])
            used = int(card["VRAM Total Used Memory (B)"])
        except (KeyError, ValueError, TypeError):
            continue

        name = (
            card.get("Card series")
            or card.get("Card model")
            or "AMD GPU"
        )

        gpu_info.append({
            "name": name,
            "memory_total_bytes": total,
            "memory_used_bytes": used,
            "memory_free_bytes": max(0, total - used),
            "utilization_percent": 0.0,
        })

    return gpu_info


def _get_amd_gpu_info() -> list[dict]:
    """AMD GPUs, via rocm-smi (ROCm's bundled CLI). Only reports
    anything on machines with the ROCm stack installed - mainly Linux,
    occasionally Windows via AMD's HIP SDK. There is no equally
    reliable way to read live free/used VRAM on a plain Windows+AMD
    setup without ROCm, so that case still falls back to CPU-only.

    Returns [] if rocm-smi isn't on PATH or anything about running or
    parsing it fails - never raises.
    """

    rocm_smi = shutil.which("rocm-smi")

    if rocm_smi is None:
        return []

    try:
        result = subprocess.run(
            [rocm_smi, "--showproductname", "--showmeminfo", "vram", "--json"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return []

    try:
        return _parse_rocm_smi_json(result.stdout)
    except (json.JSONDecodeError, ValueError, AttributeError):
        return []


def _get_apple_silicon_gpu_name() -> str:
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=True,
        )
        displays = json.loads(result.stdout).get("SPDisplaysDataType", [])
        for gpu in displays:
            name = gpu.get("sppci_model") or gpu.get("_name")
            if name:
                return name
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError, ValueError):
        pass

    return "Apple Silicon GPU"


def _get_apple_silicon_gpu_info() -> list[dict]:
    """Apple Silicon (M1/M2/M3/...) has no discrete VRAM - the GPU uses
    unified memory shared with the CPU, so "GPU memory" here is just
    system RAM. is_unified_memory=True tells callers that combine GPU
    and RAM capacity (compatibility/memory_planner.py) not to double-
    count it.

    Only applies on macOS running on arm64. Returns [] on Intel Macs
    (discrete/integrated GPU there isn't unified memory in this sense)
    and everywhere else.
    """

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        return []

    memory = psutil.virtual_memory()

    return [{
        "name": _get_apple_silicon_gpu_name(),
        "memory_total_bytes": memory.total,
        "memory_used_bytes": memory.used,
        "memory_free_bytes": memory.available,
        "utilization_percent": 0.0,
        "is_unified_memory": True,
    }]


def get_gpu_info() -> list[dict]:
    """Detect GPUs across vendors. Each detector degrades to [] on its
    own (missing tool, wrong platform, unexpected output) rather than
    raising, so a machine with none of these - or a GPU we don't
    recognize yet - just falls back to CPU-only mode.
    """

    return [
        *_get_nvidia_gpu_info(),
        *_get_amd_gpu_info(),
        *_get_apple_silicon_gpu_info(),
    ]
