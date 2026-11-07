# STEP017A — Update and Failure Policy

Status: DESIGN FROZEN; runtime implementation and tests NOT RUN.
Applies to the [HTTP contract](STEP017A_FRAME_HTTP_CONTRACT.md) and [LAN architecture](STEP017A_LAN_PRODUCT_ARCHITECTURE.md).

## 1. Polling is not refreshing

Product default polling interval: 60 seconds, configurable later; not an immutable wire protocol constant. Polling must be bounded, non-overlapping and without catch-up bursts or unbounded fast retries. Concrete timeout milliseconds, reconnect/backoff APIs, buffer classes and tasks are STEP017C work.

| Result | Product action |
| --- | --- |
| Valid conditional 304 | No new frame; zero display operations |
| Complete valid 200, accepted identity unchanged | Discard redundant candidate; zero display operations |
| Complete valid 200, changed identity | Eligible for display handoff only after lifecycle gate |
| Network/HTTP/transport validation failure | Reject; zero display operations; retain physical image |
| Display rejects or TIMEOUT/UNKNOWN | Do not advance identity; no automatic display retry; stop display progression |

One changed candidate must not create an unconditional refresh loop. Intermediate business states may coalesce into the latest publication; this is a latest-state display, not an event replay terminal.

## 2. Last Known Good and acceptance boundary

Last Known Good (LKG) is the last frame completely received, transport-validated and accepted by the display chain. Received identity, published identity and accepted identity are distinct. Only accepted identity may be used for device conditional requests/change suppression.
Network failure covers Wi-Fi loss, DNS failure, unreachable Host, connection failure/timeout, HTTP timeout, 4xx/5xx, malformed identity/metadata, wrong type/length, truncation, oversize and incomplete response. Reject candidate, retain accepted identity and current physical image. Never clear white/black, draw an ERROR page, refresh the old frame to indicate failure or hand partial data to GxEPD2.
Physical image retention on network failure does not prove electrical health or actual controller state. Once a display operation has started, an uncertain result cannot guarantee that the previous physical image survived; no software rollback or automatic repair is claimed.

Existing H1 refreshOnce returning true only reports the one-shot invocation; it does not certify BUSY success. Its elapsed/BUSY checks are conservative software conditions, not physical display PASS. STEP017C must define exactly when display acceptance advances LKG and how rejection/unknown stops future display commands. No automatic next-poll retry of a failed display candidate is permitted. Network activity alone must never clear that display stop condition.

## 3. Cold boot and restart

Physical e-paper content can persist while MCU in-memory identity is lost. No NVS, filesystem or Flash identity persistence is included. On cold boot/reset, device starts without an accepted ETag, fetches unconditionally, and may refresh the first valid frame even if physically identical to the retained image.
If the network or Host is unavailable at boot, leave the retained physical image untouched. No fallback embedded error/blank page. Actual cold-boot/repeated-update behavior remains future verification, not inherited H1 PASS.

## 4. Host publication atomicity

Future STEP017B pipeline: capture the configured source snapshot → map business data/time → strict render L → encode L → convert T → validate all 15000 bytes → compute ETag → atomically publish.
Existing POST /api/events acceptance acknowledges event storage, not frame publication or display. Rendering/font/layout failure may reject publication even after valid event ingestion; do not change existing event API meaning.

| Method | Benefits | Costs / decision |
| --- | --- | --- |
| Immutable in-memory publication record, synchronized replacement | Fits existing process-local EventStateStore; body/identity/metadata captured together | Selected; single serving process only, no persistence |
| Temporary file plus atomic replacement | Could support durable file publication | More path/lifetime/recovery complexity; not needed for this MVP |

Readers take one complete publication record; old readers can finish using old immutable bytes. Never derive headers from one version and body from another. No reader sees partial rendering/raw writes or temporary output.
Publication must be conditioned on the source snapshot still being current: an older render completing later cannot overwrite a newer accepted publication. Use source/version checks in the future implementation, with concurrency tests. Source is fixed for the running deployment; unrelated source events cannot replace it.
Failed publication retains the old record; if none exists return 503. Host restart loses process-local snapshots/publication, so no frame is available until a valid event is supplied again. No cross-worker consistency or persistence is claimed; multiple independent serving workers are outside MVP.
Polling must not insert current time into rendered content. Snapshot time is stable, and fixed snapshot/font/render configuration must give stable bytes and ETag. Strict rendering failure must not fall back to a waiting/error graphic.

## 5. Display lifecycle gate

The existing [H1 one-shot adapter](../src/h1/atomic_display.h) and [STEP016 flow](STEP016D_DISPLAY_FLOW.md) remain unchanged. Finished cannot be reset by merely scheduling another poll. STEP017C must separately review repeated standard FULL lifecycle, complete RAM preparation, acceptance and fault-stop behavior before D implements it.
No object recreation, cold reinitialization, successful-path continuation or third-party patch is authorized by this document. STEP017A freezes the product requirement and the mandatory future gate; it does not certify feasibility of any particular lifecycle workaround. See [stage gates](STEP017A_STAGE_TEST_PLAN.md).
