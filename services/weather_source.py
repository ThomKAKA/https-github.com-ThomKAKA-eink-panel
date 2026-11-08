"""Fetch Changsha weather from Open-Meteo and cache it as a page document."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import logging
from threading import Lock
from typing import Any, Callable, Mapping

import httpx

from services.page_state import PageStateStore


logger = logging.getLogger(__name__)
CST = timezone(timedelta(hours=8), "Asia/Shanghai")
WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
WMO_LABELS = {
    0: "晴",
    1: "少云",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾",
    51: "毛毛雨",
    53: "毛毛雨",
    55: "毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "米雪",
    80: "阵雨",
    81: "阵雨",
    82: "强阵雨",
    85: "阵雪",
    86: "阵雪",
    95: "雷雨",
    96: "雷暴",
    99: "雷暴",
}
QUERY = {
    "current": "temperature_2m,weather_code",
    "hourly": "temperature_2m,weather_code",
    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
    "timezone": "Asia/Shanghai",
    "forecast_days": 3,
}


class WeatherFetchError(ValueError):
    """The upstream response could not produce a complete document."""


def weather_label(code: int) -> str:
    return WMO_LABELS.get(code, "未知")


class WeatherSource:
    """One Open-Meteo client with a last-known-good page cache."""

    def __init__(
        self,
        store: PageStateStore,
        config: Mapping[str, Any],
        *,
        client: httpx.Client | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._config = dict(config)
        self._client = client
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._stale_after = timedelta(minutes=int(self._config.get("stale_after_minutes", 90)))
        self._lock = Lock()

    def fetch_document(self) -> dict[str, Any]:
        payload = self._request()
        try:
            return self._parse(payload)
        except WeatherFetchError:
            raise
        except (KeyError, TypeError, ValueError) as error:
            raise WeatherFetchError("weather payload invalid") from error

    def refresh(self) -> dict[str, Any]:
        with self._lock:
            document = self._store.load("weather")
            try:
                data = self.fetch_document()
            except WeatherFetchError as error:
                stale = bool(document.data.get("stale", True))
                if not stale and self._aged_out(document):
                    payload = dict(document.data)
                    payload["stale"] = True
                    document = self._store.save("weather", payload, document.revision)
                    stale = True
                    logger.warning("Weather data is stale; serving the last good frame")
                return {
                    "ok": False,
                    "stale": stale,
                    "revision": document.revision,
                    "updated_at": document.updated_at,
                    "error": str(error) or "weather refresh failed",
                }
            saved = self._store.save("weather", data, document.revision)
            return {
                "ok": True,
                "stale": False,
                "revision": saved.revision,
                "updated_at": saved.updated_at,
                "error": None,
            }

    def _request(self) -> dict[str, Any]:
        url = str(self._config.get("url") or "")
        if not url.startswith("https://"):
            raise WeatherFetchError("weather URL must be HTTPS")
        params = dict(QUERY)
        params["latitude"] = self._config.get("latitude", 28.2282)
        params["longitude"] = self._config.get("longitude", 112.9388)
        timeout = float(self._config.get("timeout_seconds", 8))
        owns_client = self._client is None
        # A malformed NO_PROXY on the operator machine breaks httpx environment parsing;
        # this Host talks to the public API directly, never through an HTTP proxy.
        client = self._client or httpx.Client(trust_env=False)
        try:
            response = client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise WeatherFetchError("weather request failed") from error
        finally:
            if owns_client:
                client.close()

    def _parse(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        now = self._now()
        current = payload["current"]
        current_temp = self._celsius(current["temperature_2m"])
        current_code = int(current["weather_code"])

        hourly = payload["hourly"]
        times = hourly["time"]
        temps = hourly["temperature_2m"]
        codes = hourly["weather_code"]
        if not (len(times) == len(temps) == len(codes)):
            raise WeatherFetchError("hourly arrays mismatch")
        current_hour = now.strftime("%Y-%m-%dT%H:00")
        start = next((index for index, value in enumerate(times) if value >= current_hour), None)
        if start is None or start + 8 > len(times):
            raise WeatherFetchError("hourly window unavailable")
        window = [
            {
                "hour": int(times[index][11:13]),
                "temp": self._celsius(temps[index]),
                "label": weather_label(int(codes[index])),
            }
            for index in range(start, start + 8)
        ]

        daily = payload["daily"]
        days = daily["time"]
        highs = daily["temperature_2m_max"]
        lows = daily["temperature_2m_min"]
        day_codes = daily["weather_code"]
        if not (len(days) == len(highs) == len(lows) == len(day_codes)) or len(days) < 3:
            raise WeatherFetchError("daily arrays mismatch")
        forecast = []
        for index in range(3):
            day = date.fromisoformat(days[index])
            forecast.append(
                {
                    "date": f"{day.month:02d}-{day.day:02d}",
                    "weekday": WEEKDAYS[day.weekday()],
                    "high": self._celsius(highs[index]),
                    "low": self._celsius(lows[index]),
                    "label": weather_label(int(day_codes[index])),
                }
            )

        return {
            "city": str(self._config.get("city") or "长沙"),
            "current_temp": current_temp,
            "current_label": weather_label(current_code),
            "hourly": window,
            "daily": forecast,
            "stale": False,
            "source": "open-meteo",
        }

    def _aged_out(self, document) -> bool:
        if not document.updated_at:
            return True
        try:
            stamp = datetime.strptime(document.updated_at, "%Y-%m-%d %H:%M").replace(tzinfo=CST)
        except ValueError:
            return True
        return self._now() - stamp >= self._stale_after

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(CST)

    @staticmethod
    def _celsius(value: Any) -> int:
        number = float(value)
        if number != number or number < -50 or number > 60:
            raise WeatherFetchError("temperature out of range")
        return int(round(number))
