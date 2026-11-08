"""Host CLI wiring for --remote; uvicorn and sockets are mocked."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import uvicorn

import server.main as server


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    monkeypatch.setattr(server.app.state, "host_advertisement", None, raising=False)


def test_default_startup_still_calls_uvicorn_run(monkeypatch):
    listener = Mock()
    monkeypatch.setattr(uvicorn, "run", listener)
    bind = Mock()
    monkeypatch.setattr(server, "bind_listeners", bind)

    assert server.main(["--host", "192.168.1.23", "--port", "8000"]) == 0
    listener.assert_called_once()
    assert listener.call_args.args == (server.app,)
    assert listener.call_args.kwargs == {"host": "192.168.1.23", "port": 8000, "reload": False}
    bind.assert_not_called()


def test_remote_binds_both_addresses_and_runs_one_server(monkeypatch):
    sockets = [Mock(name="lan"), Mock(name="loopback")]
    bind = Mock(return_value=(sockets, 8000))
    monkeypatch.setattr(server, "bind_listeners", bind)
    config = Mock()
    monkeypatch.setattr(uvicorn, "Config", Mock(return_value=config))
    server_type = Mock()
    monkeypatch.setattr(uvicorn, "Server", server_type)
    listener = Mock()
    monkeypatch.setattr(uvicorn, "run", listener)

    assert server.main(["--host", "192.168.1.23", "--remote"]) == 0
    bind.assert_called_once_with(["192.168.1.23", "127.0.0.1"], 8000)
    server_type.assert_called_once_with(config)
    server_type.return_value.run.assert_called_once_with(sockets=sockets)
    listener.assert_not_called()
    assert server.app.state.host_advertisement.address == "192.168.1.23"


def test_remote_with_loopback_host_exits_with_usage_error(monkeypatch, capsys):
    listener = Mock()
    monkeypatch.setattr(uvicorn, "run", listener)
    with pytest.raises(SystemExit) as exit_info:
        server.main(["--host", "127.0.0.1", "--remote"])
    assert exit_info.value.code == 2
    assert "--remote requires a non-loopback --host" in capsys.readouterr().err
    listener.assert_not_called()


def test_bind_failure_returns_nonzero_without_starting(monkeypatch, caplog):
    monkeypatch.setattr(server, "bind_listeners", Mock(side_effect=OSError("in use")))
    server_type = Mock()
    monkeypatch.setattr(uvicorn, "Server", server_type)

    assert server.main(["--host", "192.168.1.23", "--remote"]) == 1
    server_type.assert_not_called()
    assert "in use" in caplog.text
    assert "192.168.1.23" in caplog.text and "8000" in caplog.text
