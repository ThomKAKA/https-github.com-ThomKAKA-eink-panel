"""Loopback listener for Tailscale Serve, next to the existing LAN listener."""

from __future__ import annotations

import socket
import sys
from ipaddress import IPv4Address
from typing import Callable, Sequence

LOOPBACK = "127.0.0.1"
BROADCAST = 0xFFFFFFFF


def listen_addresses(host: str, remote: bool) -> list[str]:
    """Return the addresses uvicorn must bind for this startup."""
    address = IPv4Address(host)
    if not remote:
        return [str(address)]
    if address.is_loopback:
        raise ValueError("--remote requires a non-loopback --host")
    if address.is_unspecified or address.is_multicast or int(address) == BROADCAST:
        raise ValueError("--remote requires a unicast LAN IPv4")
    return [str(address), LOOPBACK]


def bind_listeners(
    addresses: Sequence[str],
    port: int,
    *,
    sock_factory: Callable[..., socket.socket] = socket.socket,
) -> tuple[list[socket.socket], int]:
    """Bind every address on one port and return the listening sockets."""
    if not addresses:
        raise ValueError("At least one listen address is required")
    if not 0 <= port <= 65535:
        raise ValueError("HTTP port must be between 0 and 65535")
    created: list[socket.socket] = []
    bound_port = port
    try:
        for address in addresses:
            sock = sock_factory(socket.AF_INET, socket.SOCK_STREAM)
            created.append(sock)
            if sys.platform != "win32":
                # On Windows SO_REUSEADDR lets a second process claim the same
                # endpoint; keep the default exclusive bind so port-in-use fails.
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((address, bound_port))
            sock.listen(128)
            if bound_port == 0:
                bound_port = sock.getsockname()[1]
    except BaseException:
        for sock in created:
            sock.close()
        raise
    return created, bound_port
