"""Common DataAdapter contract and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Mapping


Clock = Callable[[], datetime]


def format_timestamp(clock: Clock) -> str:
    return clock().astimezone().strftime("%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class AdapterMetadata:
    adapter_type: str
    panel_type: str
    source: str


@dataclass(frozen=True)
class AdapterResult:
    success: bool
    data: dict[str, Any] | None
    source: str
    fetched_at: str
    source_updated_at: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseDataAdapter(ABC):
    adapter_type = "base"

    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        clock: Clock | None = None,
    ) -> None:
        self.config = dict(config)
        self._clock = clock or datetime.now
        self.panel_type = str(self.config.get("panel") or "")
        self.source = str(self.config.get("label") or self.config.get("source") or self.adapter_type)

    @abstractmethod
    def fetch(self) -> AdapterResult:
        """Fetch and normalize one data payload without leaking exceptions."""

    def normalize(self, raw_data: Any) -> dict[str, Any]:
        if not isinstance(raw_data, Mapping):
            raise ValueError("JSON payload must be an object")
        data = dict(raw_data)
        fetched_at = format_timestamp(self._clock)
        if not data.get("source"):
            data["source"] = self.source
        if data.get("updated_at") is None or not str(data.get("updated_at", "")).strip():
            data["updated_at"] = fetched_at
        return data

    def health_check(self) -> dict[str, Any]:
        result = self.fetch()
        return {
            "healthy": result.success,
            "source": result.source,
            "checked_at": result.fetched_at,
            "error": result.error,
        }

    def get_metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_type=self.adapter_type,
            panel_type=self.panel_type,
            source=self.source,
        )

    def success_result(self, raw_data: Any) -> AdapterResult:
        fetched_at = format_timestamp(self._clock)
        source_updated_at = None
        if isinstance(raw_data, Mapping):
            raw_time = raw_data.get("updated_at")
            if raw_time is not None and str(raw_time).strip():
                source_updated_at = str(raw_time)
        return AdapterResult(
            success=True,
            data=self.normalize(raw_data),
            source=self.source,
            fetched_at=fetched_at,
            source_updated_at=source_updated_at,
        )

    def failure_result(self, error: Exception | str) -> AdapterResult:
        return AdapterResult(
            success=False,
            data=None,
            source=self.source,
            fetched_at=format_timestamp(self._clock),
            error=str(error),
        )
