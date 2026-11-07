"""One DNS-SD advertisement for the Host's actual IPv4 HTTP endpoint."""

from ipaddress import IPv4Address

from zeroconf import IPVersion, ServiceInfo, Zeroconf

SERVICE_TYPE = "_eink-panel._tcp.local."
SERVICE_NAME = "eink-panel." + SERVICE_TYPE
SERVER_NAME = "eink-panel.local."


class HostAdvertisement:
    def __init__(self, address: str, port: int):
        ip = IPv4Address(address)
        if ip.is_unspecified or ip.is_multicast or ip.is_loopback or int(ip) == 0xFFFFFFFF:
            raise ValueError("Advertisement requires a unicast LAN IPv4 address")
        if not 1 <= port <= 65535:
            raise ValueError("HTTP port must be between 1 and 65535")
        self.address = str(ip)
        self.info = ServiceInfo(
            SERVICE_TYPE, SERVICE_NAME, addresses=[ip.packed], port=port,
            server=SERVER_NAME,
        )
        self.zeroconf = None

    def start(self):
        engine = Zeroconf(interfaces=[self.address], ip_version=IPVersion.V4Only)
        try:
            engine.register_service(self.info, allow_name_change=False)
        except BaseException:
            engine.close()
            raise
        self.zeroconf = engine

    def close(self):
        engine = self.zeroconf
        if engine is None:
            return
        self.zeroconf = None
        try:
            engine.unregister_service(self.info)
        finally:
            engine.close()
