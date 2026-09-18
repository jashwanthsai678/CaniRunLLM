import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from canirunllm.backends.interface import DownloadStatus
from canirunllm.backends.ollama import ModelNotDownloadableError, OllamaBackend
from canirunllm.registry.models import get_known_models


def _get_model(name: str):
    return next(m for m in get_known_models() if m.name == name)


def test_tag_for_known_model():
    backend = OllamaBackend()
    assert backend.tag_for(_get_model("Qwen3-8B-Q4_K_M")) == "qwen3:8b-q4_K_M"


def test_tag_for_unknown_model_is_none():
    backend = OllamaBackend()
    model = next(m for m in get_known_models() if backend.tag_for(m) is None)
    assert backend.tag_for(model) is None


def test_is_available_true_on_200():
    backend = OllamaBackend()
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = MagicMock()
        assert backend.is_available() is True


def test_is_available_false_on_connection_error():
    backend = OllamaBackend()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        assert backend.is_available() is False


def test_download_raises_without_verified_tag():
    backend = OllamaBackend()
    model = next(m for m in get_known_models() if backend.tag_for(m) is None)

    with pytest.raises(ModelNotDownloadableError):
        list(backend.download(model))


def test_download_yields_progress_and_completion():
    backend = OllamaBackend()
    model = _get_model("Qwen3-8B-Q4_K_M")

    lines = [
        json.dumps({"status": "pulling manifest", "completed": 0, "total": 100}),
        json.dumps({"status": "downloading", "completed": 50, "total": 100}),
        json.dumps({"status": "success", "completed": 100, "total": 100}),
    ]
    fake_response = MagicMock()
    fake_response.__iter__.return_value = iter(line.encode("utf-8") for line in lines)

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response

        progress_events = list(backend.download(model))

    assert len(progress_events) == 3
    assert progress_events[0].status == DownloadStatus.DOWNLOADING
    assert progress_events[-1].status == DownloadStatus.COMPLETE
    assert progress_events[-1].bytes_downloaded == 100


def test_download_raises_on_ollama_error_payload():
    backend = OllamaBackend()
    model = _get_model("Qwen3-8B-Q4_K_M")

    fake_response = MagicMock()
    fake_response.__iter__.return_value = iter(
        [json.dumps({"error": "model not found"}).encode("utf-8")]
    )

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response

        with pytest.raises(RuntimeError, match="model not found"):
            list(backend.download(model))


def test_serve_raises_without_verified_tag():
    backend = OllamaBackend()
    model = next(m for m in get_known_models() if backend.tag_for(m) is None)

    with pytest.raises(ModelNotDownloadableError):
        backend.serve(model)


def test_serve_returns_base_url_for_known_model():
    backend = OllamaBackend()
    assert backend.serve(_get_model("Qwen3-8B-Q4_K_M")) == "http://127.0.0.1:11434"


def test_chat_sends_verified_tag_and_returns_reply():
    backend = OllamaBackend()
    model = _get_model("Qwen3-8B-Q4_K_M")

    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({
        "message": {"role": "assistant", "content": "hi there"}
    }).encode("utf-8")

    with patch("urllib.request.urlopen") as mock_urlopen, \
         patch("urllib.request.Request") as mock_request:
        mock_urlopen.return_value.__enter__.return_value = fake_response

        reply = backend.chat(model, "hello")

        sent_body = json.loads(mock_request.call_args.kwargs["data"])
        assert sent_body["model"] == "qwen3:8b-q4_K_M"

    assert reply == "hi there"
