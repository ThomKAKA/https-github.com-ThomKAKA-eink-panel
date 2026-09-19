# PROJECT_STATE.md

> Project fact source for Codex continuation.
>
> This file records frozen project state, verification boundaries, current phase,
> and execution constraints.
>
> Update this file only when a project phase is completed or frozen.

---

# 1. Project Identity

Project:
eink-panel

Hardware Target:

- ESP32-M1
- GDEY042T81
- SSD1683 e-paper controller
- USB-SERIAL CH340


Display:

- Resolution: 400×300
- Current verified path: FULL refresh only


Development Environment:

- PlatformIO
- Arduino Framework
- GxEPD2


---

# 2. Current Phase

Current Stage:

STEP017C ESP32 NETWORK FETCHER DESIGN FREEZE: COMPLETE


Current Objective:

Host on-demand Progress T publication and HTTP conditional delivery implemented;
in-process software verification complete. STEP017C network/state/session design
is frozen; STEP017D implementation, compilation and LAN physical verification
are NOT RUN. Stop before STEP017D.
STEP016D-C physical business page remains PASS (limited scope), with evidence
closure COMPLETE. No historical hardware verification scope is changed.


---

# 3. Completed Milestones


## STEP014 H0 Hardware Validation

Status:

PASS


Commit:

f24d0c0e3ffdf178fb05fe226e71406dd7461b30


Verified:

- ESP32-M1 display chain
- GDEY042T81 response
- Geometry direction validation


Scope limitation:

H0 does NOT prove:

- product functionality
- partial refresh
- deep sleep
- long-term stability



---

## STEP015 H1 Physical Validation

Status:

PASS (limited scope)


Commits:

STEP015B1:

55e32b5e788d762cc3a08587ccceb45e457bed20


STEP015C:

85e2c4bb64561e55d27b42f215e1235b123a6ae8


Verified:

- esp32-m1-h1 firmware upload
- COM11 upload path
- GDEY042T81 display response
- single FULL refresh observation


Evidence:

Local only:

hardware/evidence/


Not committed:

- photos
- upload logs
- raw evidence


---

## STEP016B Interface Freeze

Status:

STEP016B INTERFACE FREEZE = COMPLETE


Commit:

f8bf7ae8270aa34d58cb3006f6ab44db2792fd5c


Created documents:

Directory: hardware/gdey042t81_esp32/docs/

- STEP016B_JSON_SCHEMA.md
- STEP016B_RENDER_INTERFACE.md
- STEP016B_DISPLAY_ENTRY.md
- STEP016B_PAGE_LAYOUT.md
- STEP016B_TEST_PLAN.md


Status and execution boundary:

- Interfaces frozen
- Function implementation NOT RUN
- Tests NOT RUN
- No source/config changes
- No hardware operation
- No push/tag


---

# 4. Hardware Verification Boundary


Current status:


H0:

PASS

(scope: display chain and geometry)


H1 STATIC:

PASS


H1 PHYSICAL:

PASS (limited scope)


PRODUCT FUNCTION VERIFIED:

YES (Offline Progress Display, limited scope)


---

# 5. Not Tested


The following MUST remain NOT TESTED:


## Refresh

- Partial Refresh
- Fast Refresh


## Power

- Deep Sleep
- Hibernate
- Wake recovery


## Reliability

- Long duration operation
- Repeated refresh endurance


## Failure Handling

- BUSY timeout fault injection
- Automatic recovery


Do not describe these features as verified.


---

# 6. Current Product Decision

Selected STEP017 Product:

LAN Connected Progress Terminal (Host complete; device design frozen; device/LAN verification NOT RUN).
NETWORK PRODUCT FUNCTION VERIFIED: NO.

The following selected/verified version remains the STEP016 offline baseline:

Selected Product Version:

Offline Progress Display


Goal:

Create an offline electronic paper progress/status terminal.


Display content:

- project progress
- current step
- status
- snapshot timestamp
- Chinese text


---

# 7. Frozen Architecture

