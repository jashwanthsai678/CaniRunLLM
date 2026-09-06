import platform
import psutil


def get_cpu_info():
    return {
        "name": platform.processor(),
        "architecture": platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "frequency_mhz": psutil.cpu_freq().current
        if psutil.cpu_freq() else None,
    }