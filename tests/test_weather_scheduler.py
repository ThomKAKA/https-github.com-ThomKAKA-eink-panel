"""Weather refresh thread lifecycle and hourly target."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from services.weather_scheduler import WeatherScheduler


CST = timezone(timedelta(hours=8))


class FakeThread:
    instances: list["FakeThread"] = []

    def __init__(self, *, target, name, daemon):
        self.target = target
        self.name = name
        self.daemon = daemon
        self.started = False
        self.joined = None
        FakeThread.instances.append(self)

    def start(self):
        self.started = True

    def join(self, timeout=None):
        self.joined = timeout


class FakeStop:
    def __init__(self, waits):
        self.waits = list(waits)
        self.delays = []

    def is_set(self):
        return False

    def wait(self, seconds):
        self.delays.append(seconds)
        return self.waits.pop(0) if self.waits else True

    def set(self):
        pass


def build(now):
    FakeThread.instances = []
    source = Mock()
    scheduler = WeatherScheduler(source, clock=lambda: now, thread_factory=FakeThread)
    return source, scheduler


def test_start_creates_one_daemon_thread():
    _, scheduler = build(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    scheduler.start()
    scheduler.start()
    assert len(FakeThread.instances) == 1
    thread = FakeThread.instances[0]
    assert thread.name == "eink-weather" and thread.daemon is True and thread.started is True


def test_run_refreshes_once_before_stopping():
    source, scheduler = build(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    scheduler.start()
    scheduler._stop = FakeStop([True])
    scheduler._run()
    source.refresh.assert_called_once_with()
    assert scheduler._stop.delays == [2405.0]


def test_close_sets_stop_and_joins():
    _, scheduler = build(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    scheduler.start()
    scheduler.close()
    assert FakeThread.instances[0].joined == 2.0
    scheduler.close()
    assert FakeThread.instances[0].joined == 2.0


def test_delay_waits_for_the_next_hour():
    _, scheduler = build(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    assert scheduler.delay_seconds() == 2405.0
    _, late = build(datetime(2026, 11, 8, 14, 59, 30, tzinfo=CST))
    assert late.delay_seconds() == 60.0


def test_refresh_failure_does_not_break_the_thread():
    source, scheduler = build(datetime(2026, 11, 8, 14, 20, tzinfo=CST))
    source.refresh.side_effect = RuntimeError("down")
    scheduler.start()
    scheduler._stop = FakeStop([True])
    scheduler._run()
    source.refresh.assert_called_once_with()