STEP017A design: Host renders final T frame from one configured Progress event
source; ESP32 fetches/validates complete T bytes over LAN HTTP. It does not parse
business JSON or render UI. Existing H1 standard FULL path remains the display
foundation, but its one-shot object is NOT directly reusable for continuous
updates. STEP017C freezes fresh per-frame sessions and a terminal fault-stop gate;
their implementation and repeated-session verification remain NOT RUN.

Sections 7-9 below describe the preserved STEP016 implementation baseline, not
an implemented LAN architecture. STEP017A contracts are linked in section 15.

Data Flow:


Local JSON

↓

Python Adapter

↓

ProgressPanel

↓

Pillow Renderer

↓

400×300 Bitmap

↓

Build-time Embedded Frame

↓

ESP32 Display Entry

↓

GDEY042T81 FULL Refresh



---

# 8. Module Responsibilities


## Python Side


Responsible for:

- business data
- JSON processing
- layout
- Chinese font rendering
- bitmap generation


Existing components:

- Python data adapters
- ProgressPanel
- Stats panel
- Flow panel
- Pillow Renderer


---

## ESP32 Side


Responsible only for:

- initialization
- loading complete frame
- display refresh


ESP32 MUST NOT:

- parse JSON
- render UI
- handle fonts
- generate images
- fetch network frames


---

# 9. Current Refresh Strategy


Frozen:

FULL Refresh only


Current flow:


init

↓

load bitmap

↓

single FULL refresh

↓

stop


Forbidden:

- refresh loop
- automatic retry
- partial refresh
- fast refresh


---

# 10. STEP016 Scope


## Status

- STEP016B INTERFACE FREEZE = COMPLETE
- Interfaces frozen
- STEP016C COMPLETE; Renderer implementation and Renderer-only review completed
- STEP016D-A DESIGN FREEZE COMPLETE; design documents only
- STEP016D-B1 logical raw/header converter: COMPLETE (84886cc15af2bec7d220e062865450927fcfaacc)
- STEP016D-B2A transport rule and math verification: COMPLETE (e1fa8b94f357d5878ffedc4b0ac94421fbea5fb8)
- STEP016D-B2B transport adapter, dedicated embedded entry and compilation: COMPLETE
- Python regression: 311 passed (270 existing + 41 new), 3.00s
- Four environments compiled; isolated negative compiler checks passed
- STEP016D-C physical business page validation: PASS (limited scope)
- STEP016D-C EVIDENCE CLOSURE: COMPLETE


## Included


- Local JSON schema
- Python → Bitmap interface
- ESP32 display entry interface
- Page layout specification
- Renderer validation


## Excluded


- WiFi
- HTTP
- Network update
- Polling
- Partial refresh
- Fast refresh
- Deep Sleep
- Auto recovery
- Long-term running test


---

# 11. Current Task

STEP017C ESP32 NETWORK FETCHER DESIGN FREEZE: COMPLETE

Six design documents only; source/configuration unchanged. Current decisions and
remaining gates are in section 17. STEP017D implementation is next, NOT RUN.
No executable tests, compilation, server, serial or hardware operation in C.

## Previous completed stage: STEP017B

STEP017B HOST FRAME ENDPOINT IMPLEMENTATION: COMPLETE

Host-only service and GET route; 311 existing + 53 new tests = 364 passed.
See the STEP017B report and current results in section 16. No real network,
firmware or hardware execution. STEP017C lifecycle design remains NOT RUN.

## Previous completed stage: STEP017A

STEP017A LAN PRODUCT ARCHITECTURE FREEZE: COMPLETE

Five design documents and state update only. Pre-flight parent HEAD:
37f80a69470a91a921c7b8b8db4e29032ae14840; empty index; only hardware/evidence/
untracked. Document consistency, links and Git checks; executable tests NOT RUN.
Host endpoint/network implementation/build/physical validation NOT RUN.

## Previous completed stage: STEP016D-C

STEP016D-C EVIDENCE CLOSURE: COMPLETE

User-confirmed physical business page validation: PASS (limited scope).
The verified observations and remaining evidence boundaries are recorded at the
end of this file. Multiple visible refresh/flash phases were observed; the exact
physical FULL invocation count is NOT independently verified.
This task only reconciles existing evidence in PROJECT_STATE.md.

