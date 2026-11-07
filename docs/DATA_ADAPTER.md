# DataAdapter

DataAdapter separates data acquisition from panel rendering. Panels only receive dictionaries
that already resemble their panel schema; they never call HTTP endpoints or read files.

```text
Data Source → DataAdapter → RefreshManager → Panel → PNG/BMP
```

## Included adapters

- `MockAdapter`: selects an entry from the existing `examples/*_samples.json` files.
- `LocalJSONAdapter`: reads one panel-shaped JSON object from `data/local/`.
- `HTTPJSONAdapter`: performs a GET request with a configured timeout and accepts JSON objects.

Each adapter returns `success`, `data`, `source`, `fetched_at`, `source_updated_at`, and
`error`. File, HTTP, timeout, and JSON errors become failure results instead of escaping into
the simulator.

## Configuration

Sources live in `config/data_sources.json`. Never put keys, cookies, or tokens in that file.
Future secrets belong in `.env`, which Git ignores.

To add another source of an existing adapter type, add one configuration entry. To add a new
adapter type, implement `BaseDataAdapter` and register it in `adapters/factory.py`.

HTTP JSON must already resemble the target Panel schema. Phase 3 does not scrape HTML,
execute returned code, or guess arbitrary field mappings.

## Failure and semantic validation

Adapters catch file, connection, timeout, HTTP status, and JSON decoding errors and return a
failure result. HTTP error text is categorized without including the full request URL, query
parameters, response body, or credentials.

`RefreshManager` performs the final panel semantic check before accepting adapter data as Last
Known Good. A payload that parses as a JSON object but normalizes to a Panel `waiting` or `error`
state is not cached. Compatible values such as a numeric string for Progress remain accepted by
the existing Pydantic model; Phase 3 does not introduce strict field coercion rules or arbitrary
text-length limits.
