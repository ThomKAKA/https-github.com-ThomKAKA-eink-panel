"""Adapter for simple HTTP endpoints that return panel-shaped JSON."""

from __future__ import annotations

import json

import httpx

from adapters.base import AdapterResult, BaseDataAdapter


class HTTPJSONAdapter(BaseDataAdapter):
    adapter_type = "http_json"

    def __init__(self, config, *, clock=None, client: httpx.Client | None = None) -> None:
        super().__init__(config, clock=clock)
        self._client = client

    def fetch(self) -> AdapterResult:
        url = str(self.config.get("url") or "")
        if not url.startswith(("http://", "https://")):
            return self.failure_result("HTTP URL must start with http:// or https://")

        try:
            timeout = float(self.config.get("timeout") or 5)
            if self._client is not None:
                response = self._client.get(url, timeout=timeout)
            else:
                with httpx.Client() as client:
                    response = client.get(url, timeout=timeout)
            response.raise_for_status()
            return self.success_result(response.json())
        except httpx.TimeoutException:
            return self.failure_result("HTTP request timed out")
        except httpx.ConnectError:
            return self.failure_result("HTTP connection failed")
        except httpx.HTTPStatusError as exc:
            return self.failure_result(f"HTTP {exc.response.status_code}")
        except json.JSONDecodeError:
            return self.failure_result("HTTP response was not valid JSON")
        except httpx.HTTPError:
            return self.failure_result("HTTP request failed")
        except (ValueError, TypeError) as exc:
            if str(exc) == "JSON payload must be an object":
                return self.failure_result("HTTP JSON payload must be an object")
            return self.failure_result("HTTP adapter configuration is invalid")
