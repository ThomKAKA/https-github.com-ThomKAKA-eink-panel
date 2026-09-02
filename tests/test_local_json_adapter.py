import json
from datetime import datetime

from adapters.local_json import LocalJSONAdapter


def fixed_clock() -> datetime:
    return datetime(2026, 8, 31, 12, 34, 56)


def test_local_json_adapter_reads_panel_data(tmp_path) -> None:
    (tmp_path / "stats.json").write_text(
        json.dumps({"primary_value": "258.42M"}),
        encoding="utf-8",
    )
    adapter = LocalJSONAdapter(
        {"panel": "stats", "label": "Local JSON", "path": "stats.json"},
        root=tmp_path,
        clock=fixed_clock,
    )

    result = adapter.fetch()

    assert result.success is True
    assert result.data["primary_value"] == "258.42M"
    assert result.data["updated_at"] == "2026-08-31 12:34:56"


def test_local_json_adapter_invalid_json_is_failure(tmp_path) -> None:
    (tmp_path / "bad.json").write_text("not-json", encoding="utf-8")
    adapter = LocalJSONAdapter(
        {"path": "bad.json"},
        root=tmp_path,
        clock=fixed_clock,
    )

    assert adapter.fetch().success is False


def test_local_json_adapter_requires_object_payload(tmp_path) -> None:
    (tmp_path / "list.json").write_text("[]", encoding="utf-8")
    adapter = LocalJSONAdapter(
        {"path": "list.json"},
        root=tmp_path,
        clock=fixed_clock,
    )

    result = adapter.fetch()

    assert result.success is False
    assert "must be an object" in result.error
