"""Remote listener address rules and the binder that opens the sockets."""

from __future__ import annotations

import socket

import pytest

from services.remote_listen import bind_listeners, listen_addresses


def test_default_and_lan_startup_keep_one_address():
    assert listen_addresses("127.0.0.1", False) == ["127.0.0.1"]
    assert listen_addresses("10.21.98.75", False) == ["10.21.98.75"]


def test_remote_adds_loopback_after_the_lan_address():
    assert listen_addresses("10.21.98.75", True) == ["10.21.98.75", "127.0.0.1"]


def test_remote_rejects_loopback_host():
    with pytest.raises(ValueError, match="--remote requires a non-loopback --host"):
        listen_addresses("127.0.0.1", True)


@pytest.mark.parametrize("host", ["0.0.0.0", "224.0.0.251", "255.255.255.255"])
def test_remote_rejects_non_unicast_host(host):
    with pytest.raises(ValueError, match="--remote requires a unicast LAN IPv4"):
        listen_addresses(host, True)


def test_bind_listeners_share_one_ephemeral_port():
    sockets, port = bind_listeners(["127.0.0.1", "127.0.0.2"], 0)
    try:
        assert port > 0
        assert len(sockets) == 2
        assert {sock.getsockname() for sock in sockets} == {
            ("127.0.0.1", port),
            ("127.0.0.2", port),
        }
        for sock in sockets:
            assert sock.fileno() != -1
    finally:
        for sock in sockets:
            sock.close()


def test_bind_listeners_closes_earlier_sockets_when_a_bind_fails():
    created = []

    def factory(family, type_):
        sock = socket.socket(family, type_)
        created.append(sock)
        return sock

    with pytest.raises(OSError):
        bind_listeners(["127.0.0.1", "192.0.2.1"], 0, sock_factory=factory)
    assert len(created) == 2
    assert all(sock.fileno() == -1 for sock in created)


@pytest.mark.parametrize("addresses,port", [([], 8000), (["127.0.0.1"], -1), (["127.0.0.1"], 65536)])
def test_bind_listeners_rejects_invalid_arguments(addresses, port):
    with pytest.raises(ValueError):
        bind_listeners(addresses, port)


def test_bind_listeners_refuses_a_port_that_is_already_listening():
    first, port = bind_listeners(["127.0.0.1"], 0)
    try:
        with pytest.raises(OSError):
            bind_listeners(["127.0.0.1"], port)
    finally:
        for sock in first:
            sock.close()
