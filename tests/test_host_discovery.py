"""R2A DNS-SD contracts. All multicast and HTTP listeners are mocked."""

import hashlib
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from zeroconf import NonUniqueNameException

import server.main as server
import services.host_discovery as discovery
from services.event_store import EventStateStore
from services.progress_frame import ProgressFramePublisher


@pytest.fixture
def environment(monkeypatch):
    engine = Mock()
    factory = Mock(return_value=engine)
    monkeypatch.setattr(discovery, "Zeroconf", factory)
    monkeypatch.setattr(server.app.state, "host_advertisement", None, raising=False)
    store = EventStateStore()
    monkeypatch.setattr(server, "event_store", store)
    monkeypatch.setattr(server, "frame_publisher", ProgressFramePublisher(store, "lan"))
    return factory, engine


def test_stable_service_identity_and_ipv4(environment):
    factory, engine = environment
    advertisement = discovery.HostAdvertisement("192.168.1.23", 8765)
    advertisement.start()
    info = engine.register_service.call_args.args[0]
    assert info.type == "_eink-panel._tcp.local."
    assert info.name == "eink-panel._eink-panel._tcp.local."
    assert info.server == "eink-panel.local."
    assert info.parsed_addresses() == ["192.168.1.23"]
    assert info.port == 8765
    assert engine.register_service.call_args.kwargs == {"allow_name_change": False}
    assert factory.call_args.kwargs["interfaces"] == ["192.168.1.23"]
    advertisement.close()


@pytest.mark.parametrize("port", [8000, 8765])
def test_advertisement_port_is_the_actual_http_bind_port(environment, monkeypatch, port):
    _, engine = environment
    listener = Mock()
    monkeypatch.setattr("uvicorn.run", listener)
    server.main(["--host", "192.168.1.23", "--port", str(port)])
    assert listener.call_args.args == (server.app,)
    assert listener.call_args.kwargs["host"] == "192.168.1.23"
    with TestClient(server.app):
        assert engine.register_service.call_args.args[0].port == listener.call_args.kwargs["port"] == port
    engine.unregister_service.assert_called_once()
    engine.close.assert_called_once()


def test_startup_and_status_do_not_render(environment, monkeypatch):
    _, engine = environment
    monkeypatch.setattr(server.app.state, "host_advertisement", discovery.HostAdvertisement("192.168.1.23", 8000))
    renderer = Mock(side_effect=AssertionError("Advertisement must not render"))
    monkeypatch.setattr(server, "frame_publisher", ProgressFramePublisher(server.event_store, "lan", renderer=renderer))
    server.event_store.ingest(server.PanelUpdateEvent(
        event_id="pending-before-startup", type="panel.update", source="lan", panel="progress",
        occurred_at="2026-10-03T01:00:00Z",
        data={"title": "项目", "current_step": "待渲染", "status": "进行中", "progress": 72},
    ))
    with TestClient(server.app) as client:
        response = client.get("/api/panels/progress/status")
        assert response.status_code == 200
        assert response.json()["host_stage"] == "HOST_ACCEPTED"
        assert response.json()["frame_version"] is None
        engine.register_service.assert_called_once()
    renderer.assert_not_called()


def test_shutdown_unregisters_and_releases_registration(environment):
    _, engine = environment
    advertisement = discovery.HostAdvertisement("192.168.1.23", 8000)
    server.app.state.host_advertisement = advertisement
    with TestClient(server.app):
        engine.close.assert_not_called()
    engine.unregister_service.assert_called_once_with(advertisement.info)
    engine.close.assert_called_once()
    advertisement.close()  # Released object does not retain a live registration.
    engine.close.assert_called_once()


@pytest.mark.parametrize("failure", [OSError("interface unavailable"), NonUniqueNameException()])
def test_unavailable_advertisement_keeps_existing_http_api_and_closes(environment, failure):
    _, engine = environment
    engine.register_service.side_effect = failure
    server.app.state.host_advertisement = discovery.HostAdvertisement("192.168.1.23", 8000)
    with TestClient(server.app) as client:
        assert client.get("/api/panels/progress/status").status_code == 200
    engine.close.assert_called_once()
    engine.unregister_service.assert_not_called()


def test_loopback_default_keeps_local_server_without_multicast(environment, monkeypatch):
    factory, _ = environment
    listener = Mock()
    monkeypatch.setattr("uvicorn.run", listener)
    server.main([])
    assert listener.call_args.kwargs["host"] == "127.0.0.1"
    assert listener.call_args.kwargs["port"] == 8000
    with TestClient(server.app) as client:
        assert client.get("/api/panels/progress/status").status_code == 200
    factory.assert_not_called()


@pytest.mark.parametrize("address,port", [("0.0.0.0", 8000), ("224.0.0.251", 8000), ("192.168.1.23", 0), ("192.168.1.23", 65536)])
def test_invalid_advertised_endpoint_is_rejected_without_network(environment, address, port):
    factory, _ = environment
    with pytest.raises(ValueError):
        discovery.HostAdvertisement(address, port)
    factory.assert_not_called()


def test_advertisement_preserves_real_frame_etag_304_and_observability(environment):
    server.app.state.host_advertisement = discovery.HostAdvertisement("192.168.1.23", 8765)
    with TestClient(server.app) as client:
        assert client.post("/api/events", json={
            "event_id": "r2a", "type": "panel.update", "source": "lan", "panel": "progress",
            "occurred_at": "2026-10-03T01:00:00Z",
            "data": {"title": "项目", "current_step": "状态验证", "status": "进行中",
                     "progress": 72, "updated_at": "2026-10-03 09:00"},
        }).json()["accepted"]
        assert client.get("/api/panels/progress/status").json()["host_stage"] == "HOST_ACCEPTED"
        frame = client.get("/api/panels/progress/frame")
        assert frame.status_code == 200 and len(frame.content) == 15000
        assert frame.headers["etag"] == '"' + hashlib.sha256(frame.content).hexdigest() + '"'
        assert frame.headers["x-frame-format"] == "epd-t-400x300-mono1-msb-v1"
        before = client.get("/api/panels/progress/status").json()
        assert set(before) == {
            "publish_id", "frame_version", "host_stage", "source",
            "frame_format", "device",
        }
        assert before["publish_id"] == "r2a" and before["host_stage"] == "FRAME_READY"
        unchanged = client.get("/api/panels/progress/frame", headers={"If-None-Match": frame.headers["etag"]})
        assert unchanged.status_code == 304 and unchanged.content == b""
        assert client.get("/api/panels/progress/status").json() == before
        for stage in ["DEVICE_FRAME_ACCEPTED", "DEVICE_REFRESH_FLOW_COMPLETE"]:
            assert client.post("/api/panels/progress/device-report", json={
                "frame_version": before["frame_version"], "firmware_version": "round2-r1a-1",
                "refresh_stage": stage,
            }).status_code == 200
        assert client.get("/api/panels/progress/status").json()["device"]["refresh_stage"] == "DEVICE_REFRESH_FLOW_COMPLETE"
