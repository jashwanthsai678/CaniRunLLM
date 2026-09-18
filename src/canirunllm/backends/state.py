"""In-memory 'what's currently running' state, shared across requests
within a single dashboard process. Not persisted - restarting the
dashboard always starts with nothing running.
"""

from dataclasses import dataclass


@dataclass
class RunningModel:
    model_name: str
    backend_name: str
    endpoint_url: str


class RuntimeState:

    def __init__(self):
        self._running: RunningModel | None = None

    def get(self) -> RunningModel | None:
        return self._running

    def set(self, running: RunningModel) -> None:
        self._running = running

    def clear(self) -> None:
        self._running = None


runtime_state = RuntimeState()
