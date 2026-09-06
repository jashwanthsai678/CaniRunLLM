from dataclasses import dataclass

from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.memory import estimate_weight_memory
from canirunllm.compatibility.kv_cache import estimate_kv_cache_memory
from canirunllm.compatibility.config import MemoryConfig


@dataclass
class MemoryRequirement:
    weight_memory_bytes: int
    kv_cache_bytes: int
    runtime_overhead_bytes: int
    safety_margin_bytes: int
    total_required_bytes: int


def estimate_memory_requirement(
    model: ModelSpec,
    config: MemoryConfig | None = None,
) -> MemoryRequirement:

    if config is None:
        config = MemoryConfig()

    weights = estimate_weight_memory(model)

    kv_cache = estimate_kv_cache_memory(model)

    runtime_overhead = int(
        (weights + kv_cache)
        * config.runtime_overhead_percent
        / 100
    )

    subtotal = (
        weights
        + kv_cache
        + runtime_overhead
    )

    safety_margin = int(
        subtotal
        * config.safety_margin_percent
        / 100
    )

    total = (
        subtotal
        + safety_margin
    )

    return MemoryRequirement(
        weight_memory_bytes=weights,
        kv_cache_bytes=kv_cache,
        runtime_overhead_bytes=runtime_overhead,
        safety_margin_bytes=safety_margin,
        total_required_bytes=total,
    )
