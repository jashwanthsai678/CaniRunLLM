from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from canirunllm.api.server import app, _ollama_backend
from canirunllm.backends.ollama_tags import OLLAMA_TAGS
from canirunllm.backends.state import runtime_state
from canirunllm.registry.models import get_known_models


client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_runtime_state():
    """runtime_state is a module-level singleton - never let one test's
    "running model" leak into the next."""
    runtime_state.clear()
    yield
    runtime_state.clear()


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


def test_models_include_performance_prediction():

    response = client.get("/api/models")
    data = response.json()

    for entry in data:

        performance = entry["performance"]

        assert performance["confidence"] in ("HIGH", "MEDIUM", "LOW")
        assert performance["source"] == "MODELLED_ESTIMATE"
        assert len(performance["explanation"]) > 0

        if entry["compatibility"]["overall_verdict"] == "CANNOT_RUN":
            assert performance["generation_speed"] is None
        else:
            speed = performance["generation_speed"]
            assert speed is not None
            assert speed["low"] > 0
            assert speed["high"] >= speed["low"]
            assert speed["unit"] == "tok/s"


def test_scan_best_for_you_and_recommended_include_performance():

    response = client.get("/api/scan")
    data = response.json()

    if data["best_for_you"] is not None:
        assert "performance" in data["best_for_you"]

    for entry in data["recommended"]:
        assert "performance" in entry


