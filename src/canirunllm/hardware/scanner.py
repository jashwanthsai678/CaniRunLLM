from .cpu import get_cpu_info
from .memory import get_memory_info
from .os import get_os_info

def scan_hardware():
    return {
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "os": get_os_info(),
    }