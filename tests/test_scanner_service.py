from canirunllm.application.scanner_service import ScannerService
from canirunllm.models.hardware import HardwareProfile
from canirunllm.models.results import ModelCheckResult
from canirunllm.recommendation.engine import RankedModel


def test_scan_returns_hardware_and_results():

    service = ScannerService()

    hardware, results = service.scan()

    assert isinstance(hardware, HardwareProfile)
    assert len(results) > 0

    for item in results:
        assert isinstance(item, ModelCheckResult)
        assert item.model is not None
        assert item.compatibility is not None


def test_recommend_returns_hardware_and_ranked_models():

    service = ScannerService()

    hardware, ranked = service.recommend()

    assert isinstance(hardware, HardwareProfile)
    assert len(ranked) > 0

    for entry in ranked:
        assert isinstance(entry, RankedModel)
        assert 1 <= entry.stars <= 5

    tier_positions = [
        entry.tier for entry in ranked
    ]

    # Ranked output should be grouped by tier order, never scrambled.
    from canirunllm.recommendation.tier import TIER_ORDER

    orders = [TIER_ORDER[tier] for tier in tier_positions]
    assert orders == sorted(orders)


def test_search_returns_matching_models():

    service = ScannerService()

    models = service.search("qwen")

    assert len(models) > 0

    for model in models:
        assert "qwen" in model.name.lower()


def test_check_variant_returns_single_model():

    service = ScannerService()

    outcome = service.check("Qwen3-32B-Q4_K_M")

    assert outcome is not None
    assert outcome["type"] == "variant"
    assert len(outcome["models"]) == 1
    assert outcome["models"][0].model.name == "Qwen3-32B-Q4_K_M"


def test_check_family_returns_all_variants():

    service = ScannerService()

    outcome = service.check("Qwen3-32B")

    assert outcome is not None
    assert outcome["type"] == "family"
    assert len(outcome["models"]) > 0

    for item in outcome["models"]:
        assert item.model.family == "Qwen3-32B"


def test_check_unknown_returns_none():

    service = ScannerService()

    outcome = service.check("nonexistent-model-xyz")

    assert outcome is None
