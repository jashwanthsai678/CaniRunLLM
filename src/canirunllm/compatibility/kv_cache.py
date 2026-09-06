from canirunllm.models.model import ModelSpec


def estimate_kv_cache_memory(
    model: ModelSpec,
) -> int:

    if (
        model.num_layers is None
        or model.num_kv_heads is None
        or model.head_dim is None
    ):
        raise ValueError(
            "Model architecture information is required "
            "to estimate KV cache."
        )

    bytes_per_value = (
        model.kv_cache_dtype_bits / 8
    )

    return int(
        2
        * model.num_layers
        * model.num_kv_heads
        * model.head_dim
        * model.context_length
        * bytes_per_value
    )
