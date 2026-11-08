"""Remote listener address rules; no sockets are opened in this file yet."""

from __future__ import annotations

import pytest

from services.remote_listen import listen_addresses


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
