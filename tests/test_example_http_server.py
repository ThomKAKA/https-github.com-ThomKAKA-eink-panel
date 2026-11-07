from fastapi.testclient import TestClient

from examples.http_server import _counts, app


client = TestClient(app)


def test_progress_endpoint_uses_requested_codex_sequence() -> None:
    _counts["progress"] = 0

    outcomes = [client.get("/progress").json() for _ in range(6)]

    assert [outcome["progress"] for outcome in outcomes] == [72, 73, 81, 81, 100, 100]
    assert [outcome["status"] for outcome in outcomes] == [
        "开发中",
        "开发中",
        "开发中",
        "等待确认",
        "已完成",
        "已完成",
    ]


def test_stats_endpoint_uses_requested_token_sequence() -> None:
    _counts["stats"] = 0

    values = [client.get("/stats").json()["primary_value"] for _ in range(4)]

    assert values == ["258.42M", "260.11M", "264.73M", "264.73M"]


def test_flow_endpoint_uses_requested_stage_sequence() -> None:
    _counts["flow"] = 0

    outcomes = [client.get("/flow").json() for _ in range(4)]

    assert [outcome["title"] for outcome in outcomes] == ["准备", "执行", "完成", "完成"]
    assert [[stage["status"] for stage in outcome["stages"]] for outcome in outcomes] == [
        ["active", "pending", "pending"],
        ["done", "active", "pending"],
        ["done", "done", "done"],
        ["done", "done", "done"],
    ]