## Previous completed stage: STEP016D-B2B

STEP016D-B2B SOFTWARE INTEGRATION AND COMPILATION: COMPLETE

Baseline: e1fa8b94f357d5878ffedc4b0ac94421fbea5fb8.
See [B2B report](hardware/gdey042t81_esp32/docs/STEP016D_B2B_EMBEDDED_FRAME_REPORT.md)
for source chain, exact hashes, call-chain comparison and verification limits.

- Independent PC Adapter validates B1 L raw/header/manifest, reverses rows once to T.
- Dedicated esp32-m1-progress copies the embedded T array to static RAM, reuses H1
  coldInit / prepareColdStartFullFrame / refreshOnce without changing H1.
- Four builds passed: esp32dev, esp32-m1, esp32-m1-h1, esp32-m1-progress.
- Progress RAM 36616 bytes; Flash 294725 bytes. ELF array and RAM buffer each 15000 bytes.
- Existing 270 + new 41 Python tests passed; five negative compiler cases rejected.
- T raw/array SHA256: a243c5740472d3f2f3c09ca440446d2e50b5da0b32bcb00b6ddca533f6084f8d.
- firmware.bin SHA256: 942f7eaa9a7ad6574ee36a05478d085d52440d0578c82ed0457a7c65ac241523.
- Ignored output: artifacts/step016-transport-adapter/step016d-b2b-review/.
- Ignored build/verification logs: artifacts/step016-b2b-build/.
- No new physical verification, serial access or upload; no product PASS.

B1 and B2A intentionally did not update this file. Their completed stages are
now recorded from their committed reports; historical A/B/C records remain below.
At B2B completion, H0/H1 remained unchanged and STEP016D-C had not run;
physical verification then awaited separate authorization.

## Previous completed stage: STEP016D-A

STEP016D-A DESIGN FREEZE: COMPLETE

Baseline: 45ca1dcc0e9043639299621229a223c7f0eca7de (STEP016C finalization).
Frozen design documents in hardware/gdey042t81_esp32/docs/:

- [Bitmap interface](hardware/gdey042t81_esp32/docs/STEP016D_BITMAP_INTERFACE.md)
- [Frame embed decision](hardware/gdey042t81_esp32/docs/STEP016D_FRAME_EMBED_DECISION.md)
- [Display flow](hardware/gdey042t81_esp32/docs/STEP016D_DISPLAY_FLOW.md)
- [Orientation rule](hardware/gdey042t81_esp32/docs/STEP016D_ORIENTATION_RULE.md)
- [Display test plan](hardware/gdey042t81_esp32/docs/STEP016D_DISPLAY_TEST_PLAN.md)

Chosen design: manual PC conversion before compilation, read-only embedded array
copied to a complete static RAM buffer; no runtime PNG/JSON decoder.
Renderer L stays readable; export T flips Y once; fixed H1 flips Y once to P=L.
No extra flip/rotation. New entry/environment remains unimplemented; H1 is unchanged.
Only document checks performed; all new execution tests remain NOT RUN.
No new raw/header, build, upload, serial access or hardware operation.
H0/H1 and PRODUCT FUNCTION VERIFIED=NO retain their historical boundaries.

## Previous completed stage: STEP016C

STEP016C: COMPLETE

Implemented: strict offline adapter, existing ProgressPanel step title, optional
font/layout validation, renderer-only CLI, separate example and 78 new tests.
Ordinary LocalJSONAdapter, Stats/Flow, firmware/configuration and historical A/B
documents remain unchanged. H0/H1 history and PRODUCT FUNCTION VERIFIED=NO remain.

Verification: 125 existing + 78 new tests passed (203 total in 2.06s).
Agent inspected the final 1-bit PNG: Chinese project/step/status, percentage,
description, tags and timestamp readable without observed clipping/overlap.
Renderer-only review passed; the user authorized stage finalization.
This is software/visual verification, not a physical display test.
Glyph checking uses conservative missing-glyph raster comparisons and actual draw
bounds/contrast; it is not exhaustive font cmap or arbitrary-text legibility proof.

