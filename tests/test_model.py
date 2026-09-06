from canirunllm.models.model import ModelSpec


def test_model_spec():

    model = ModelSpec(
        name="Qwen3-27B-Q4_K_M",
        family="Qwen3-27B",
        parameters=27_000_000_000,
        architecture="Qwen",
        quantization="Q4_K_M",
        context_length=32768,
        file_size_bytes=16_000_000_000,
        runtime="llama.cpp",
    )

    assert model.name == "Qwen3-27B-Q4_K_M"
    assert model.family == "Qwen3-27B"
    assert model.parameters == 27_000_000_000
    assert model.quantization == "Q4_K_M"

    assert (
        model.identifier
        == "Qwen3-27B:Q4_K_M:llama.cpp"
    )
