import time
from unittest.mock import patch

from canirunllm.web.launcher import (
    DEFAULT_HOST,
    DEFAULT_PORT,
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

    with patch("canirunllm.web.launcher.uvicorn.run") as mock_run, \
         patch("canirunllm.web.launcher.open_browser_later") as mock_open_later:

        run_dashboard()

        _, kwargs = mock_run.call_args
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8765
        mock_open_later.assert_called_once()


def test_run_dashboard_uses_custom_port():

    with patch("canirunllm.web.launcher.uvicorn.run") as mock_run, \
         patch("canirunllm.web.launcher.open_browser_later"):

        run_dashboard(port=9000)

        _, kwargs = mock_run.call_args
        assert kwargs["port"] == 9000


def test_run_dashboard_skips_browser_when_disabled():

    with patch("canirunllm.web.launcher.uvicorn.run"), \
         patch("canirunllm.web.launcher.open_browser_later") as mock_open_later:

        run_dashboard(open_browser=False)

        mock_open_later.assert_not_called()