Output (ignored, renderer candidate only):
`artifacts/step016-offline-progress/step016c-final-20260913/progress.preview.png`

- 400x300; Pillow mode 1; 1-bit; 1619 bytes; normal reading, no preflip
- SHA256: 538be61374b7804bc64a05dd1eb4f6caca65a778201d2e03ddbae8f7aedb0c2a
- Adjacent `renderer-manifest.json` records input, fonts, draw bounds and tool versions;
  it is NOT the complete STEP016B publication manifest.
- Actual fonts: C:/Windows/Fonts/msyhbd.ttc, msyh.ttc and consolab.ttf; hashes in manifest.
- Reproduce manually with a new unused run-id:
  `.venv/Scripts/python.exe -B -m panels.offline_progress --input data/progress_offline.json --run-id <new-run-id>`

Raw/header export, transmission preflip, firmware integration, build isolation
execution and new hardware validation remain NOT RUN.
Finalization includes only the seven authorized implementation/state files in a
local commit. No push/tag, ESP32 compilation or hardware operation.


---

# 12. Execution Rules for Codex


Before any action:


Read this file first.


Allowed:

- read existing files
- create/update design documents
- run verification commands


Forbidden unless explicitly authorized:

- firmware modification
- hardware operation
- upload
- serial monitor
- changing H0/H1 baseline
- adding network capability


---

# 13. Git Rules


Pre-STEP016D-A-design-freeze HEAD (parent baseline):

45ca1dcc0e9043639299621229a223c7f0eca7de


Commit history:

- STEP015C: 85e2c4bb64561e55d27b42f215e1235b123a6ae8
- STEP016B INTERFACE FREEZE: f8bf7ae8270aa34d58cb3006f6ab44db2792fd5c
- STEP016C FINALIZE: 45ca1dcc0e9043639299621229a223c7f0eca7de
- STEP016D-A: e0eb4df614c6d424327b9bf7ce6022db525147dd
- STEP016D-B1: 84886cc15af2bec7d220e062865450927fcfaacc
- STEP016D-B2A: e1fa8b94f357d5878ffedc4b0ac94421fbea5fb8
- STEP016D-B2B: 07ba02734dd7266d4b6acd37fcc032758b683b76
- STEP016D-C EVIDENCE CLOSURE: 37f80a69470a91a921c7b8b8db4e29032ae14840
- STEP017A LAN ARCHITECTURE FREEZE: 4f5383dda1202f1e09ea48aefdac69e92f4e196d
- STEP017B HOST FRAME ENDPOINT: 9a23df88ed85466f52847c45c20933f942159979


Current expected untracked:

hardware/evidence/

STEP016D-A design freeze commit message:
`docs(hardware): freeze STEP016D display integration design`
The commit containing this state records five design documents and this state file. Resolve its
SHA from Git history; no self-referential commit hash is embedded here.
Artifacts stay ignored; hardware/evidence/ stays local-only and untracked.

The above D-A commit description is historical. Previous B2B local commit message:
`feat(display): integrate embedded progress frame`.
Resolve its SHA from Git history; private configuration/build artifacts remain ignored.


Do not commit:

- raw photos
- raw logs
- hardware evidence


Commit:

- source code
- design documents
- audit documents


---

# 14. Development Philosophy


Follow:

Freeze → Implement → Verify → Document → Commit


Do not combine:

- architecture changes
- feature implementation
- hardware validation

in one step.


---

# STEP016 Completed State (preserved history)
STEP016C:
COMPLETE
STEP016D-A DESIGN FREEZE:
COMPLETE
STEP016D-B1 / B2A / B2B software integration and compilation:
COMPLETE
STEP016D-C PHYSICAL BUSINESS PAGE VALIDATION
PASS (limited scope)

Verified:
- frozen firmware upload PASS on COM11
- business Progress page displayed on GDEY042T81
- expected five fields displayed correctly
- Chinese rendering normal
- orientation normal
- final page stable
- no obvious clipping / overlap / black artifact

