from canirunllm.models.resolver import ModelResolver


def test_resolve_all_returns_known_models():

    resolver = ModelResolver()

    models = resolver.resolve_all()

    assert len(models) > 0


def test_resolver_search():

    resolver = ModelResolver()

    results = resolver.search("qwen")

    assert len(results) > 0

    for model in results:
        assert "qwen" in model.name.lower()


def test_search_no_match_returns_empty():

    resolver = ModelResolver()

    results = resolver.search("nonexistent-model-xyz")

    assert results == []


def test_get_by_family():

    resolver = ModelResolver()

    results = resolver.get_by_family(
        "Qwen3-27B"
    )

    assert len(results) > 0

    for model in results:
        assert model.family == "Qwen3-27B"


def test_get_by_family_no_match_returns_empty():

    resolver = ModelResolver()

    results = resolver.get_by_family("nonexistent-family")

    assert results == []


def test_get_variant():

    resolver = ModelResolver()

    model = resolver.get_variant(
        "Qwen3-27B-Q4_K_M"
    )

    assert model is not None
    assert model.name == "Qwen3-27B-Q4_K_M"


def test_get_variant_is_case_insensitive():

    resolver = ModelResolver()

    model = resolver.get_variant("qwen3-27b-q4_k_m")

    assert model is not None
    assert model.name == "Qwen3-27B-Q4_K_M"


def test_get_variant_does_not_match_family_only():

    resolver = ModelResolver()

    model = resolver.get_variant("qwen3-27b")

    assert model is None
