"""The Ollama backend: wraps the `ollama` local service instead of
managing downloads/processes ourselves. Ollama already solves
resumable downloads, checksums, and serving - this backend is a thin
adapter around its REST API (http://127.0.0.1:11434), never a
reimplementation.

Only registry entries with a verified tag in ollama_tags.py can be
downloaded through this backend - everything else raises, rather than
guessing a tag that might not exist.
"""

import json
import urllib.error
import urllib.request
from typing import Iterator

from canirunllm.backends.interface import Backend, DownloadProgress, DownloadStatus
from canirunllm.backends.ollama_tags import OLLAMA_TAGS
from canirunllm.models.model import ModelSpec

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
_AVAILABILITY_TIMEOUT_SECONDS = 1.5
_REQUEST_TIMEOUT_SECONDS = 5


class OllamaNotAvailableError(Exception):
    pass


class ModelNotDownloadableError(Exception):
    """Raised when a model has no verified Ollama tag - never guess one."""


class OllamaBackend(Backend):
    name = "ollama"

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self._base_url = base_url

    def is_available(self) -> bool:
        try:
            request = urllib.request.Request(f"{self._base_url}/api/version")
            with urllib.request.urlopen(request, timeout=_AVAILABILITY_TIMEOUT_SECONDS):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def tag_for(self, model: ModelSpec) -> str | None:
        return OLLAMA_TAGS.get(model.name)

    def download(self, model: ModelSpec) -> Iterator[DownloadProgress]:
        tag = self.tag_for(model)

        if tag is None:
            raise ModelNotDownloadableError(
                f"No verified Ollama tag for {model.name} - see backends/ollama_tags.py."
            )

        body = json.dumps({"name": tag, "stream": True}).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/api/pull",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue

                    payload = json.loads(line)

                    if "error" in payload:
                        raise RuntimeError(payload["error"])

                    completed = payload.get("completed", 0)
                    total = payload.get("total")
                    status_text = payload.get("status", "")

                    is_done = status_text == "success"

                    yield DownloadProgress(
                        status=DownloadStatus.COMPLETE if is_done else DownloadStatus.DOWNLOADING,
                        bytes_downloaded=completed,
                        total_bytes=total,
                        message=status_text,
                    )
        except urllib.error.URLError as error:
            yield DownloadProgress(
                status=DownloadStatus.FAILED,
                bytes_downloaded=0,
                total_bytes=None,
                message=str(error),
            )
            raise

    def serve(self, model: ModelSpec) -> str:
        tag = self.tag_for(model)

        if tag is None:
            raise ModelNotDownloadableError(
                f"No verified Ollama tag for {model.name} - see backends/ollama_tags.py."
            )

        # Ollama's API is always running and serves any model already
        # pulled - there's no separate process for this backend to spawn.
        return self._base_url

    def stop(self) -> None:
        pass

    def chat(self, model: ModelSpec, message: str) -> str:
        """Send one message to the given model via Ollama's chat API and
        return the assistant's reply text."""

        tag = self.tag_for(model)

        if tag is None:
            raise ModelNotDownloadableError(
                f"No verified Ollama tag for {model.name} - see backends/ollama_tags.py."
            )

        body = json.dumps({
            "model": tag,
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }).encode("utf-8")

        request = urllib.request.Request(
            f"{self._base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return payload["message"]["content"]
