"""Aggregate real Codex rollout files into the usage payload."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from scripts.sync_codex_usage import CodexUsageError, summarize


CST = timezone(timedelta(hours=8))


def record(timestamp, total):
    return {
        "timestamp": timestamp,
        "type": "token_usage_record",
        "payload": {"usage": {"input_tokens": total - 10, "output_tokens": 10, "total_tokens": total}},
    }


def token_count(timestamp, rate, total=1000):
    return {
        "timestamp": timestamp,
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {"total_token_usage": {"total_tokens": total}},
            "rate_limits": rate,
        },
    }


RATE = {
    "limit_id": "codex",
    "primary": {"used_percent": 0.0, "window_minutes": 43200, "resets_at": 1796627426},
    "secondary": None,
    "plan_type": "free",
}


def write_session(home, name, lines):
    path = home / "sessions" / "2026" / "11" / "07" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


@pytest.fixture
def home(tmp_path):
    root = tmp_path / "codex"
    write_session(
        root,
        "rollout-a.jsonl",
        [
            record("2026-11-01T15:59:00.000Z", 999),          # 11-01 23:59 CST, outside the window
            record("2026-11-02T01:00:00.000Z", 1_000_000),    # 11-02 09:00 CST
            record("2026-11-07T07:10:35.794Z", 352081),       # 11-07 15:10 CST
            token_count("2026-11-07T07:10:35.802Z", RATE),
        ],
    )
    write_session(
        root,
        "rollout-b.jsonl",
        [
            record("2026-11-08T02:00:00.000Z", 5000),         # 11-08 10:00 CST, today
            {"timestamp": "2026-11-08T02:01:00.000Z", "type": "event_msg", "payload": {"type": "token_count"}},
        ],
    )
    (root / "sessions" / "2026" / "11" / "07" / "broken.jsonl").write_text(
        "{not json}\n", encoding="utf-8"
    )
    return root


NOW = datetime(2026, 11, 8, 15, 0, tzinfo=CST)


def test_summarize_reports_windows_days_and_quota(home):
    payload = summarize(home, NOW)

    assert payload["today_tokens"] == 5000
    assert payload["week_tokens"] == 1_357_081
    assert payload["total_tokens"] == 1_358_080
    assert payload["responses"] == 4
    assert payload["sessions"] == 2
    assert payload["last_activity"] == "11-08 10:00"
    assert payload["days"] == [
        {"date": "11-02", "tokens": 1_000_000},
        {"date": "11-03", "tokens": 0},
        {"date": "11-04", "tokens": 0},
        {"date": "11-05", "tokens": 0},
        {"date": "11-06", "tokens": 0},
        {"date": "11-07", "tokens": 352081},
        {"date": "11-08", "tokens": 5000},
    ]
    assert payload["used_percent"] == 0.0
    assert payload["window_minutes"] == 43200
    assert payload["resets_at"] == "12-07"
    assert payload["quota_at"] == "11-07 15:10"
    assert payload["plan"] == "free"
    assert payload["source"] == "codex-sessions"


def test_missing_sessions_directory_is_an_error(tmp_path):
    with pytest.raises(CodexUsageError):
        summarize(tmp_path / "absent", NOW)


def test_sessions_without_records_are_an_error(tmp_path):
    write_session(tmp_path / "codex", "empty.jsonl", [{"type": "session_meta", "payload": {}}])
    with pytest.raises(CodexUsageError):
        summarize(tmp_path / "codex", NOW)
