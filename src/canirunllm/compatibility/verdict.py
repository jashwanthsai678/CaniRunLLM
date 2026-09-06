from enum import Enum


class MemoryVerdict(str, Enum):
    FIT = "FIT"
    MULTI_GPU = "MULTI_GPU"
    CPU_OFFLOAD = "CPU_OFFLOAD"
    NO_FIT = "NO_FIT"
