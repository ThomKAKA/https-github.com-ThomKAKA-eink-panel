"""Aggregate local Codex token usage and POST it to the Host page store.

Only aggregate numbers and timestamps leave this script: prompts, responses and
paths are never read into the payload or printed.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


CST = timezone(timedelta(hours=8))
WINDOW_DAYS = 7


class CodexUsageError(RuntimeError):
    """The local session files cannot produce a usage payload."""


def _moment(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(CST)


def summarize(home: Path, now: datetime) -> dict[str, Any]:
    sessions = Path(home) / "sessions"
    if not sessions.is_dir():
        raise CodexUsageError(f"sessions directory missing: {sessions}")

    now = now if now.tzinfo else now.replace(tzinfo=CST)
    today = now.astimezone(CST).date()
    per_day: dict[str, int] = defaultdict(int)
    responses = 0
    session_files: set[Path] = set()
    last_activity: datetime | None = None
    latest_rate: tuple[str, dict] | None = None

    for path in sorted(sessions.rglob("*.jsonl")):
        try:
            stream = path.open(encoding="utf-8", errors="replace")
        except OSError as error:
            raise CodexUsageError(f"cannot read {path.name}: {error}") from error
        with stream:
            for line in stream:
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("type") == "event_msg":
                    payload = obj.get("payload")
                    stamp = obj.get("timestamp")
                    if (
                        isinstance(payload, dict)
                        and payload.get("type") == "token_count"
                        and isinstance(payload.get("rate_limits"), dict)
                        and isinstance(stamp, str)
                        and (latest_rate is None or stamp > latest_rate[0])
                    ):
                        latest_rate = (stamp, payload["rate_limits"])
                    continue
                if obj.get("type") != "token_usage_record":
                    continue
                payload = obj.get("payload")
                stamp = obj.get("timestamp")
                if not isinstance(payload, dict) or not isinstance(stamp, str):
                    continue
                usage = payload.get("usage")
                if not isinstance(usage, dict):
                    continue
                tokens = usage.get("total_tokens")
                if not isinstance(tokens, int) or tokens < 0:
                    continue
                moment = _moment(stamp)
                per_day[moment.date().isoformat()] += tokens
                responses += 1
                session_files.add(path)
                if last_activity is None or moment > last_activity:
                    last_activity = moment

    if responses == 0:
        raise CodexUsageError("no token usage records found")

    days = []
    window_total = 0
    for offset in range(WINDOW_DAYS - 1, -1, -1):
        day = today - timedelta(days=offset)
        tokens = per_day.get(day.isoformat(), 0)
        days.append({"date": day.strftime("%m-%d"), "tokens": tokens})
        window_total += tokens

    payload: dict[str, Any] = {
        "today_tokens": per_day.get(today.isoformat(), 0),
        "week_tokens": window_total,
        "total_tokens": sum(per_day.values()),
        "responses": responses,
        "sessions": len(session_files),
        "last_activity": last_activity.strftime("%m-%d %H:%M") if last_activity else None,
        "days": days,
        "source": "codex-sessions",
    }
    if latest_rate is not None:
        stamp, rate = latest_rate
        primary = rate.get("primary") if isinstance(rate.get("primary"), dict) else {}
        payload["used_percent"] = primary.get("used_percent")
        payload["window_minutes"] = primary.get("window_minutes")
        reset = primary.get("resets_at")
        if isinstance(reset, (int, float)):
            payload["resets_at"] = datetime.fromtimestamp(reset, CST).strftime("%m-%d")
        payload["plan"] = rate.get("plan_type")
        payload["quota_at"] = _moment(stamp).strftime("%m-%d %H:%M")
    return payload


def post_payload(host: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = host.rstrip("/") + "/api/pages/codex/usage"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://127.0.0.1:8000")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    args = parser.parse_args(argv)

    try:
        payload = summarize(Path(args.codex_home), datetime.now(CST))
        result = post_payload(args.host, payload)
    except (CodexUsageError, OSError, ValueError, urllib.error.URLError) as error:
        print(f"sync failed: {error}", file=sys.stderr)
        return 1
    print(
        "synced r{revision}: today={today} week={week} total={total}".format(
            revision=result.get("revision"),
            today=payload["today_tokens"],
            week=payload["week_tokens"],
            total=payload["total_tokens"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
