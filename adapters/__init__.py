"""Data adapter implementations for Phase 3."""

from adapters.base import AdapterMetadata, AdapterResult, BaseDataAdapter
from adapters.factory import create_adapter
from adapters.http_json import HTTPJSONAdapter
from adapters.local_json import LocalJSONAdapter
from adapters.mock import MockAdapter

__all__ = [
    "AdapterMetadata",
    "AdapterResult",
    "BaseDataAdapter",
    "HTTPJSONAdapter",
    "LocalJSONAdapter",
    "MockAdapter",
    "create_adapter",
]