def test_model_detail_includes_performance():

    known_models = get_known_models()
    target = known_models[0]

    response = client.get(f"/api/models/{target.name}")
    data = response.json()

    assert "performance" in data
    assert data["performance"]["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_compatibility_includes_friendly_language():

    response = client.get("/api/models")
    data = response.json()

    for entry in data:
        compat = entry["compatibility"]
        assert compat["friendly_verdict"]
        assert compat["friendly_icon"] in {"check", "warn", "unknown", "cross"}
        assert isinstance(compat["reasons"], list)
        assert len(compat["reasons"]) > 0
        for reason in compat["reasons"]:
            assert "ok" in reason
            assert reason["text"]


def test_scan_best_for_you_is_consistent_with_summary():

    response = client.get("/api/scan")
    data = response.json()

    best = data["best_for_you"]
    favorable_total = (
        data["summary"]["can_run"] + data["summary"]["can_run_with_offload"]
    )

    if favorable_total == 0:
        assert best is None
    else:
        assert best is not None
        assert best["compatibility"]["overall_verdict"] in (
            "CAN_RUN",
            "CAN_RUN_WITH_OFFLOAD",
        )


def test_model_detail_run_commands_present_for_llama_cpp_models():

    known_models = get_known_models()
    llama_cpp_model = next(m for m in known_models if m.runtime == "llama.cpp")

    response = client.get(f"/api/models/{llama_cpp_model.name}")
    data = response.json()

    runtimes = [c["runtime"] for c in data["run_commands"]]

    assert "llama.cpp" in runtimes
    assert "Ollama" in runtimes

    llama_cpp_entry = next(
        c for c in data["run_commands"] if c["runtime"] == "llama.cpp"
    )
    assert llama_cpp_model.name in llama_cpp_entry["command"]


def test_model_detail_ollama_uses_verified_tag_for_known_model():

    response = client.get("/api/models/Qwen3-8B-Q4_K_M")
    data = response.json()

    ollama_entry = next(c for c in data["run_commands"] if c["runtime"] == "Ollama")

    assert ollama_entry["command"] == "ollama run qwen3:8b-q4_K_M"
    assert data["ollama_downloadable"] is True


def test_model_detail_ollama_downloadable_false_without_verified_tag():

    known_models = get_known_models()
    model_without_tag = next(m for m in known_models if m.name not in OLLAMA_TAGS)

    response = client.get(f"/api/models/{model_without_tag.name}")

    assert response.json()["ollama_downloadable"] is False


def test_model_detail_llama_cpp_downloadable_true_for_every_registry_family():
    """llama_cpp_sources.py has a verified GGUF repo for every family
    in models.json (checked directly against registry/SOURCES.md's own
    citations) - unlike Ollama's partial, hand-curated tag coverage."""

    for model in get_known_models():
        response = client.get(f"/api/models/{model.name}")
        assert response.json()["llama_cpp_downloadable"] is True, model.name


def test_model_detail_alternative_only_present_when_cannot_run():

    known_models = get_known_models()

    for model in known_models:

        response = client.get(f"/api/models/{model.name}")
        data = response.json()

        if data["compatibility"]["overall_verdict"] != "CANNOT_RUN":
            assert data["alternative"] is None


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


def test_hardware_includes_disk():

    response = client.get("/api/hardware")
    data = response.json()

    assert data["disk"]["total_bytes"] > 0


def test_download_unknown_model_returns_404():

    response = client.post("/api/models/does-not-exist/download")

    assert response.status_code == 404


def test_download_model_without_ollama_tag_falls_back_to_llama_cpp_backend():

    known_models = get_known_models()
    model_without_tag = next(
        m for m in known_models
        if m.name not in OLLAMA_TAGS
    )

    response = client.post(f"/api/models/{model_without_tag.name}/download")

    # llama.cpp backend covers every registry family (see
    # llama_cpp_sources.py), so this now falls through to it instead of
    # a flat 400 - it's just unavailable in this test environment.
    assert response.status_code == 503


def test_download_with_explicit_backend_that_does_not_support_model_returns_400():

    known_models = get_known_models()
    model_without_tag = next(
        m for m in known_models
        if m.name not in OLLAMA_TAGS
    )

    response = client.post(f"/api/models/{model_without_tag.name}/download?backend=ollama")

    assert response.status_code == 400
    assert "doesn't support backend" in response.json()["detail"]


def test_download_when_ollama_not_running_returns_503():

    with patch.object(_ollama_backend, "is_available", return_value=False):
        response = client.post("/api/models/Qwen3-8B-Q4_K_M/download?backend=ollama")

    assert response.status_code == 503


def test_runtime_status_reports_nothing_running_by_default():

    response = client.get("/api/runtime/status")

    assert response.status_code == 200
    assert response.json() == {
        "running": False,
        "model_name": None,
        "backend_name": None,
        "endpoint_url": None,
    }


def test_stop_when_nothing_running_reports_false():

    response = client.post("/api/runtime/stop")

    assert response.status_code == 200
    assert response.json() == {"stopped": False}


def test_stop_when_something_running_calls_backend_stop_and_clears_state():

    from canirunllm.backends.state import RunningModel

    runtime_state.set(RunningModel(
        model_name="Qwen3-8B-Q4_K_M",
        backend_name="ollama",
        endpoint_url="http://127.0.0.1:11434",
    ))

    with patch.object(_ollama_backend, "stop") as mock_stop:
        response = client.post("/api/runtime/stop")

    assert response.status_code == 200
    assert response.json() == {"stopped": True}
    mock_stop.assert_called_once()
    assert runtime_state.get() is None


def test_model_detail_includes_backend_availability_flags():

    response = client.get("/api/models/Qwen3-8B-Q4_K_M")
    data = response.json()

    assert "ollama_available" in data
    assert "llama_cpp_available" in data
    assert isinstance(data["ollama_available"], bool)
    assert isinstance(data["llama_cpp_available"], bool)


def test_chat_says_no_runtime_when_no_backend_available():

    with patch.object(_ollama_backend, "is_available", return_value=False):
        response = client.post(
            "/api/chat",
            json={"model_name": "Qwen3-8B-Q4_K_M", "message": "hello"},
        )

    assert response.status_code == 200
    assert "No model runtime is available" in response.json()["reply"]


def test_chat_says_model_not_running_when_backend_available_but_nothing_running():

    with patch.object(_ollama_backend, "is_available", return_value=True):
        response = client.post(
            "/api/chat",
            json={"model_name": "Qwen3-8B-Q4_K_M", "message": "hello"},
        )

    assert response.status_code == 200
    assert "isn't running yet" in response.json()["reply"]


def test_chat_routes_to_backend_when_matching_model_is_running():

    from canirunllm.backends.state import RunningModel

    runtime_state.set(RunningModel(
        model_name="Qwen3-8B-Q4_K_M",
        backend_name="ollama",
        endpoint_url="http://127.0.0.1:11434",
    ))

    with patch.object(_ollama_backend, "chat", return_value="a real reply") as mock_chat:
        response = client.post(
            "/api/chat",
            json={"model_name": "Qwen3-8B-Q4_K_M", "message": "hello"},
        )

    assert response.status_code == 200
    assert response.json()["reply"] == "a real reply"
    mock_chat.assert_called_once()
