from canirunllm.models.model import ModelSpec
from canirunllm.compatibility.memory import estimate_weight_memory


def test_q4_memory_estimate():

    model = ModelSpec(
        name="Test-7B",
        family="Test-7B",
        parameters=7_000_000_000,
        architecture="Test",
        quantization="Q4",
        context_length=8192,
    )

    memory = estimate_weight_memory(model)

    expected = (
        7_000_000_000 * 4
    ) // 8

    assert memory == expected
