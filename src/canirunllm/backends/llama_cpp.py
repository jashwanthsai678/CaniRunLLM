"""The direct llama.cpp backend: downloads a model's GGUF file straight
from Hugging Face and spawns a local llama-server process to serve it.

Bigger scope than the Ollama backend (ROADMAP.md Phase 2) - this
backend does for itself what Ollama does internally: resolve the right
file, download it, check disk space, and supervise a server process.

Requires llama-server already installed (on PATH, or pointed to via
the LLAMA_SERVER_PATH environment variable). Bundling a binary
ourselves is a possible future phase, not this one - see ROADMAP.md.
"""

import atexit
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterator

from canirunllm.backends.interface import (
    Backend,
    DownloadProgress,
    DownloadStatus,
    ModelNotDownloadableError,
)
from canirunllm.backends.llama_cpp_sources import HF_GGUF_REPOS
from canirunllm.hardware.disk import get_disk_info
from canirunllm.models.model import ModelSpec

HF_BASE = "https://huggingface.co"
HF_API = "https://huggingface.co/api"
DEFAULT_MODELS_DIR = Path.home() / ".canirunllm" / "models"

# Require this much headroom beyond the file's own size before starting
# a download - GGUF metadata isn't byte-perfect and llama.cpp needs a
# little scratch space too.
DISK_SAFETY_MARGIN = 1.1

_DOWNLOAD_CHUNK_BYTES = 1024 * 1024
_HEALTH_CHECK_TIMEOUT_SECONDS = 120
_HEALTH_CHECK_POLL_SECONDS = 1


class LlamaServerNotFoundError(Exception):
    pass


class InsufficientDiskSpaceError(Exception):
    pass


class GatedRepositoryError(Exception):
    """Raised on a 401 from a gated HF repo - not automatable without
    the user's own token accepted for that repo's license."""


