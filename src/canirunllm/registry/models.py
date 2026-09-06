from canirunllm.models.model import ModelSpec


def get_known_models() -> list[ModelSpec]:

    return [

        ModelSpec(
            name="Qwen3-27B-Q4_K_M",
            family="Qwen3-27B",
            parameters=27_000_000_000,
            architecture="Qwen",
            quantization="Q4_K_M",
            context_length=32768,
            runtime="llama.cpp",
            num_layers=64,
            num_kv_heads=4,
            head_dim=128,
        ),

        ModelSpec(
            name="Qwen3-27B-Q8",
            family="Qwen3-27B",
            parameters=27_000_000_000,
            architecture="Qwen",
            quantization="Q8",
            context_length=32768,
            runtime="llama.cpp",
            num_layers=64,
            num_kv_heads=4,
            head_dim=128,
        ),

        ModelSpec(
            name="Qwen3-8B-Q4_K_M",
            family="Qwen3-8B",
            parameters=8_000_000_000,
            architecture="Qwen",
            quantization="Q4_K_M",
            context_length=32768,
            runtime="llama.cpp",
            num_layers=36,
            num_kv_heads=8,
            head_dim=128,
        ),

        ModelSpec(
            name="Qwen3-8B-Q8",
            family="Qwen3-8B",
            parameters=8_000_000_000,
            architecture="Qwen",
            quantization="Q8",
            context_length=32768,
            runtime="llama.cpp",
            num_layers=36,
            num_kv_heads=8,
            head_dim=128,
        ),
    ]
