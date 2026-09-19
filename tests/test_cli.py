import errno
import sys
from unittest.mock import patch

import pytest

from canirunllm import cli


def _set_argv(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["canirunllm"] + args)


# --- find_pip_mismatch ---

def test_find_pip_mismatch_returns_none_when_pip_matches_running_python(monkeypatch):
    monkeypatch.setattr(cli.shutil, "which", lambda name: sys.executable)
    assert cli.find_pip_mismatch() is None


def test_find_pip_mismatch_returns_none_when_pip_not_found(monkeypatch):
    monkeypatch.setattr(cli.shutil, "which", lambda name: None)
    assert cli.find_pip_mismatch() is None


def test_find_pip_mismatch_detects_real_mismatch(monkeypatch, tmp_path):
    fake_pip = tmp_path / "other_python" / "Scripts" / "pip.exe"
    fake_pip.parent.mkdir(parents=True)
    fake_pip.write_text("fake")

    monkeypatch.setattr(cli.shutil, "which", lambda name: str(fake_pip))

    warning = cli.find_pip_mismatch()

    assert warning is not None
    assert sys.executable in warning
    assert "pip install --upgrade canirunllm" in warning


# --- _is_port_in_use_error ---

def test_is_port_in_use_error_detects_errno():
    exc = OSError()
    exc.errno = errno.EADDRINUSE
    assert cli._is_port_in_use_error(exc) is True


def test_is_port_in_use_error_detects_windows_message():
    exc = OSError("[WinError 10048] Only one usage of each socket address is normally permitted")
    assert cli._is_port_in_use_error(exc) is True


def test_is_port_in_use_error_false_for_unrelated_error():
    exc = OSError("Permission denied")
    assert cli._is_port_in_use_error(exc) is False


# --- main() behavior ---

def test_help_with_no_args(monkeypatch, capsys):
    _set_argv(monkeypatch, [])
    cli.main()
    out = capsys.readouterr().out
    assert "Usage:" in out


def test_version_includes_python_path(monkeypatch, capsys):
    _set_argv(monkeypatch, ["--version"])
    cli.main()
    out = capsys.readouterr().out
    assert "canirunllm" in out
    assert sys.executable in out


def test_unknown_command_points_at_help(monkeypatch, capsys):
    _set_argv(monkeypatch, ["bogus"])
    monkeypatch.setattr(cli, "find_pip_mismatch", lambda: None)
    cli.main()
    out = capsys.readouterr().out
    assert "Unknown command: bogus" in out
    assert "--help" in out


def test_pip_mismatch_warning_is_printed_when_present(monkeypatch, capsys):
    _set_argv(monkeypatch, ["recommend"])
    monkeypatch.setattr(cli, "find_pip_mismatch", lambda: "MISMATCH WARNING TEXT")

    with patch.object(cli, "ScannerService") as mock_service_cls:
        mock_service_cls.return_value.recommend.return_value = (None, [])
        cli.main()

    out = capsys.readouterr().out
    assert "MISMATCH WARNING TEXT" in out


def test_keyboard_interrupt_is_caught_not_raised(monkeypatch, capsys):
    _set_argv(monkeypatch, ["recommend"])
    monkeypatch.setattr(cli, "find_pip_mismatch", lambda: None)

    with patch.object(cli, "ScannerService") as mock_service_cls:
        mock_service_cls.return_value.recommend.side_effect = KeyboardInterrupt()
        cli.main()  # must not raise

    out = capsys.readouterr().out
    assert "Cancelled." in out


def test_unexpected_exception_gets_friendly_message_not_a_traceback(monkeypatch, capsys):
    _set_argv(monkeypatch, ["recommend"])
    monkeypatch.setattr(cli, "find_pip_mismatch", lambda: None)

    with patch.object(cli, "ScannerService") as mock_service_cls:
        mock_service_cls.return_value.recommend.side_effect = RuntimeError("boom")
        cli.main()  # must not raise

    out = capsys.readouterr().out
    assert "Something went wrong: boom" in out
    assert "github.com" in out


def test_port_in_use_error_gives_actionable_message(monkeypatch, capsys):
    _set_argv(monkeypatch, ["web", "--port", "9999"])
    monkeypatch.setattr(cli, "find_pip_mismatch", lambda: None)

    with patch.object(cli, "run_dashboard") as mock_run:
        mock_run.side_effect = OSError("[WinError 10048] Only one usage of each socket address")
        cli.main()  # must not raise

    out = capsys.readouterr().out
    assert "Port 9999 is already in use" in out
    assert "--port 9000" in out
