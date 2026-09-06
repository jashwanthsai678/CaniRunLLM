import psutil


def get_memory_info():
    memory = psutil.virtual_memory()

    return {
        "total_bytes": memory.total,
        "available_bytes": memory.available,
        "used_bytes": memory.used,
        "usage_percent": memory.percent,
    }