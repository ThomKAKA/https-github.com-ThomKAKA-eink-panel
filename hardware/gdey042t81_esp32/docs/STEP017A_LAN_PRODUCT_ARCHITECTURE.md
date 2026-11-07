# STEP017A — LAN Product Architecture

Status: DESIGN FREEZE COMPLETE. Implementation, network tests, builds and LAN physical validation: NOT RUN.

## 1. Pre-flight and verified baseline

Expected and actual parent HEAD: `37f80a69470a91a921c7b8b8db4e29032ae14840`.
Pre-flight: PASS; index empty; initial status only `?? hardware/evidence/`.
[PROJECT_STATE](../../../PROJECT_STATE.md), [physical audit](STEP016D_C_PHYSICAL_AUDIT.md) and [evidence manifest](STEP016D_C_EVIDENCE_MANIFEST.md) agree: STEP016D-C physical business page PASS (limited scope), evidence closure COMPLETE.
Offline Progress Display has verified upload, five business fields, readable Chinese, physical orientation and stable final page without obvious clipping, overlap or black artifacts.
The manifest explicitly leaves a copied upload-log file hash unrecorded; this freeze does not invent it or recertify evidence. Historical D-A/B2B NOT RUN entries describe their original stages, not current physical status.

H0 PASS and H1 PASS (limited scope) remain unchanged. BUSY fault injection, Deep Sleep, Partial/Fast Refresh and long-duration operation remain NOT TESTED. Exact physical FULL invocation count is NOT independently verified. Network business-data delivery is NOT RUN; NETWORK PRODUCT FUNCTION VERIFIED=NO.

## 2. Product problem and minimum solution

STEP016 requires a new frame, firmware build and USB upload for changed business content. STEP017 must deliver changed final display bytes over LAN without rebuilding or uploading firmware for each update.
Selected product: **LAN Connected Progress Terminal**. Host owns business state and final bytes; ESP32 validates a complete candidate and only a valid changed frame may request display. Network failure must not destroy the current physical image.
This is a low-frequency host-rendered terminal, not a cloud, account, realtime messaging or general IoT platform.

## 3. Read-only repository/API audit

[Server](../../../server/main.py) uses existing FastAPI, Uvicorn and Response/JSONResponse/FileResponse. Pinned dependencies in [requirements](../../../requirements.txt) include FastAPI 0.116.1, Uvicorn 0.35.0, Pillow 11.3.0 and Pydantic 2.11.7. No new framework or dependency is required.

| Existing route | Current responsibility |
| --- | --- |
| GET `/` and mounted `/static` | Existing simulator UI/static files, not a new STEP017 UI |
| GET `/api/samples/{panel_type}` | Samples |
| GET `/api/data-sources/{panel_type}` | Configured sources |
| POST `/api/data-sources/{source_id}/refresh` | Existing adapter refresh |
| POST `/api/events` | Validate and ingest panel.update event |
| GET `/api/events/snapshots/{panel_type}/{source}` | Read one stored snapshot |
| POST `/api/panels/{panel_type}/render` | Render supplied data to PNG/BMP |

FastAPI also supplies its default schema/documentation routes; they are not device frame interfaces. The separate [development mock server](../../../examples/http_server.py) has GET `/progress`, `/stats`, `/flow`; it changes data/time per request and is not the product publisher.

[EventStateStore](../../../services/event_store.py) normalizes through create_panel, keeps copied snapshots keyed by `(panel, source)` under a lock, detects duplicate/out-of-order events and is process-local. There is no separate persistent Panel State service. Existing tests manually connect ingestion, snapshot GET and render POST; there is no automatic T publication or existing ETag implementation.
The render endpoint already returns binary Response with custom headers, but accepts general preview configuration and is not the fixed device contract.

Reuse [ProgressPanel](../../../panels/progress.py), its strict font/layout path demonstrated by [offline renderer](../../../panels/offline_progress.py), [PNG-to-L function](../../../panels/frame_converter.py) and [L-to-T function](../../../panels/transport_adapter.py). Existing file CLIs/manifests remain stage artifacts; LAN publishing must not require creating C arrays or invoking those CLIs per request.
Existing ordinary adapters have timestamp fallback; future Host mapping must use snapshot data/time before rendering, never poll time. STEP016 offline JSON field aliases are not automatically the event schema. Preserve existing POST event contract and map its snapshot to ProgressPanelData on the Host. No automatic fallback to mock/local data if the configured event source is missing.

