from dataclasses import dataclass, field


@dataclass
class CPUInfo:
    name: str
    architecture: str
    physical_cores: int | None
    logical_cores: int | None
    frequency_mhz: float | None


@dataclass
class MemoryInfo:
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float


@dataclass
class GPUInfo:
    name: str
    memory_total_bytes: int
    memory_used_bytes: int
    memory_free_bytes: int
    utilization_percent: float
    # True on Apple Silicon: the GPU has no VRAM of its own, it shares
    # system RAM. Callers that combine GPU and RAM capacity (see
    # compatibility/memory_planner.py) must not count this GPU's memory
    # on top of RAM - it's the same physical pool.
    is_unified_memory: bool = False


@dataclass
class OSInfo:
    system: str
    release: str
    version: str
    machine: str


@dataclass
class DiskInfo:
    total_bytes: int
    free_bytes: int
    used_bytes: int


@dataclass
class HardwareProfile:
    cpu: CPUInfo
    memory: MemoryInfo
    os: OSInfo
    gpus: list[GPUInfo] = field(default_factory=list)
    # Free disk space where downloaded model files would land - optional
    # so existing callers/tests that only care about RAM/VRAM don't need
    # to supply it. See hardware/disk.py.
    disk: DiskInfo | None = None