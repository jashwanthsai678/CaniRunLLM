from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.kv_cache import (
    estimate_kv_cache_memory,
)


def test_kv_cache_estimate():

    model = ModelSpec(
        name="Test",
        family="Test",
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
        num_layers=32,
        num_kv_heads=8,
        head_dim=128,
        kv_cache_dtype_bits=16,
    )

    result = estimate_kv_cache_memory(model)

    expected = int(
        2
        * 32
        * 8
        * 128
        * 8192
        * 2
    )

    assert result == expected
