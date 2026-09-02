import json
from datetime import datetime
from pathlib import Path
from threading import Barrier, Event, Lock, Thread

import httpx
import pytest

from adapters.base import AdapterResult
from services.refresh_manager import RefreshManager


def fixed_clock() -> datetime:
    return datetime(2026, 8, 31, 12, 34, 56)


def write_config(tmp_path, source) -> None:
    write_sources_config(tmp_path, {"stats_test": source})


def write_sources_config(tmp_path, sources) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "data_sources.json").write_text(
        json.dumps({"sources": sources}),
        encoding="utf-8",
    )


def test_refresh_manager_saves_last_known_good_and_falls_back(tmp_path) -> None:
    write_config(
        tmp_path,
        {
            "type": "http_json",
            "panel": "stats",
            "label": "HTTP JSON",
            "enabled": True,
            "url": "http://test.local/stats",
            "timeout": 5,
        },
    )
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"primary_value": "258.42M"})
        raise httpx.ConnectError("offline", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    manager = RefreshManager(
        tmp_path / "config" / "data_sources.json",
        root=tmp_path,
        clock=fixed_clock,
        http_client=client,
    )

    online = manager.refresh("stats_test", interval_seconds=300)
    offline = manager.refresh("stats_test", interval_seconds=300)

    assert online.status == "ONLINE"
    assert online.stale is False
    assert online.next_refresh == "2026-08-31 12:39:56"
    assert offline.status == "OFFLINE"
    assert offline.stale is True
    assert offline.data["primary_value"] == "258.42M"
    assert offline.last_success == "2026-08-31 12:34:56"


def test_refresh_manager_failure_without_cache_returns_empty_data(tmp_path) -> None:
    write_config(
        tmp_path,
        {
            "type": "http_json",
            "panel": "stats",
            "label": "HTTP JSON",
            "enabled": True,
            "url": "http://test.local/stats",
        },
    )

    def handler(request):
        raise httpx.ConnectError("offline", request=request)

    manager = RefreshManager(
        tmp_path / "config" / "data_sources.json",
        root=tmp_path,
        clock=fixed_clock,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    outcome = manager.refresh("stats_test")

    assert outcome.status == "OFFLINE"
    assert outcome.stale is False
    assert outcome.data == {}
    assert outcome.last_success is None


def test_refresh_manager_lists_compatible_sources(tmp_path) -> None:
    write_config(
        tmp_path,
        {
            "type": "local_json",
            "panel": "stats",
            "label": "Local JSON",
            "enabled": True,
            "path": "stats.json",
        },
    )
    manager = RefreshManager(
        tmp_path / "config" / "data_sources.json",
        root=tmp_path,
        clock=fixed_clock,
    )

    sources = manager.list_sources("stats")

    assert [source["id"] for source in sources] == ["stats_test"]
    assert sources[0]["status"] == "IDLE"


def test_refresh_manager_recovers_after_http_failure(tmp_path) -> None:
    write_config(
        tmp_path,
        {
            "type": "http_json",
            "panel": "stats",
            "label": "HTTP JSON",
            "enabled": True,
            "url": "http://test.local/stats",
        },
    )
    responses = iter(
        [
            httpx.Response(200, json={"primary_value": "OLD"}),
            httpx.ConnectError("offline"),
            httpx.Response(200, json={"primary_value": "NEW"}),
        ]
    )

    def handler(request):
        response = next(responses)
        if isinstance(response, Exception):
            response.request = request
            raise response
        return response

    manager = RefreshManager(
        tmp_path / "config" / "data_sources.json",
        root=tmp_path,
        clock=fixed_clock,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    online = manager.refresh("stats_test")
    offline = manager.refresh("stats_test")
    recovered = manager.refresh("stats_test")

    assert online.data["primary_value"] == "OLD"
    assert offline.status == "OFFLINE"
    assert offline.stale is True
    assert offline.data["primary_value"] == "OLD"
    assert recovered.status == "ONLINE"
    assert recovered.stale is False
    assert recovered.data["primary_value"] == "NEW"


def test_refresh_manager_invalid_payload_does_not_replace_last_good(tmp_path) -> None:
    write_config(
        tmp_path,
        {
            "type": "http_json",
            "panel": "stats",
            "label": "HTTP JSON",
            "enabled": True,
            "url": "http://test.local/stats",
        },
    )
    responses = iter(
        [
            httpx.Response(200, json={"primary_value": "258.42M"}),
            httpx.Response(200, json={"title": "MISSING VALUE"}),
        ]
    )
    manager = RefreshManager(
        tmp_path / "config" / "data_sources.json",
        root=tmp_path,
        clock=fixed_clock,
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda request: next(responses))
        ),
    )

    manager.refresh("stats_test")
    invalid = manager.refresh("stats_test")

    assert invalid.success is False
    assert invalid.status == "ERROR"
    assert invalid.stale is True
    assert invalid.data["primary_value"] == "258.42M"
    assert invalid.error == "Panel data is incomplete or invalid"


def test_refresh_manager_serializes_refreshes_for_same_source(
    tmp_path, monkeypatch
) -> None:
    write_config(
        tmp_path,
        {
            "type": "http_json",
            "panel": "stats",
            "label": "HTTP JSON",
            "enabled": True,
            "url": "http://test.local/stats",
        },
    )
    first_started = Event()
    release_first = Event()
    second_created = Event()
    count_lock = Lock()
    call_count = 0

    class FakeAdapter:
        def __init__(self, value, block=False):
            self.value = value
            self.block = block

        def fetch(self):
            if self.block:
                first_started.set()
                assert release_first.wait(2)
            return AdapterResult(
                True,
                {"primary_value": self.value},
                "HTTP JSON",
                self.value,
            )

    def fake_create_adapter(*args, **kwargs):
        nonlocal call_count
        with count_lock:
            call_count += 1
            index = call_count
        if index == 1:
            return FakeAdapter("OLD", block=True)
        second_created.set()
        return FakeAdapter("NEW")

    monkeypatch.setattr("services.refresh_manager.create_adapter", fake_create_adapter)
    manager = RefreshManager(
        tmp_path / "config" / "data_sources.json",
        root=tmp_path,
        clock=fixed_clock,
    )
    outcomes = {}
    first = Thread(
        target=lambda: outcomes.setdefault("first", manager.refresh("stats_test"))
    )
    second = Thread(
        target=lambda: outcomes.setdefault("second", manager.refresh("stats_test"))
    )

    first.start()
    assert first_started.wait(2)
    second.start()
    assert second_created.wait(0.05) is False
    release_first.set()
    first.join(2)
    second.join(2)

    assert first.is_alive() is False
    assert second.is_alive() is False
    assert outcomes["first"].data["primary_value"] == "OLD"
    assert outcomes["second"].data["primary_value"] == "NEW"
    assert manager._last_good["stats_test"]["primary_value"] == "NEW"


def test_refresh_manager_allows_different_sources_to_refresh_concurrently(
    tmp_path, monkeypatch
) -> None:
    source = {
        "type": "http_json",
        "panel": "stats",
        "enabled": True,
        "url": "http://test.local/stats",
    }
    write_sources_config(
        tmp_path,
        {
            "stats_one": {**source, "label": "ONE"},
            "stats_two": {**source, "label": "TWO"},
        },
    )
    fetch_barrier = Barrier(2)

    class ConcurrentAdapter:
        def __init__(self, value):
            self.value = value

        def fetch(self):
            fetch_barrier.wait(2)
            return AdapterResult(
                True,
                {"primary_value": self.value},
                self.value,
                self.value,
            )

    monkeypatch.setattr(
        "services.refresh_manager.create_adapter",
        lambda config, **kwargs: ConcurrentAdapter(config["label"]),
    )
    manager = RefreshManager(
        tmp_path / "config" / "data_sources.json",
        root=tmp_path,
        clock=fixed_clock,
    )
    outcomes = {}
    threads = [
        Thread(
            target=lambda source_id=source_id: outcomes.setdefault(
                source_id, manager.refresh(source_id)
            )
        )
        for source_id in ("stats_one", "stats_two")
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(3)

    assert all(thread.is_alive() is False for thread in threads)
    assert {outcome.status for outcome in outcomes.values()} == {"ONLINE"}


@pytest.mark.parametrize(
    ("source_id", "expected_field"),
    [
        ("progress_mock", "progress"),
        ("stats_mock", "primary_value"),
        ("flow_mock", "stages"),
    ],
)
def test_refresh_manager_handles_100_refreshes_for_each_panel(
    source_id, expected_field
) -> None:
    root = Path(__file__).resolve().parents[1]
    manager = RefreshManager(root / "config" / "data_sources.json", root=root)

    for _ in range(100):
        outcome = manager.refresh(source_id, sample_id="default")
        assert outcome.status == "ONLINE"
        assert expected_field in outcome.data
