import shutil
from pathlib import Path


def get_disk_info(path: Path | None = None) -> dict:
    """Free/total disk space for the volume containing `path`.

    Defaults to the user's home directory - a stable, always-existing
    location standing in for where downloaded model files will
    eventually live. Once a real models directory exists (Phase 2 of
    ROADMAP.md), this should be pointed at that directory instead.
    """

    target = path or Path.home()

    usage = shutil.disk_usage(target)

    return {
        "total_bytes": usage.total,
        "free_bytes": usage.free,
        "used_bytes": usage.used,
    }
