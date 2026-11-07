"""Adapter for the existing sample JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.base import AdapterResult, BaseDataAdapter


class MockAdapter(BaseDataAdapter):
    adapter_type = "mock"

    def __init__(self, config, *, root: Path, clock=None) -> None:
        super().__init__(config, clock=clock)
        self.root = root.resolve()

    def fetch(self) -> AdapterResult:
        try:
            path = self._resolve_path(str(self.config.get("path") or ""))
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                sample_id = str(self.config.get("sample_id") or "default")
                sample = next(
                    (item for item in payload if str(item.get("id")) == sample_id),
                    None,
                )
                if sample is None:
                    raise ValueError(f"Unknown sample id: {sample_id}")
                payload = sample.get("data")
            return self.success_result(payload)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return self.failure_result(exc)

    def _resolve_path(self, configured_path: str) -> Path:
        path = (self.root / configured_path).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError("Mock path must stay inside the project")
        return path
