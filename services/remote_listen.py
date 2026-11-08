"""Loopback listener for Tailscale Serve, next to the existing LAN listener."""

from __future__ import annotations

from ipaddress import IPv4Address

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