def _find_llama_server_binary() -> str | None:
    configured = os.environ.get("LLAMA_SERVER_PATH")
    if configured and Path(configured).is_file():
        return configured
    return shutil.which("llama-server")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _hf_headers() -> dict:
    token = os.environ.get("HF_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


class LlamaCppBackend(Backend):
    name = "llama.cpp"

    def __init__(self, models_dir: Path = DEFAULT_MODELS_DIR):
        self._models_dir = models_dir
        self._process: subprocess.Popen | None = None
        self._port: int | None = None
        atexit.register(self.stop)

    def is_available(self) -> bool:
        return _find_llama_server_binary() is not None

    def repo_for(self, model: ModelSpec) -> str | None:
        return HF_GGUF_REPOS.get(model.family)

    def supports(self, model: ModelSpec) -> bool:
        return self.repo_for(model) is not None

    def _resolve_filename(self, repo: str, model: ModelSpec) -> tuple[str, int | None]:
        url = f"{HF_API}/models/{repo}/tree/main"
        request = urllib.request.Request(url, headers=_hf_headers())

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                tree = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise GatedRepositoryError(
                    f"{repo} is gated - set the HF_TOKEN environment "
                    "variable to a token that has accepted its license."
                )
            raise

        quant = model.quantization.lower()

        for entry in tree:
            path = entry.get("path", "")
            if path.lower().endswith(".gguf") and quant in path.lower():
                return path, entry.get("size")

        raise ModelNotDownloadableError(
            f"No {model.quantization} GGUF file found in {repo} for {model.name}."
        )

    def _family_dir(self, model: ModelSpec) -> Path:
        return self._models_dir / model.family

    def _find_local_gguf(self, model: ModelSpec) -> Path | None:
        family_dir = self._family_dir(model)
        if not family_dir.is_dir():
            return None

        quant = model.quantization.lower()
        return next(
            (path for path in family_dir.glob("*.gguf") if quant in path.name.lower()),
            None,
        )

    def download(self, model: ModelSpec) -> Iterator[DownloadProgress]:
        repo = self.repo_for(model)

        if repo is None:
            raise ModelNotDownloadableError(
                f"No verified GGUF repo for {model.family} - "
                "see backends/llama_cpp_sources.py."
            )

        filename, total_size = self._resolve_filename(repo, model)
        destination = self._family_dir(model) / filename
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and total_size and destination.stat().st_size == total_size:
            yield DownloadProgress(DownloadStatus.COMPLETE, total_size, total_size, "Already downloaded.")
            return

        required_bytes = int((total_size or model.file_size_bytes or 0) * DISK_SAFETY_MARGIN)
        disk = get_disk_info(destination.parent)

        if required_bytes and disk["free_bytes"] < required_bytes:
            raise InsufficientDiskSpaceError(
                f"{model.name} needs ~{required_bytes / 1e9:.1f} GB free, "
                f"only {disk['free_bytes'] / 1e9:.1f} GB available."
            )

        resume_from = destination.stat().st_size if destination.exists() else 0
        headers = _hf_headers()
        if resume_from:
            headers["Range"] = f"bytes={resume_from}-"

        url = f"{HF_BASE}/{repo}/resolve/main/{filename}"
        request = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                mode = "ab" if resume_from else "wb"
                downloaded = resume_from

                with open(destination, mode) as file:
                    while True:
                        chunk = response.read(_DOWNLOAD_CHUNK_BYTES)
                        if not chunk:
                            break

                        file.write(chunk)
                        downloaded += len(chunk)

                        yield DownloadProgress(DownloadStatus.DOWNLOADING, downloaded, total_size, filename)
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise GatedRepositoryError(
                    f"{repo} is gated - set the HF_TOKEN environment "
                    "variable to a token that has accepted its license."
                )
            raise

        yield DownloadProgress(DownloadStatus.COMPLETE, downloaded, total_size, "Download complete.")

    def serve(self, model: ModelSpec) -> str:
        binary = _find_llama_server_binary()

        if binary is None:
            raise LlamaServerNotFoundError(
                "llama-server not found. Install llama.cpp and put it on "
                "PATH, or set the LLAMA_SERVER_PATH environment variable."
            )

        gguf_path = self._find_local_gguf(model)

        if gguf_path is None:
            raise ModelNotDownloadableError(f"{model.name} hasn't been downloaded yet.")

        self.stop()  # this backend serves one model at a time

        port = _find_free_port()
        log_path = self._models_dir / "llama-server.log"
        log_file = open(log_path, "w", encoding="utf-8")

        self._process = subprocess.Popen(
            [binary, "-m", str(gguf_path), "-c", str(model.context_length), "--port", str(port)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        self._port = port

        base_url = f"http://127.0.0.1:{port}"

        try:
            self._wait_until_healthy(base_url)
        except Exception:
            self.stop()
            raise

        return base_url

    def _wait_until_healthy(self, base_url: str) -> None:
        deadline = time.monotonic() + _HEALTH_CHECK_TIMEOUT_SECONDS

        while time.monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                raise RuntimeError(
                    f"llama-server exited early (code {self._process.returncode}) - "
                    f"see {self._models_dir / 'llama-server.log'}"
                )

            try:
                with urllib.request.urlopen(f"{base_url}/health", timeout=2):
                    return
            except (urllib.error.URLError, OSError):
                time.sleep(_HEALTH_CHECK_POLL_SECONDS)

        raise TimeoutError(
            f"llama-server did not become healthy within {_HEALTH_CHECK_TIMEOUT_SECONDS}s."
        )

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()

        self._process = None
        self._port = None

    def chat(self, model: ModelSpec, message: str) -> str:
        if self._port is None:
            raise RuntimeError(f"{model.name} isn't running.")

        body = json.dumps({
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }).encode("utf-8")

        request = urllib.request.Request(
            f"http://127.0.0.1:{self._port}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return payload["choices"][0]["message"]["content"]