Observed:
- multiple visible refresh/flash phases during update
- final display stabilized

Evidence boundary:
- exact physical FULL invocation count NOT independently verified
- BUSY timeout fault injection NOT TESTED
- Deep Sleep NOT TESTED
- Partial Refresh NOT TESTED
- Fast Refresh NOT TESTED
- long-duration operation NOT TESTED
- network business-data delivery NOT TESTED

Current stage:
STEP016D-C EVIDENCE CLOSURE
COMPLETE

---

# 15. STEP017A Frozen LAN Product Direction

The following is the preserved A design-freeze record; current B results follow
in section 16. Historical NOT RUN entries are not rewritten as later test claims.

STEP017A LAN PRODUCT ARCHITECTURE FREEZE: COMPLETE
Selected STEP017 Product: LAN Connected Progress Terminal.
Parent baseline: 37f80a69470a91a921c7b8b8db4e29032ae14840.

- [Architecture](hardware/gdey042t81_esp32/docs/STEP017A_LAN_PRODUCT_ARCHITECTURE.md)
- [Frame HTTP contract](hardware/gdey042t81_esp32/docs/STEP017A_FRAME_HTTP_CONTRACT.md)
- [Update and failure policy](hardware/gdey042t81_esp32/docs/STEP017A_UPDATE_AND_FAILURE_POLICY.md)
- [Network security boundary](hardware/gdey042t81_esp32/docs/STEP017A_NETWORK_SECURITY_BOUNDARY.md)
- [Stage/test plan](hardware/gdey042t81_esp32/docs/STEP017A_STAGE_TEST_PLAN.md)

Host owns event/snapshot business mapping, fonts/layout, strict L rendering,
one PC L-to-T row reversal and complete atomic T publication. ESP32 owns LAN
request/complete validation/change detection; no business JSON or UI logic.
GET /api/panels/progress/frame serves the one Host-configured source.
Exact T: 400x300, 1-bit, 15000 bytes, stride 50, MSB-first, 0 black/1 white.
Strong ETag hashes exact T bytes. Valid 304 or unchanged 200 causes no display.
Network failure retains the physical image; no clear/error page/partial handoff.
60-second polling is a product default, not a display refresh period.
Cold boot does not persist identity; first valid frame may refresh again.
Trusted-LAN HTTP only; no TLS/auth claim, Internet exposure, discovery or secrets
in Git. Explicit Host address; real credentials remain private/ignored.

Existing H1 source/history stays unchanged. STEP017C must resolve repeated-update
lifecycle and LKG acceptance before D; no automatic display retry on unknown.
This scheduled gate is not a claim that existing refreshOnce supports looping.

Stage order: A freeze -> B Host implementation -> C Fetcher/lifecycle design
-> D dedicated implementation -> E software/compile -> F authorized physical LAN
validation -> G evidence closure. Each later stage requires separate authorization.

Host endpoint implementation: NOT RUN.
ESP32 network implementation: NOT RUN.
Network compilation and executable tests: NOT RUN.
Network business-data delivery / physical validation: NOT RUN.
NETWORK PRODUCT FUNCTION VERIFIED: NO.

STEP016D-C PHYSICAL BUSINESS PAGE VALIDATION: PASS (limited scope).
STEP016D-C EVIDENCE CLOSURE: COMPLETE.
PRODUCT FUNCTION VERIFIED: YES (Offline Progress Display, limited scope).
H0 PASS and H1 PASS (limited scope) retained.
BUSY timeout fault injection, Deep Sleep, Partial/Fast Refresh and long-duration
operation remain NOT TESTED; exact physical FULL invocation count remains NOT
independently verified. Architecture freeze does not expand these results.

Commit message: docs(network): freeze STEP017A LAN product architecture.
Resolve this document-only commit SHA from Git; no self-referential SHA here.
Only five new design documents and this state file are included. Evidence stays
local-only/untracked. No source changes, tests/build/server/network/hardware
execution, push or tag. Stop before STEP017B.

---

# 16. STEP017B Host Implementation and Software Verification

