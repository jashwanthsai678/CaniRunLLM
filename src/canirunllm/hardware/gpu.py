import shutil
import subprocess

_QUERY_FIELDS = "name,memory.total,memory.used,memory.free,utilization.gpu"
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


def get_gpu_info() -> list[dict]:
    """NVIDIA-only, via nvidia-smi directly - no third-party GPU library
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
    anything about running it fails - never raises, so a machine
    without an NVIDIA GPU degrades to "no GPU detected" instead of
    crashing the whole scan.
    """

    nvidia_smi = shutil.which("nvidia-smi")

    if nvidia_smi is None:
        return []

    try:
        result = subprocess.run(
            [
                nvidia_smi,
                f"--query-gpu={_QUERY_FIELDS}",
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
