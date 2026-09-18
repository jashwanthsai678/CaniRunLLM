import json
import subprocess
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from canirunllm.backends.interface import DownloadStatus, ModelNotDownloadableError
from canirunllm.backends.llama_cpp import (
    GatedRepositoryError,
    InsufficientDiskSpaceError,
    LlamaCppBackend,
    LlamaServerNotFoundError,
)
from canirunllm.registry.models import get_known_models


def _get_model(name: str):
    return next(m for m in get_known_models() if m.name == name)


def _backend(tmp_path):
    return LlamaCppBackend(models_dir=tmp_path)


def test_repo_for_known_family(tmp_path):
    backend = _backend(tmp_path)
    assert backend.repo_for(_get_model("Qwen3-8B-Q4_K_M")) == "Qwen/Qwen3-8B-GGUF"


def test_supports_true_for_every_registry_family(tmp_path):
    backend = _backend(tmp_path)
    assert all(backend.supports(m) for m in get_known_models())


def test_is_available_false_when_no_binary_configured(tmp_path, monkeypatch):
    monkeypatch.delenv("LLAMA_SERVER_PATH", raising=False)
    with patch("shutil.which", return_value=None):
        assert _backend(tmp_path).is_available() is False


def test_is_available_true_when_env_var_points_at_real_file(tmp_path, monkeypatch):
    fake_binary = tmp_path / "llama-server.exe"
    fake_binary.write_text("not a real binary")
    monkeypatch.setenv("LLAMA_SERVER_PATH", str(fake_binary))

    assert _backend(tmp_path).is_available() is True


def test_download_raises_without_verified_repo(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    with patch.object(backend, "repo_for", return_value=None):
        with pytest.raises(ModelNotDownloadableError):
            list(backend.download(model))


def test_resolve_filename_raises_when_no_quant_match(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    fake_tree = [{"path": "README.md"}, {"path": "config.json"}]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(fake_tree).encode()

        with pytest.raises(ModelNotDownloadableError):
            backend._resolve_filename("Qwen/Qwen3-8B-GGUF", model)


def test_resolve_filename_raises_gated_error_on_401(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        "url", 401, "unauthorized", {}, None
    )):
        with pytest.raises(GatedRepositoryError):
            backend._resolve_filename("Qwen/Qwen3-8B-GGUF", model)


def test_download_raises_when_insufficient_disk_space(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    tree = [{"path": "Qwen3-8B-Q4_K_M.gguf", "size": 5_000_000_000}]

    with patch("urllib.request.urlopen") as mock_urlopen, \
         patch("canirunllm.backends.llama_cpp.get_disk_info", return_value={
             "total_bytes": 10_000_000_000, "free_bytes": 1_000_000_000, "used_bytes": 9_000_000_000,
         }):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(tree).encode()

        with pytest.raises(InsufficientDiskSpaceError):
            list(backend.download(model))


def test_download_skips_when_file_already_complete(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    family_dir = tmp_path / model.family
    family_dir.mkdir(parents=True)
    existing = family_dir / "Qwen3-8B-Q4_K_M.gguf"
    existing.write_bytes(b"x" * 10)

    tree = [{"path": "Qwen3-8B-Q4_K_M.gguf", "size": 10}]

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(tree).encode()

        events = list(backend.download(model))

    assert len(events) == 1
    assert events[0].status == DownloadStatus.COMPLETE
    assert events[0].message == "Already downloaded."


def test_download_writes_file_and_reports_progress(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    tree = [{"path": "Qwen3-8B-Q4_K_M.gguf", "size": 20}]
    file_bytes = [b"0123456789", b"0123456789", b""]

    tree_response = MagicMock()
    tree_response.read.return_value = json.dumps(tree).encode()

    download_response = MagicMock()
    download_response.read.side_effect = file_bytes

    with patch("urllib.request.urlopen") as mock_urlopen, \
         patch("canirunllm.backends.llama_cpp.get_disk_info", return_value={
             "total_bytes": 10_000_000_000, "free_bytes": 9_000_000_000, "used_bytes": 1_000_000_000,
         }):
        mock_urlopen.return_value.__enter__.side_effect = [tree_response, download_response]

        events = list(backend.download(model))

    destination = tmp_path / model.family / "Qwen3-8B-Q4_K_M.gguf"
    assert destination.read_bytes() == b"01234567890123456789"
    assert events[-1].status == DownloadStatus.COMPLETE
    assert events[-1].bytes_downloaded == 20


def test_serve_raises_when_binary_not_found(tmp_path, monkeypatch):
    monkeypatch.delenv("LLAMA_SERVER_PATH", raising=False)
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    with patch("shutil.which", return_value=None):
        with pytest.raises(LlamaServerNotFoundError):
            backend.serve(model)


def test_serve_raises_when_not_downloaded_yet(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    with patch("shutil.which", return_value="/usr/bin/llama-server"):
        with pytest.raises(ModelNotDownloadableError):
            backend.serve(model)


def test_serve_starts_process_and_waits_for_health(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    family_dir = tmp_path / model.family
    family_dir.mkdir(parents=True)
    (family_dir / "Qwen3-8B-Q4_K_M.gguf").write_bytes(b"fake")

    fake_process = MagicMock()
    fake_process.poll.return_value = None

    with patch("shutil.which", return_value="/usr/bin/llama-server"), \
         patch("subprocess.Popen", return_value=fake_process), \
         patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = MagicMock()

        url = backend.serve(model)

    assert url.startswith("http://127.0.0.1:")
    backend.stop()


def test_serve_raises_and_cleans_up_when_process_exits_early(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    family_dir = tmp_path / model.family
    family_dir.mkdir(parents=True)
    (family_dir / "Qwen3-8B-Q4_K_M.gguf").write_bytes(b"fake")

    fake_process = MagicMock()
    fake_process.poll.return_value = 1
    fake_process.returncode = 1

    with patch("shutil.which", return_value="/usr/bin/llama-server"), \
         patch("subprocess.Popen", return_value=fake_process):
        with pytest.raises(RuntimeError, match="exited early"):
            backend.serve(model)


def test_chat_raises_when_nothing_running(tmp_path):
    backend = _backend(tmp_path)
    model = _get_model("Qwen3-8B-Q4_K_M")

    with pytest.raises(RuntimeError, match="isn't running"):
        backend.chat(model, "hello")


def test_stop_terminates_running_process(tmp_path):
    backend = _backend(tmp_path)
    fake_process = MagicMock()
    fake_process.poll.return_value = None
    backend._process = fake_process
    backend._port = 1234

    backend.stop()

    fake_process.terminate.assert_called_once()
    assert backend._process is None
    assert backend._port is None