Preserved B completion record. Its C NOT RUN entries describe that historical
stage; the current C design result is recorded in section 17.

STEP017B HOST FRAME ENDPOINT IMPLEMENTATION: COMPLETE.
Parent baseline: 4f5383dda1202f1e09ea48aefdac69e92f4e196d.
Report: [Host Frame Endpoint](hardware/gdey042t81_esp32/docs/STEP017B_HOST_FRAME_ENDPOINT_REPORT.md).

- EINK_PROGRESS_SOURCE selects one source at process initialization; no fallback.
- GET /api/panels/progress/frame renders only a new snapshot on demand.
- Existing strict ProgressPanel, PNG-to-L and L-to-T functions remain unchanged.
- Snapshot time is normalized to Shanghai wall-clock minutes, never poll time.
- Complete immutable 15000-byte T publication; SHA-256 strong ETag; 200/304.
- Invalid conditional header: 400; no valid publication: 503.
- Render failure retains old publication; source/version gate discards stale work.
- EventStateStore internal short callback synchronizes validation/publication with ingestion.
- Existing event/snapshot/render API contracts and H1/ESP32 code preserved.

Verification: original regression 311 passed in 3.49s; new tests 53 passed in
1.09s; final total 364 passed in 4.12s. In-process TestClient only, no listener.
Sample T length 15000 and SHA256:
a243c5740472d3f2f3c09ca440446d2e50b5da0b32bcb00b6ddca533f6084f8d.
No new runtime frame/header files or firmware produced.

STEP017C Fetcher/continuous display lifecycle design: NOT RUN.
ESP32 network implementation, compilation, real TCP/LAN delivery, device rejection
tests and physical validation: NOT RUN. NETWORK PRODUCT FUNCTION VERIFIED: NO.
H0 PASS, H1 PASS (limited scope), STEP016D-C PASS (limited scope) and evidence
closure COMPLETE retained. PRODUCT FUNCTION VERIFIED remains YES only for the
Offline Progress Display (limited scope).
BUSY timeout fault injection, Deep Sleep, Partial/Fast Refresh and long-duration
operation remain NOT TESTED; exact physical FULL invocation count NOT independently verified.

Local commit message: feat(network): publish progress transport frames over HTTP.
Resolve SHA from Git history, not from this self-referential state file.
Only Host code/tests/report/state submitted. Evidence local-only/untracked;
no push/tag, ESP32 build, serial or hardware operation. Stop before STEP017C.

---

# 17. STEP017C ESP32 Network Fetcher Design Freeze

STEP017C ESP32 NETWORK FETCHER DESIGN FREEZE: COMPLETE.
Parent baseline: 9a23df88ed85466f52847c45c20933f942159979.
Initial gate: HEAD matched, index empty, only hardware/evidence/ untracked.

- [Fetcher design](hardware/gdey042t81_esp32/docs/STEP017C_ESP32_NETWORK_FETCHER_DESIGN.md)
- [State machine](hardware/gdey042t81_esp32/docs/STEP017C_NETWORK_STATE_MACHINE.md)
- [Frame acceptance and LKG](hardware/gdey042t81_esp32/docs/STEP017C_FRAME_ACCEPTANCE_AND_LKG.md)
- [Display lifecycle](hardware/gdey042t81_esp32/docs/STEP017C_DISPLAY_LIFECYCLE.md)
- [Configuration and timeouts](hardware/gdey042t81_esp32/docs/STEP017C_NETWORK_CONFIG_AND_TIMEOUTS.md)
- [D/E/F verification gates](hardware/gdey042t81_esp32/docs/STEP017C_IMPLEMENTATION_TEST_PLAN.md)

Host A/B contract audit found no blocking conflict; B software result remains
364 passed historically, not rerun. Local H1/GxEPD2 and Arduino framework audit
informed these design decisions, not an assertion of new runtime verification:

- One application owner; network and EPD transactions never overlap.
- Existing Wi-Fi STA, WiFiClient-owned socket, bounded restricted HTTP parsing,
  nonblocking socket transfer and mbedTLS SHA-256; no new dependency.
