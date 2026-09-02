"""Adapter for panel-shaped JSON files on disk."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.base import AdapterResult, BaseDataAdapter


class LocalJSONAdapter(BaseDataAdapter):
    adapter_type = "local_json"

    def __init__(self, config, *, root: Path, clock=None) -> None:
        super().__init__(config, clock=clock)
        self.root = root.resolve()

    def fetch(self) -> AdapterResult:
        try:
            path = self._resolve_path(str(self.config.get("path") or ""))
            payload = json.loads(path.read_text(encoding="utf-8"))
            return self.success_result(payload)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return self.failure_result(exc)

    def _resolve_path(self, configured_path: str) -> Path:
        path = (self.root / configured_path).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError("Local JSON path must stay inside the project")
        return path
