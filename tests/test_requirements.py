from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.config import MemoryConfig
from canirunllm.compatibility.requirements import (
    estimate_memory_requirement,
)


def test_total_memory_includes_overhead_and_margin():

    model = ModelSpec(
        name="Test-7B",
        family="Test-7B",
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
        num_layers=32,
        num_kv_heads=8,
        head_dim=128,
    )

    config = MemoryConfig(
        runtime_overhead_percent=10.0,
        safety_margin_percent=10.0,
    )

    result = estimate_memory_requirement(model, config)

    weights = (7_000_000_000 * 4) // 8
    kv_cache = int(2 * 32 * 8 * 128 * 8192 * 2)
    runtime_overhead = int((weights + kv_cache) * 0.10)
    subtotal = weights + kv_cache + runtime_overhead
    safety_margin = int(subtotal * 0.10)
    total = subtotal + safety_margin

    assert result.weight_memory_bytes == weights
    assert result.kv_cache_bytes == kv_cache
    assert result.runtime_overhead_bytes == runtime_overhead
    assert result.safety_margin_bytes == safety_margin
    assert result.total_required_bytes == total
