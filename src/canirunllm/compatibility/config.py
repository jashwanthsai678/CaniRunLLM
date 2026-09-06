from dataclasses import dataclass


@dataclass
class MemoryConfig:
    runtime_overhead_percent: float = 10.0
    safety_margin_percent: float = 10.0
