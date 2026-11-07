import json
from datetime import datetime

from adapters.mock import MockAdapter


def fixed_clock() -> datetime:
    return datetime(2026, 8, 31, 12, 34, 56)


def test_mock_adapter_selects_requested_sample(tmp_path) -> None:
    path = tmp_path / "samples.json"
    path.write_text(
        json.dumps([{"id": "default", "data": {"progress": 72}}]),
        encoding="utf-8",
    )
    adapter = MockAdapter(
        {
            "panel": "progress",
            "label": "Mock",
            "path": "samples.json",
            "sample_id": "default",
        },
        root=tmp_path,
        clock=fixed_clock,
    )

    result = adapter.fetch()

    assert result.success is True
    assert result.data["progress"] == 72
    assert result.data["source"] == "Mock"
    assert result.fetched_at == "2026-08-31 12:34:56"


def test_mock_adapter_unknown_sample_is_failure(tmp_path) -> None:
    (tmp_path / "samples.json").write_text("[]", encoding="utf-8")
    adapter = MockAdapter(
        {"path": "samples.json", "sample_id": "missing"},
        root=tmp_path,
        clock=fixed_clock,
    )

    result = adapter.fetch()

    assert result.success is False
    assert "Unknown sample id" in result.error


def test_mock_adapter_rejects_path_outside_project(tmp_path) -> None:
    adapter = MockAdapter(
        {"path": "../outside.json"},
        root=tmp_path,
        clock=fixed_clock,
    )

    result = adapter.fetch()

    assert result.success is False
    assert "inside the project" in result.error
