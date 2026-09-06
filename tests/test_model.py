from canirunllm.models.model import ModelSpec


def test_model_spec():

    model = ModelSpec(
        name="Qwen3-32B-Q4_K_M",
        family="Qwen3-32B",
        parameters=32_800_000_000,
        architecture="Qwen3",
        quantization="Q4_K_M",
        context_length=32768,
        file_size_bytes=21_260_088_115,
        runtime="llama.cpp",
    )

    assert model.name == "Qwen3-32B-Q4_K_M"
    assert model.family == "Qwen3-32B"
    assert model.parameters == 32_800_000_000
    assert model.quantization == "Q4_K_M"

    assert (
        model.identifier
        == "Qwen3-32B:Q4_K_M:llama.cpp"
    )
