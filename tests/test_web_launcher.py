import socket
import time
from unittest.mock import patch

import pytest

from canirunllm.web.launcher import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    _check_port_available,
    open_browser_later,
    run_dashboard,
)


def test_default_host_is_localhost():
    assert DEFAULT_HOST == "127.0.0.1"


def test_default_port_is_8765():
    assert DEFAULT_PORT == 8765


def test_open_browser_later_calls_webbrowser_open():

    with patch("canirunllm.web.launcher.webbrowser.open") as mock_open:

        open_browser_later("http://127.0.0.1:8765", delay=0)

        time.sleep(0.1)

        mock_open.assert_called_once_with("http://127.0.0.1:8765")


def test_open_browser_later_swallows_errors():

    with patch(
        "canirunllm.web.launcher.webbrowser.open",
        side_effect=RuntimeError("no display"),
    ):

        open_browser_later("http://127.0.0.1:8765", delay=0)

        time.sleep(0.1)

        # Should not raise — the background thread must not crash the process.


def test_run_dashboard_binds_to_localhost_by_default():

    with patch("canirunllm.web.launcher._check_port_available"), \
         patch("canirunllm.web.launcher.uvicorn.run") as mock_run, \
         patch("canirunllm.web.launcher.open_browser_later") as mock_open_later:

        run_dashboard()

        _, kwargs = mock_run.call_args
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8765
        mock_open_later.assert_called_once()


def test_run_dashboard_uses_custom_port():

    with patch("canirunllm.web.launcher._check_port_available"), \
         patch("canirunllm.web.launcher.uvicorn.run") as mock_run, \
         patch("canirunllm.web.launcher.open_browser_later"):

        run_dashboard(port=9000)

        _, kwargs = mock_run.call_args
        assert kwargs["port"] == 9000


def test_run_dashboard_skips_browser_when_disabled():

    with patch("canirunllm.web.launcher._check_port_available"), \
         patch("canirunllm.web.launcher.uvicorn.run"), \
         patch("canirunllm.web.launcher.open_browser_later") as mock_open_later:

        run_dashboard(open_browser=False)

        mock_open_later.assert_not_called()


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_check_port_available_passes_when_port_is_free():
    port = _get_free_port()
    _check_port_available("127.0.0.1", port)  # must not raise


def test_check_port_available_raises_when_port_is_taken():
    port = _get_free_port()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as holder:
        holder.bind(("127.0.0.1", port))
        holder.listen(1)

        with pytest.raises(OSError):
            _check_port_available("127.0.0.1", port)


def test_run_dashboard_raises_real_oserror_when_port_taken_before_uvicorn_starts():
    """The actual bug this was built to catch: uvicorn.run() swallows a
    bind failure internally and calls sys.exit() instead of raising a
    normal exception - so a caller's `except OSError` around
    run_dashboard() would never fire. Checking the port ourselves,
    before uvicorn is ever invoked, gives a real, catchable OSError."""

    port = _get_free_port()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as holder:
        holder.bind(("127.0.0.1", port))
        holder.listen(1)

        with patch("canirunllm.web.launcher.uvicorn.run") as mock_run:
            with pytest.raises(OSError):
                run_dashboard(port=port)

            mock_run.assert_not_called()
