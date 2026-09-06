from .cpu import get_cpu_info
from .memory import get_memory_info
from .os import get_os_info
from .gpu import get_gpu_info

from canirunllm.models.hardware import (
    HardwareProfile,
    CPUInfo,
    MemoryInfo,
    GPUInfo,
    OSInfo,
)


def scan_hardware() -> HardwareProfile:

    cpu_data = get_cpu_info()
    memory_data = get_memory_info()
    os_data = get_os_info()
    gpu_data = get_gpu_info()

    cpu = CPUInfo(**cpu_data)

    memory = MemoryInfo(**memory_data)

    os_info = OSInfo(**os_data)

    gpus = [
        GPUInfo(**gpu)
        for gpu in gpu_data
    ]

    return HardwareProfile(
        cpu=cpu,
        memory=memory,
        os=os_info,
        gpus=gpus,
    )