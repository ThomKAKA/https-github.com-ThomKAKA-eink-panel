from datetime import datetime

import httpx

from adapters.http_json import HTTPJSONAdapter


def fixed_clock() -> datetime:
    return datetime(2026, 8, 31, 12, 34, 56)


def make_adapter(handler) -> HTTPJSONAdapter:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return HTTPJSONAdapter(
        {
            "panel": "stats",
            "label": "HTTP JSON",
            "url": "http://test.local/stats",
            "timeout": 5,
        },
        clock=fixed_clock,
        client=client,
    )


def test_http_json_adapter_fetches_object() -> None:
    adapter = make_adapter(
        lambda request: httpx.Response(200, json={"primary_value": "258.42M"})
    )

    result = adapter.fetch()

    assert result.success is True
    assert result.data["primary_value"] == "258.42M"
    assert result.source == "HTTP JSON"


def test_http_json_adapter_handles_http_error() -> None:
    adapter = make_adapter(lambda request: httpx.Response(500, json={"error": "down"}))

    result = adapter.fetch()

    assert result.success is False
    assert result.error == "HTTP 500"


def test_http_json_adapter_handles_invalid_json() -> None:
    adapter = make_adapter(
        lambda request: httpx.Response(
            200,
            content=b"not-json",
            headers={"content-type": "application/json"},
        )
    )

    result = adapter.fetch()

    assert result.success is False
    assert result.error == "HTTP response was not valid JSON"


def test_http_json_adapter_handles_timeout() -> None:
    def timeout_handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    adapter = make_adapter(timeout_handler)

    result = adapter.fetch()

    assert result.success is False
    assert result.error == "HTTP request timed out"


def test_http_json_adapter_handles_connection_failure_without_leaking_url() -> None:
    def connection_handler(request):
        raise httpx.ConnectError("secret failure", request=request)

    client = httpx.Client(transport=httpx.MockTransport(connection_handler))
    adapter = HTTPJSONAdapter(
        {
            "panel": "stats",
            "label": "HTTP JSON",
            "url": "http://test.local/stats?token=private-value",
        },
        clock=fixed_clock,
        client=client,
    )

    result = adapter.fetch()

    assert result.success is False
    assert result.error == "HTTP connection failed"
    assert "private-value" not in result.error


def test_http_json_adapter_rejects_json_array() -> None:
    adapter = make_adapter(lambda request: httpx.Response(200, json=[]))

    result = adapter.fetch()

    assert result.success is False
    assert result.error == "HTTP JSON payload must be an object"


def test_http_json_adapter_rejects_non_http_url() -> None:
    adapter = HTTPJSONAdapter(
        {"url": "file:///tmp/data.json"},
        clock=fixed_clock,
    )

    result = adapter.fetch()

    assert result.success is False
    assert "http://" in result.error
