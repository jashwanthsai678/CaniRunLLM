from canirunllm.registry.models import get_known_models


def test_known_models():

    models = get_known_models()

    assert len(models) > 0

    for model in models:

        assert model.name
        assert model.family
        assert model.parameters > 0
        assert model.quantization
        assert model.context_length > 0
