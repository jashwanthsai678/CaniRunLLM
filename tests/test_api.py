from fastapi.testclient import TestClient

from canirunllm.api.server import app
from canirunllm.registry.models import get_known_models


client = TestClient(app)


def test_health():

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hardware_returns_valid_schema():

    response = client.get("/api/hardware")

    assert response.status_code == 200

    data = response.json()

    assert "cpu" in data
    assert "memory" in data
    assert "os" in data
    assert "gpus" in data
    assert isinstance(data["gpus"], list)

    assert data["cpu"]["name"]
    assert data["memory"]["total_bytes"] > 0


def test_models_returns_every_registry_entry():

    response = client.get("/api/models")

    assert response.status_code == 200

    data = response.json()
    known_models = get_known_models()

    assert len(data) == len(known_models)

    for entry in data:
        assert "model" in entry
        assert "compatibility" in entry
        assert entry["compatibility"]["overall_verdict"] in (
            "CAN_RUN",
            "CAN_RUN_WITH_OFFLOAD",
            "NEEDS_VALIDATION",
            "CANNOT_RUN",
        )


def test_scan_returns_hardware_summary_and_results():

    response = client.get("/api/scan")

    assert response.status_code == 200

    data = response.json()

    assert "hardware" in data
    assert "summary" in data
    assert "results" in data
    assert "recommended" in data
    assert "scanned_at" in data

    known_models = get_known_models()

    assert data["summary"]["total"] == len(known_models)
    assert len(data["results"]) == len(known_models)

    summary = data["summary"]
    assert (
        summary["can_run"]
        + summary["can_run_with_offload"]
        + summary["needs_validation"]
        + summary["cannot_run"]
        == summary["total"]
    )


def test_scan_recommended_only_contains_favorable_tiers():

    response = client.get("/api/scan")
    data = response.json()

    recommended_names = {entry["model"]["name"] for entry in data["recommended"]}

    favorable_verdicts = {"CAN_RUN", "CAN_RUN_WITH_OFFLOAD"}

    for entry in data["results"]:
        if entry["model"]["name"] in recommended_names:
            assert entry["compatibility"]["overall_verdict"] in favorable_verdicts


def test_model_detail_known_model():

    known_models = get_known_models()
    target = known_models[0]

    response = client.get(f"/api/models/{target.name}")

    assert response.status_code == 200

    data = response.json()

    assert data["model"]["name"] == target.name
    assert "memory_breakdown" in data
    assert data["memory_breakdown"]["total_required_bytes"] > 0
    assert (
        data["memory_breakdown"]["weight_memory_bytes"]
        + data["memory_breakdown"]["kv_cache_bytes"]
        + data["memory_breakdown"]["runtime_overhead_bytes"]
        + data["memory_breakdown"]["safety_margin_bytes"]
        == data["memory_breakdown"]["total_required_bytes"]
    )


def test_model_detail_unknown_model_returns_404():

    response = client.get("/api/models/does-not-exist-anywhere")

    assert response.status_code == 404


def test_index_serves_html():

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "CanIRunLLM" in response.text


def test_static_files_are_served():

    response = client.get("/static/style.css")

    assert response.status_code == 200

    response = client.get("/static/app.js")

    assert response.status_code == 200
