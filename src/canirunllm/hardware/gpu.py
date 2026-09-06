import GPUtil


def get_gpu_info():
    gpus = GPUtil.getGPUs()

    if not gpus:
        return []

    gpu_info = []

    for gpu in gpus:
        gpu_info.append(
            {
                "name": gpu.name,
                "memory_total_bytes": int(gpu.memoryTotal * 1024 * 1024),
                "memory_used_bytes": int(gpu.memoryUsed * 1024 * 1024),
                "memory_free_bytes": int(gpu.memoryFree * 1024 * 1024),
                "utilization_percent": gpu.load * 100,
            }
        )

    return gpu_info