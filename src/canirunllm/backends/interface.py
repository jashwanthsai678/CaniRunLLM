"""Shared contract for model download/run backends (Ollama, direct
llama.cpp, ...). See ROADMAP.md for the phased plan this supports.

No backend implementation exists yet (Phase 0) - this defines what
Phase 1 (Ollama) and Phase 2 (llama.cpp) will implement against. The
dashboard is meant to only ever talk to this interface, never to a
specific backend's implementation details, so adding a new backend
later never requires touching the API/dashboard layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from canirunllm.models.model import ModelSpec


class DownloadStatus(Enum):
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class DownloadProgress:
    status: DownloadStatus
    bytes_downloaded: int
    total_bytes: int | None
    message: str | None = None


ProgressCallback = Callable[[DownloadProgress], None]


class Backend(ABC):
    """One way to get a model downloaded and actually serving locally."""

    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this backend can be used at all on this machine right now
        (e.g. is Ollama installed and running? is a llama-server binary
        configured?)."""

    @abstractmethod
    def download(self, model: ModelSpec, on_progress: ProgressCallback) -> None:
        """Fetch whatever this backend needs to serve `model`, calling
        on_progress() as it goes. Raises on failure."""

    @abstractmethod
    def serve(self, model: ModelSpec) -> str:
        """Start serving `model`, returning a local endpoint URL."""

    @abstractmethod
    def stop(self) -> None:
        """Stop whatever this backend is currently serving."""