- Explicit LAN IPv4 and port, fixed Progress endpoint; no DNS/discovery.
- One static 15000-byte T buffer, unchanged MCU bytes and fixed H1 direction.
- Strict 200/304 identity/framing validation, complete body and bounded EOF check.
- Wi-Fi window 15 s, TCP 3 s, send 1 s, header/body 5 s each, idle/EOF 2 s,
  whole HTTP transaction 15 s; earliest deadline wins.
- Poll/retry interval starts at completed transaction, default 60 s, range 60..86400 s.
- Fresh H1 object per validated changed-frame session; unchanged coldInit/prepare/
  refreshOnce, complete dual RAM, standard FULL only, no session cleanup EPD commands.
- Accepted identity advances only on conservative software return conditions,
  never merely on download and never as proof of physical success.
- Display refusal/unknown enters FAULT_STOP: no later application network/display
  activity or automatic reboot. No physical rollback or recovery is claimed.
- Future dedicated esp32-m1-network-progress environment and ignored private config;
  historical four environments/H1/Host/Renderer remain unchanged.

Repeated reset/initialization is a new STEP017 behavior requiring later verification;
software object recreation is not hardware power cycling. BUSY may be unobservable
or faulty despite passing software conditions. H1's historical one-shot boundary
is preserved, not rewritten as proof of the new repeated-session policy.

Document/static consistency, links, sensitive patterns and Git checks only.
Executable tests, PlatformIO build, HTTP/Wi-Fi/LAN tests and hardware operations:
NOT RUN in C. ESP32 NETWORK FETCHER IMPLEMENTED: NO.
Current next stage: STEP017D ESP32 NETWORK FETCHER IMPLEMENTATION, NOT RUN.
STEP017E software/compile verification and STEP017F physical LAN update: NOT RUN.
NETWORK PRODUCT FUNCTION VERIFIED: NO.

H0 PASS, H1 PASS (limited scope), STEP016D-C physical offline product PASS (limited
scope) and evidence closure COMPLETE retained. BUSY fault injection, Partial/Fast
Refresh, Deep Sleep and long-duration operation remain NOT TESTED; exact physical
FULL invocation count remains NOT independently verified.

Local commit message: docs(network): freeze STEP017C ESP32 fetcher design.
Resolve SHA from Git history. Only six new documents and this state file submitted;
evidence local-only/untracked, no source/config changes, push/tag or hardware work.
Stop before STEP017D.

---

# 18. STEP017D ESP32 Network Fetcher Implementation

STEP017D implementation: IMPLEMENTED; pending review and STEP017E verification.
Parent baseline: 5371460e01b38b9ec4f54438b74cf23d7691dc04.
Pre-flight: matching HEAD, empty index, only hardware/evidence/ untracked.

- [Implementation report](hardware/gdey042t81_esp32/docs/STEP017D_NETWORK_FETCHER_IMPLEMENTATION_REPORT.md)
- Dedicated network_progress entry and esp32-m1-network-progress environment.
- Bounded HTTP parser/state machine, one static T buffer, checked identity handoff,
  finite network retry and terminal display fault; original H1 adapter reused.
- No private network configuration or credentials created, no dependency changes.
- Production C++ fake-port test harness added; execution NOT RUN. No host C++
  compiler found on PATH; none installed. Existing Python tests NOT RUN in D.
- Document/source static checks only; STEP017E all-environment builds, full runtime
  tests and firmware/resource verification NOT RUN. No compiled-firmware claim.

Changes are uncommitted and unstaged for review. STEP017C frozen documents unchanged.
STEP017F LAN/physical testing NOT RUN; NETWORK PRODUCT FUNCTION VERIFIED: NO.
H0 PASS, H1 PASS (limited scope), STEP016 offline physical PASS (limited scope) and
evidence closure retained. BUSY fault injection, Partial/Fast Refresh, Deep Sleep,
long-duration behavior and exact physical FULL count retain their prior boundaries.
No upload, serial/COM access, listener, LAN request, hardware operation, push or tag.
Stop before STEP017E; this record does not authorize its execution.
