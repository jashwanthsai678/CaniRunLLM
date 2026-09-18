"""Picks which backend(s) can handle a given model. See ROADMAP.md -
Phase 1 registered an Ollama backend, Phase 2 a llama.cpp one.
"""

from canirunllm.backends.interface import Backend
from canirunllm.models.model import ModelSpec


class BackendManager:

    def __init__(self, backends: list[Backend] | None = None):
        self.backends = backends or []

    def available_backends(self) -> list[Backend]:
        return [backend for backend in self.backends if backend.is_available()]

    def supporting_backends(self, model: ModelSpec) -> list[Backend]:
        """All registered backends with a verified way to get this model,
        regardless of whether they're currently available (see
        Backend.supports) - useful for reporting "X could do this but
        isn't installed/running" rather than just "nothing can"."""
        return [backend for backend in self.backends if backend.supports(model)]

    def backends_for(self, model: ModelSpec) -> list[Backend]:
        """Backends that are both available right now and have a
        verified way to get this specific model."""
        return [backend for backend in self.supporting_backends(model) if backend.is_available()]