## 4. Communication decision

| Approach | Low-frequency/Host rendering | Complexity, faults and synchronization | Testing, maintenance, infrastructure | H1/LKG compatibility |
| --- | --- | --- | --- | --- |
| HTTP Pull, selected | Fetch final bytes when polled | Bounded request/response; latest frame identity | Reuse server; straightforward contract fixtures; no broker | Separate validation from display; retain LKG |
| WebSocket Push | Possible but unnecessary immediacy | Persistent connection, reconnect/resync and backpressure | More connection-state tests and maintenance | Can preserve LKG but adds no display-safety benefit |
| MQTT | Possible with binary payload | Broker, subscription, delivery/replay semantics | Extra infrastructure and operational tests | Still requires complete-frame validation and LKG |
| MCU business JSON/rendering | Violates Host-rendered objective | Domain, fonts, layout and timestamp logic on MCU | Duplicated rendering stack and resource testing | Discards verified rendering separation |

Freeze LAN + Wi-Fi Station + HTTP Pull + bounded polling. No WebSocket, MQTT, SSE or new event bus.

## 5. Data flow and responsibilities

```text
Agent / Script → existing POST /api/events → EventStateStore Progress snapshot
→ Host business mapping → ProgressPanel/Pillow strict L rendering
→ existing L encoding → PC L-to-T adapter → complete validated atomic T publication
→ LAN HTTP GET → ESP32 complete receive/validation/change detection
→ display handoff → standard FULL foundation → GDEY042T81
```

Host selects exactly one explicitly configured event source. Other sources do not compete for the terminal; no newest-across-sources rule or device source switching. A missing source setting is a deployment error, not an implicit default. Future source changes require controlled Host reconfiguration, not a new device API.
Host owns events, business JSON, snapshot time, fonts, layout, Chinese, L/T generation and publication. ESP32 owns LAN connection, final-byte request, HTTP validation, complete buffering and identity comparison. ESP32 must not parse business JSON, contact the Agent, understand panel fields, render UI/fonts or transform orientation.
T remains 400x300/15000 bytes, stride 50, MSB-first, 0 black/1 white. Renderer/B1 keep L; PC reverses rows once; MCU preserves T; fixed H1 mirror maps P=L. See [direction rule](STEP016D_B2A_TRANSPORT_FRAME_RULE.md).

## 6. H1 relationship and mandatory future gate

[H1 adapter](../src/h1/atomic_display.h) is one-shot: refreshOnce consumes the object into Finished. [STEP016 display flow](STEP016D_DISPLAY_FLOW.md) stops all display commands after refresh, including successful refresh. It cannot simply be called repeatedly by a polling loop.
User-approved boundary: STEP017C must independently freeze continuous-update lifecycle, display acceptance and failure stop rules before STEP017D implementation. This is a scheduled future gate, not a claim of an implemented reusable lifecycle. No reset/reinitialization, object reconstruction or dependency patch is selected or authorized here.
Preserve frozen H1 source/history and its standard-FULL/complete-RAM/direction foundation. Future success-path repeated updates need separate approval; timeout/unknown must never cause automatic display retry. Network polling does not grant permission to bypass Finished or issue broad driver calls. See [failure policy](STEP017A_UPDATE_AND_FAILURE_POLICY.md).

## 7. Related frozen decisions and exclusions

Official endpoint and bytes: [HTTP contract](STEP017A_FRAME_HTTP_CONTRACT.md). Security/addressing: [security boundary](STEP017A_NETWORK_SECURITY_BOUNDARY.md). Stage gates: [test plan](STEP017A_STAGE_TEST_PLAN.md).
Excluded: cloud/public Internet, remote accounts/control, mobile app/new dashboard, multiple-panel switching, Stats/Flow network productization, broker/SSE, Partial/Fast Refresh, Deep Sleep/hibernate optimization, battery operation, OTA/dynamic firmware update, NVS frame persistence, provisioning UI/captive portal, mDNS/discovery, touch, microSD, device registry and complex automatic recovery.
