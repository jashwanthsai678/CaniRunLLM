"""Picks which backend(s) can handle a given model.

Phase 0 registers no backends, so this always reports nothing
available - Phase 1 registers an Ollama backend here, Phase 2 a
llama.cpp one (see ROADMAP.md).
"""

from canirunllm.backends.interface import Backend
from canirunllm.models.model import ModelSpec


class BackendManager:

    def __init__(self, backends: list[Backend] | None = None):
        self._backends = backends or []

    def available_backends(self) -> list[Backend]:
        return [backend for backend in self._backends if backend.is_available()]

    def backends_for(self, model: ModelSpec) -> list[Backend]:
        """Backends that could plausibly serve this specific model.

        Phase 0 has no backends registered, so this is always empty.
        Once real backends exist, this is where model-specific checks
        belong (e.g. "does this model have a verified Ollama tag?"),
        not just "is the backend installed."
        """
        return self.available_backends()
