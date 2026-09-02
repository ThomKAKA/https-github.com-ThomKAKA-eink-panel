"""Factory for configured DataAdapter implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import httpx

from adapters.base import BaseDataAdapter, Clock
from adapters.http_json import HTTPJSONAdapter
from adapters.local_json import LocalJSONAdapter
from adapters.mock import MockAdapter


def create_adapter(
    config: Mapping[str, Any],
    *,
    root: Path,
    clock: Clock | None = None,
    http_client: httpx.Client | None = None,
) -> BaseDataAdapter:
    adapter_type = str(config.get("type") or "")
    if adapter_type == "mock":
        return MockAdapter(config, root=root, clock=clock)
    if adapter_type == "local_json":
        return LocalJSONAdapter(config, root=root, clock=clock)
    if adapter_type == "http_json":
        return HTTPJSONAdapter(config, clock=clock, client=http_client)
    raise ValueError(f"Unknown adapter type: {adapter_type}")
