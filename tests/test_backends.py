import pytest

from canirunllm.backends.interface import Backend, DownloadProgress, DownloadStatus
from canirunllm.backends.manager import BackendManager
from canirunllm.backends.state import RunningModel, RuntimeState


class _FakeBackend(Backend):
    name = "fake"

    def __init__(self, available: bool):
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def download(self, model):
        yield DownloadProgress(DownloadStatus.COMPLETE, 0, 0)

    def serve(self, model) -> str:
        return "http://localhost:0"

    def stop(self) -> None:
        pass

    def chat(self, model, message) -> str:
        return "fake reply"


def test_backend_is_abstract():
    with pytest.raises(TypeError):
        Backend()


def test_manager_with_no_backends_reports_none_available():
    manager = BackendManager()

    assert manager.available_backends() == []


def test_manager_filters_to_available_backends_only():
    available = _FakeBackend(available=True)
    unavailable = _FakeBackend(available=False)

    manager = BackendManager([available, unavailable])

    assert manager.available_backends() == [available]


def test_runtime_state_starts_empty():
    state = RuntimeState()

    assert state.get() is None


def test_runtime_state_set_and_clear():
    state = RuntimeState()
    running = RunningModel(
        model_name="Qwen3-8B-Q4_K_M",
        backend_name="fake",
        endpoint_url="http://localhost:1234",
    )

    state.set(running)
    assert state.get() == running

    state.clear()
    assert state.get() is None
