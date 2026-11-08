"""One DNS-SD advertisement for the Host's actual IPv4 HTTP endpoint."""

import logging
import math
import threading
from ipaddress import IPv4Address

from zeroconf import IPVersion, ServiceInfo, Zeroconf

SERVICE_TYPE = "_eink-panel._tcp.local."
SERVICE_NAME = "eink-panel." + SERVICE_TYPE
SERVER_NAME = "eink-panel.local."
# The device listens about one second per poll, so a longer interval can miss a
# window entirely when the AP drops its mDNS query.
ANNOUNCE_INTERVAL_SECONDS = 1.0

logger = logging.getLogger(__name__)


class HostAdvertisement:
    def __init__(
        self,
        address: str,
        port: int,
        *,
        announce_interval: float = ANNOUNCE_INTERVAL_SECONDS,
        thread_factory=threading.Thread,
    ):
        ip = IPv4Address(address)
        if ip.is_unspecified or ip.is_multicast or ip.is_loopback or int(ip) == 0xFFFFFFFF:
            raise ValueError("Advertisement requires a unicast LAN IPv4 address")
        if not 1 <= port <= 65535:
            raise ValueError("HTTP port must be between 1 and 65535")
        if not isinstance(announce_interval, (int, float)) or not math.isfinite(
            announce_interval
        ) or announce_interval <= 0:
            raise ValueError("Announcement interval must be a positive number")
        self.address = str(ip)
        self.info = ServiceInfo(
            SERVICE_TYPE, SERVICE_NAME, addresses=[ip.packed], port=port,
            server=SERVER_NAME,
        )
        self.announce_interval = float(announce_interval)
        self.zeroconf = None
        self._thread_factory = thread_factory
        self._stop = threading.Event()
        self._thread = None
        self._announce_failed = False

    def start(self):
        engine = Zeroconf(interfaces=[self.address], ip_version=IPVersion.V4Only)
        try:
            engine.register_service(self.info, allow_name_change=False)
        except BaseException:
            engine.close()
            raise
        self.zeroconf = engine
        self._stop = threading.Event()
        self._thread = self._thread_factory(
            target=self._announce_forever, name="eink-mdns-announce", daemon=True
        )
        self._thread.start()

    def announce(self):
        engine = self.zeroconf
        if engine is None:
            return
        try:
            engine.update_service(self.info)
        except Exception:
            if not self._announce_failed:
                self._announce_failed = True
                logger.warning("Host re-announcement failed", exc_info=True)
            return
        self._announce_failed = False

    def _announce_forever(self):
        while not self._stop.wait(self.announce_interval):
            self.announce()

    def close(self):
        engine = self.zeroconf
        if engine is None:
            return
        self.zeroconf = None
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=max(2.0, self.announce_interval * 2))
        try:
            engine.unregister_service(self.info)
        finally:
            engine.close()
