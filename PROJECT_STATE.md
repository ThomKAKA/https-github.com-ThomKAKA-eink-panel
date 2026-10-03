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

STEP017F CODEX-ONLY RUNTIME ACCEPTANCE: PASS.
CODEX-ONLY FINAL REGRESSION: PASS.
STEP017F CODEX-ONLY FINALIZATION: COMPLETE in this local checkpoint.

Current Next Stage:

Stop after the authorized local checkpoint. No later phase, push, tag or formal
workflow dispatch is started. Future work requires separate authorization.

Current Objective:

The LAN Connected Progress Terminal has real device-to-Host frame delivery and
physical display verification for the prescribed short STEP017F scenarios.
The initial 61% page, subsequent 62% and 63% pages, and 64% recovery page were
confirmed by the user. Unchanged ETag/304 causes no new display invocation;
truncated and SHA-invalid frames are rejected without replacing accepted identity
or the visible image. Host interruption retains the last page, and normal polling
recovers to a later valid changed page without ESP32 reset or re-upload.
NETWORK PRODUCT FUNCTION VERIFIED: YES, limited to the recorded STEP017F scope.

Section 22 is the current independent CODEX-ONLY TEMPORARY closure. Sections 18-21
preserve the earlier D/D-R1/formal E records, including their NO-GO and NOT RUN
results at that time. CODEX-ONLY E/F PASS does not grant formal dual-agent acceptance.
DUAL_AGENT_WORKFLOW_MODIFIED = NO; DSH/3090 TASK, RESULT, REVIEW, approval, STATE
and STEP017E v2/v3 history remain unchanged.
H0/H1 and STEP016 offline limited-scope verification remain preserved.


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

NETWORK PRODUCT FUNCTION VERIFIED:

YES (CODEX-ONLY STEP017F acceptance scope; section 22)


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
- Automatic display/hardware-fault recovery

Ordinary LAN Host interruption and automatic network polling recovery are verified
in section 22. This does not establish automatic recovery from display FaultStop.


Do not describe these features as verified.


---

# 6. Current Product Decision

Selected STEP017 Product:

LAN Connected Progress Terminal.

CODEX-ONLY software/compile verification and the prescribed physical LAN runtime
acceptance are PASS. NETWORK PRODUCT FUNCTION VERIFIED: YES within section 22.
The ESP32 fetches and validates final Host-rendered frames; it does not parse
business JSON, render UI or generate images. Existing standard FULL/H1 behavior
remains the display foundation.

The STEP016 Offline Progress Display remains a separately verified historical
baseline; its limited-scope PASS is preserved. No Partial/Fast Refresh, Deep Sleep,
long-duration reliability or hardware/display fault recovery claim is added.


---

# 7. Frozen Architecture

STEP017A architecture remains: Host renders final T bytes from one configured
Progress event source; ESP32 fetches/validates complete T frames over LAN HTTP.
C/C-R1 ownership, one static 15000-byte buffer, ETag/SHA, polling deadlines, last
accepted identity and terminal display FaultStop contracts remain unchanged.
D-R1 native nonblocking socket and layered Wi-Fi initialization are preserved.

Each validated changed frame uses a fresh H1 session, existing coldInit, complete
frame preparation and standard FULL refresh. The network adapter now lets coldInit
execute before applying the post-prepare BUSY invariant: only the BUSY early rejection
before coldInit was removed. H1 driver, GPIO polarity, SPI, timeout,
frame orientation, refreshOnce and FaultStop remain unchanged. The retained
NETWORK_DISPLAY_BUSY_POST_PREPARE_HIGH log is only on its original failure path.
No delay, retry, busy wait or display recovery loop was added.

Short repeated updates and Host interruption/recovery were physically verified
in the independent CODEX-ONLY task. Software acceptance does not alone prove
physical success; the 61%, 62%, 63% and 64% pages have direct human confirmation.
Formal dual-agent acceptance is not inferred from these independent results.

The data flow and module/one-shot refresh details in sections 7-9 below describe
the preserved STEP016 implementation baseline, not the STEP017 polling lifecycle.
STEP017 contracts are linked in sections 15 and 17; current evidence is section 22.

Data Flow (preserved STEP016 offline baseline):

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

STEP017F CODEX-ONLY FINALIZATION: COMPLETE in the authorized local checkpoint.

Final existing Python regression and the affected network build passed once.
The prescribed runtime acceptance and human display confirmations were completed
before this finalization task and were reused without new hardware operations.
Section 22 records the software blocker fix, final regression and evidence scope.
No next phase is started. Formal dual-agent E/F acceptance remains unchanged.

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
- STEP017C DESIGN FREEZE: 5371460e01b38b9ec4f54438b74cf23d7691dc04
- STEP017D IMPLEMENTATION PRESENT (closure NO-GO, not approved): 239411582893d05b70fbb5f0d571c078201f5216
- STEP017 STATE RECONCILIATION: 99b5e996edc9acd1a12587800954772b3c99651d
- STEP017C-R1 DESIGN AMENDMENT: 0e2cc29f92c99c842759519624cf63ad1f20af6c


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

Preserved historical record at C freeze. Its implementation/next-stage NOT RUN
statements describe that time, not current status. Section 18 supersedes those
status statements. The decisions below record the original freeze. Four network
documents are now amended by C-R1 (section 19); original display/LKG documents
remain unchanged. Do not apply superseded transport assumptions to D-R1.

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

Preserved state reconciliation record at commit 99b5e99. Its C-R1 NOT RUN and
D-R1 NOT READY entries describe that stage; current remediation is in section 20.
Old D closure NO-GO and the blockers below describe the unrepaired initial code,
not a claim that D-R1 has not executed. No historical findings are removed.

STEP017D implementation: PRESENT.
Implementation commit: 239411582893d05b70fbb5f0d571c078201f5216.
STEP017D CLOSURE: NO-GO. STEP017D APPROVED: NO.
STEP017D COMPILE VERIFIED: NO / NOT RUN.
STEP017D RUNTIME VERIFIED: NO / NOT RUN.
STEP017D PHYSICAL VERIFIED: NO / NOT RUN.
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

Implementation is committed, not approved or COMPLETE. STEP017C frozen documents
are unchanged. The implementation report's "No commit" statements describe its
creation-time history and remain unchanged; they are not the current Git status.
See [State reconciliation](hardware/gdey042t81_esp32/docs/STEP017_STATE_RECONCILIATION.md).

Closure blockers (all PRESENT, source-level findings, not runtime fault injection):

1. Wi-Fi reconnect ownership assumption mismatch: main.cpp configure() only calls
   setAutoReconnect(false); fixed framework WiFiGeneric.cpp first_connect branch
   can independently call WiFi.begin(). C-R1 must revise the ownership contract.
2. CONFIG_INVALID and WIFI_INIT_FAILURE are merged into configure() == false
   (main.cpp), then ConfigValidate enters FAULT_STOP (machine.h). D remediation
   is required after the failure classification contract is frozen.
3. WiFiClient.cpp ROE_WIFICLIENT returns on setsockopt failure before fd ownership
   transfers to clientSocketHandle; stop() cannot release that unowned descriptor.
   C-R1 must revise the transport ownership/cleanup contract.

Exact source references and effects are recorded in the reconciliation report.
This records defects only; no replacement transport or reconnect design is chosen.

STEP017C-R1 NETWORK TRANSPORT ASSUMPTION AMENDMENT: NOT RUN.
STEP017D-R1 NETWORK FETCHER REMEDIATION: NOT READY; awaits C-R1 decisions on
reconnect ownership, transport ownership and failure classification.
STEP017E SOFTWARE / COMPILE VERIFICATION: NOT READY due to unresolved blockers.
STEP017F LAN/physical testing NOT RUN; NETWORK PRODUCT FUNCTION VERIFIED: NO.
H0 PASS, H1 PASS (limited scope), STEP016 offline physical PASS (limited scope) and
evidence closure retained. BUSY fault injection, Partial/Fast Refresh, Deep Sleep,
long-duration behavior and exact physical FULL count retain their prior boundaries.
No upload, serial/COM access, listener, LAN request, hardware operation, push or tag.
Stop before STEP017E; this record does not authorize its execution.

Current factual stage: STEP017D IMPLEMENTATION PRESENT; CLOSURE NO-GO.
Current next actionable stage: STEP017C-R1 NETWORK TRANSPORT ASSUMPTION AMENDMENT.
State reconciliation is COMPLETE; C-R1 remains NOT RUN. Stop after this document-only
closure; no design amendment, remediation, test or hardware stage is started.

---

# 19. STEP017C-R1 Network Transport Assumption Amendment

Preserved C-R1 completion record. Its D-R1 READY/NOT RUN and E NOT READY entries
describe amendment completion; current implementation status is in section 20.

STEP017C ORIGINAL DESIGN FREEZE: COMPLETE.
STEP017C-R1 NETWORK TRANSPORT ASSUMPTION AMENDMENT: COMPLETE.
Parent baseline: 99b5e996edc9acd1a12587800954772b3c99651d.
Pre-flight matched, index empty, only hardware/evidence/ untracked.
Report: [C-R1 amendment](hardware/gdey042t81_esp32/docs/STEP017C_R1_NETWORK_TRANSPORT_ASSUMPTION_AMENDMENT.md).

- Layered Wi-Fi reconnect ownership: tolerate fixed first_connect framework retry;
  application exclusively owns state transitions, polling, HTTP, frames and display.
- Native nonblocking lwIP/BSD socket, immediate unique descriptor ownership,
  bounded connect/readiness/SO_ERROR checks and uniform close on all owned exits.
- No new dependency or framework patch; no absolute lower-stack leak-free claim.
- CONFIG_INVALID -> FAULT_STOP; WIFI_INIT_FAILURE -> FAILURE_WAIT and retry WIFI_INIT.
- Association/link/TCP/HTTP/candidate failures -> cleanup, no display, FAILURE_WAIT.
- Internal ownership/illegal-state or existing display refusal/unknown -> FAULT_STOP.
  Uncertain/failed close stops further allocations; no automatic close retry.
- All existing frame, LKG, identity, H1, direction and deadline contracts preserved.
  Display lifecycle and Frame Acceptance/LKG documents unchanged.

STEP017D implementation: PRESENT at 239411582893d05b70fbb5f0d571c078201f5216.
STEP017D CLOSURE: NO-GO; APPROVED: NO. Three old-code blockers remain PRESENT.
STEP017D-R1 NETWORK FETCHER REMEDIATION: READY; execution NOT RUN.
STEP017E SOFTWARE / COMPILE VERIFICATION: NOT READY.
NETWORK PRODUCT FUNCTION VERIFIED: NO. Physical LAN update: NOT RUN.
Current next actionable stage: STEP017D-R1 NETWORK FETCHER REMEDIATION.

Only four C documents, the amendment and this state file change. D implementation,
tests/configuration, D report, reconciliation report, framework and evidence stay
unchanged. Static checks only; tests, compilation, Wi-Fi/HTTP runtime, serial and
hardware NOT RUN. No push/tag. Local commit message:
docs(network): amend STEP017C transport assumptions.
H0/H1 and offline limited-scope PASS retained; BUSY fault injection, Deep Sleep,
Partial/Fast and long-duration operation NOT TESTED; exact physical FULL count
NOT independently verified. Stop before D-R1; design completion is not D approval.

---

# 20. STEP017D-R1 Network Fetcher Remediation

Preserved historical D-R1 implementation record. Its verification NOT RUN and
next-stage statements describe that stage; current independent evidence is section 22.

STEP017D-R1 NETWORK FETCHER REMEDIATION: IMPLEMENTED.
Parent baseline / C-R1 commit: 0e2cc29f92c99c842759519624cf63ad1f20af6c.
Pre-flight: matching HEAD, empty index, only hardware/evidence/ untracked.
Report: [D-R1 remediation](hardware/gdey042t81_esp32/docs/STEP017D_R1_NETWORK_FETCHER_REMEDIATION_REPORT.md).

- Layered Wi-Fi ownership: framework first-connect retry is tolerated; main state
  machine alone schedules HTTP/display. Recovery never ends FAILURE_WAIT early.
- Pure ConfigResult validation, typed WifiInitResult, WifiInit state and initialized
  retry gate replace configure() conflation. Initialization failure is retryable.
- WiFiClient transport removed; unique native nonblocking SocketOwner with immediate
  descriptor ownership, select/SO_ERROR progression and explicit checked close.
- Close failure/ownership uncertainty parks permanently without further allocation;
  local invalidation does not prove a failed close released lower-stack resources.
- Parser, single static T buffer, ETag/SHA, display function and H1 unchanged.
  Configuration, PlatformIO, Host/Python, frozen contracts and evidence unchanged.

Blocker implementation status: all three REMEDIATED IN SOURCE.
Blocker verification status: NOT RUN; not VERIFIED FIXED.
Initial D implementation PRESENT at 239411582893d05b70fbb5f0d571c078201f5216;
its closure NO-GO remains historical. Overall approval PENDING STEP017E VERIFICATION.

Static C-R1 fidelity, descriptor paths, scope, links, secret and diff review: PASS.
C++ harness updated/added; TEST EXECUTION NOT RUN. Python regression NOT RUN.
COMPILE VERIFIED: NOT RUN. RUNTIME VERIFIED: NOT RUN. PHYSICAL VERIFIED: NOT RUN.
No firmware generated; firmware hash NOT AVAILABLE / NOT RUN.
NETWORK PRODUCT FUNCTION VERIFIED: NO. PHYSICAL LAN UPDATE: NOT RUN.
Current next actionable stage: STEP017E SOFTWARE / COMPILE VERIFICATION, not executed.

H0/H1 and STEP016 offline limited-scope PASS retained. BUSY fault injection,
Deep Sleep, Partial/Fast Refresh and long-duration operation NOT TESTED;
exact physical FULL count NOT independently verified. No new physical claim.
Local commit message: fix(network): remediate STEP017D fetcher ownership.
Resolve this successor SHA from Git; it becomes the E baseline without authorizing E.
No push/tag, network execution, upload, serial/COM or hardware operation.

---

# 21. STEP017E Software / Compile Verification Attempt

Preserved formal STEP017E attempt and NO-GO. Its missing-input/build/runtime
statements describe that attempt. Section 22 records later independent Codex-only
results; it does not change this formal workflow decision or history.

STEP017E: ATTEMPTED, **NO-GO**. Baseline:
`6960515f3dca6c751c925d5fd127738735b9f486`.
Formal DeepSeek Harness run: `6cc77c084b5d415d9505c73683ebd079`.
[Verification report](hardware/gdey042t81_esp32/docs/STEP017E_SOFTWARE_COMPILE_VERIFICATION_REPORT.md)
contains the command, artifact, static-review and Git-purity evidence.

- Executor full Python suite: 364 collected / 364 passed / 0 failed / 0 skipped;
  Codex independent rerun: 364 passed. Both exit 0.
- Historical `esp32dev`, `esp32-m1`, `esp32-m1-h1`, and `esp32-m1-progress`
  PlatformIO environments: SUCCESS. BIN/ELF files, sizes and SHA-256 verified.
- Host C++17 compiler: unavailable; `tests/cpp` BLOCKED / NOT RUN. No compiler
  was installed. This blocker alone is allowed by the frozen E plan.
- Dedicated `esp32-m1-network-progress` build: BLOCKED / NOT RUN. Its required
  local-only private configuration is absent; per-environment library cache is
  absent and no dependency installation/download was authorized. Network RAM,
  Flash, BIN/ELF and SHA-256: UNAVAILABLE. Target socket API integration remains
  NOT COMPILE VERIFIED. No compile/link failure was observed because no network
  build ran.
- Static transport, application-owned descriptor cleanup, failure routing,
  frame/identity/display eligibility, dependency and scoped secret reviews:
  PASS at source-review scope only. No runtime or physical inference.
- Before/after executor snapshots: all 154 tracked file hashes and 42 local
  `hardware/evidence/` entries unchanged. HEAD unchanged; only
  `?? hardware/evidence/` untracked before documentation. Generated changes
  were confined to ignored build/test caches.

Final gate: NO-GO because the required network build did not pass. ESP32 NETWORK
FETCHER COMPILE VERIFIED: NO. NETWORK RUNTIME VERIFIED: NO. PHYSICAL LAN UPDATE:
NOT RUN. NETWORK PRODUCT FUNCTION VERIFIED: NO. Do not enter STEP017F. A future,
separately authorized E verification-environment preparation must supply an
approved local-only compile profile and exact pinned dependencies; then rerun E.
No source defect requiring STEP017D-R2 was established by this attempt.

BUSY timeout fault injection, Deep Sleep, Partial/Fast Refresh and long-duration
operation remain NOT TESTED. Exact physical FULL invocation count remains NOT
independently verified. No upload, serial/COM, hardware, push or tag.


---

# 22. STEP017F CODEX-ONLY Runtime Acceptance and Finalization

Date: 2026-10-02 (Asia/Shanghai).
Mode: CODEX-ONLY TEMPORARY / FINALIZATION.
Original source baseline / local checkpoint parent:
`c439234abea522a8afdc006354a16e2a22090b15`.

STEP017F_RUNTIME_ACCEPTANCE = PASS
CODEX_ONLY_STEP017F_PHYSICAL_LAN_VALIDATION = PASS
NETWORK_PRODUCT_FUNCTION_VERIFIED = YES
FINAL_REGRESSION = PASS
PROJECT_STATE_UPDATED = YES
DUAL_AGENT_WORKFLOW_MODIFIED = NO

These are independent Codex-only product results. Formal dual-agent STEP017E / F
acceptance, DSH/3090 jobs and frozen TASK/RESULT/REVIEW/approval/STATE/v2/v3 history
are not modified or promoted. Earlier failed attempts remain historical evidence.

## Confirmed software blocker and minimal fix

Instrumented runtime observed NETWORK_DISPLAY_BUSY_PRE_INIT_HIGH immediately
following DisplayUpdate; DisplayInvariantFailure led to FaultStop before H1
coldInit, frame preparation or refreshOnce could run. The software blocking
condition is CONFIRMED. The physical/electrical cause of BUSY HIGH before panel
initialization is NOT MEASURED, not a confirmed electrical diagnosis.

Only network_progress/main.cpp changed: remove pre-init BUSY=HIGH early rejection
so the existing H1 cold initialization executes first. Preserve pinMode, H1 driver,
coldInit, preparation, post-prepare BUSY invariant and its failure-only marker
NETWORK_DISPLAY_BUSY_POST_PREPARE_HIGH, refreshOnce and FaultStop. No new delay,
retry, busy wait, recovery loop, polarity inversion or timeout extension.

## Completed runtime acceptance (existing evidence reused)

| Scenario | Actual result / evidence boundary |
|---|---|
| Initial valid frame | PASS; complete legal 15000-byte T frame, SHA/strong ETag, display path and user-confirmed61% page |
| Unchanged ETag / 304 | PASS; empty body, PollWait, no new display invocation in saved runtime records |
| Second business page | PASS; new legal62% frame and direct human confirmation |
| Third business page | PASS; new legal63% frame and direct human confirmation |
| Truncated response | PASS; 14999 of declared15000 bytes rejected, FailureWait/FrameValidationFailure7, no display, accepted63% identity/image retained |
| SHA mismatch | PASS; complete body with wrong hash rejected, FailureWait/Failure7, no display, accepted63% identity/image retained |
| Host interruption | PASS; TCP connect failure5, FailureWait, no FaultStop/display; user confirmed63% image retained without refresh |
| Host automatic recovery | PASS; same Host implementation/configuration restored, device normal polling accepted legal64% changed page without reset/re-upload; user confirmed64% page |

Chinese content, direction and completeness were confirmed on successful61%,62%,
63%,64% pages. Invalid-response image preservation has both device/Host correlation
and direct user observations. No physical result is inferred solely from software
return conditions. Accepted identity preservation is supported by later normal
requests carrying the original ETag and obtaining304.

The recovery records retain an external helper UTF-8/GBK execution error and an
initial observation-rule error; neither altered firmware. The restarted Host also
returned503 before a valid event was published. The device entered ordinary
FailureWait then recovered on its next normal poll to the64% page. Those records
remain alongside successful recovery evidence; no failed response is rewritten.

Runtime-validated firmware BIN SHA256:
`8ac6350a3ef6634b26b331eb065a6724ea963a0476d0ba87e7647b6a5ea88efb`.
The final compile below is not uploaded and adds no new hardware verification.

## Final regression and affected target compile

- Existing `.venv/Scripts/python.exe -m pytest`, cwd main project, invoked once: 364 collected / 364 passed / 0 failed / 0 errors / 0 skipped; 3.89s; exit0. No new tests, dependency installation, upgrade or workaround.
- `esp32-m1-network-progress` build/link invoked once with existing REAL-RUNTIME private headers and pinned cached platform/toolchain/libraries, independent repository-external build_dir: PASS, exit0, 48.54s. RAM 59960 bytes (18.3%); Flash 753217 bytes (57.5%).
- Final compile BIN: 759792 bytes; SHA256 `8ac6350a3ef6634b26b331eb065a6724ea963a0476d0ba87e7647b6a5ea88efb`.
- Final compile ELF: 12272484 bytes; SHA256 `5a805316fce786d70e432dead00011ce3232be2ac6536e692ece85775d027e1b`.
- Actual dependency metadata confirms external REAL-RUNTIME network/display headers; compile-only fixture is not used. Private headers stay local, unchanged, untracked and absent from this checkpoint. Candidate binaries contain credentials and are kept local only.
- Other four PlatformIO environments: EXISTING EVIDENCE REUSED; only the network source was affected, no other builds repeated. Host C++ harness remains BLOCKED / NOT RUN as previously recorded; no compiler installed.
- Finalization hardware tests, COM11 access, upload, reset and power cycle: NOT RUN.

## Local evidence and checkpoint scope

Local-only evidence root:
`D:/Codex/2026-10-02/referenced-chatgpt-conversation-this-is-an/outputs/codex-only-temporary-20261002/`.

- Software prerequisite: STEP017E_CODEX_ONLY_FINAL_SOFTWARE_VERIFICATION.md.
- Initial fix/runtime: STEP017F_CODEX_ONLY_TARGETED_DISPLAY_INIT_ORDER_FIX_AND_RUNTIME_VALIDATION.md and step017f-display-init-order-fix-20261002/human-observation.json.
- Remaining scenes: STEP017F_CODEX_ONLY_REMAINING_RUNTIME_ACCEPTANCE_SCENARIOS.md and step017f-remaining-acceptance-20261002/final-execution.json / scenario1..6-result.json / git-postflight.json.
- Finalization: STEP017F_CODEX_ONLY_FINAL_REGRESSION_PROJECT_STATE_AND_GIT_CHECKPOINT.md and step017f-finalization-20261002/ for exact commands, logs, artifact identity, diff/secret review and Git records.

Checkpoint includes only network_progress/main.cpp and PROJECT_STATE.md. Resolve
this checkpoint SHA/message/parent from Git, not a self-referential hash here.
Raw hardware/evidence remains local-only/untracked. Private inputs, firmware,
logs, temporary scripts and external evidence are not committed. No push, tag,
merge, PR, remote change or history rewrite; stop after this local checkpoint.

BUSY timeout fault injection, electrical health, Partial/Fast Refresh, Deep Sleep,
long-duration operation/endurance and exact physical FULL invocation count remain
NOT TESTED / NOT independently verified. Automatic display/hardware-fault recovery
is not claimed; terminal display FaultStop is preserved.

---

# 23. Round 2 R0 — Baseline Freeze & Round-2 Contract

Date: 2026-10-03 (Asia/Shanghai).
Authorized scope: R0 only; baseline regression/build and product contract documents.
This appended section is the current Round 2 status source. Sections 1-22 and all
STEP016/STEP017 conclusions remain unchanged. README, RESUME and older test/build
notes describe earlier stages; current STEP017F evidence remains section 22.

## Repository baseline

- CURRENT_HEAD_BEFORE = `dc0b1910105815ef67a6da267a1cf59fdbfd98e3`.
- Historical PDF reference = `dc0b1910105815ef67a6da267a1cf59fdbfd98e3`;
  current HEAD matches; no reset, historical checkout or rollback performed.
- Workspace = `C:/Users/cslki/.codex/worktrees/a5b3/eink-panel` (detached HEAD).
- Initial `git status --short`: empty; tracked worktree and index clean,
  no untracked files. Initial `git diff --cached --name-only`: empty.
- `git rev-parse HEAD` and `git log -5 --oneline` executed. Latest five:
  `dc0b191`, `c439234`, `6960515`, `0e2cc29`, `99b5e99`.

## Fresh software verification

Reused the commands recorded in section 22 and the STEP017F finalization report.
Existing main-checkout virtual environments and cached dependencies were reused;
the Python test cwd and PlatformIO project directory select this current worktree.
No new tests or validation framework, dependency installation or upgrade.

Python command, cwd current workspace:

```powershell
& 'D:\Codex\eink-panel\.venv\Scripts\python.exe' -m pytest
```

PYTHON_REGRESSION = PASS
Collected = 364; passed = 364; failed = 0; errors = 0; skipped = 0;
exit code = 0; duration = 4.16s. Full suite invoked once.

Network build command, cwd current workspace:

```powershell
$env:PLATFORMIO_CORE_DIR = 'D:\Codex\eink-panel\.venv-hw\pio-core'
$env:PLATFORMIO_SETTING_ENABLE_TELEMETRY = 'false'
$env:PLATFORMIO_DISABLE_UPGRADE_CHECK = 'true'
& 'D:\Codex\eink-panel\.venv-hw\Scripts\python.exe' -B -m platformio run -d 'C:\Users\cslki\.codex\worktrees\a5b3\eink-panel\hardware\gdey042t81_esp32' -c 'D:\Codex\round2-r0-20261003-a5b3\platformio-round2-r0.ini' -e esp32-m1-network-progress --disable-auto-clean -j 4
```

NETWORK_BUILD = PASS
Environment = `esp32-m1-network-progress`; exit code = 0; duration = 53.18s.
RAM = 59960 / 327680 bytes (18.3%); Flash = 753217 / 1310720 bytes (57.5%).
Target build invoked once. The external STEP017F finalization configuration was
copied with only build_dir changed to a new evidence directory; tracked
platformio.ini, pinned platform/toolchain/libraries and REAL-RUNTIME headers were
preserved. Actual dependency metadata confirms both runtime-private headers and
excludes the compile-only fixture. Network source and private-header hashes were
unchanged after the build. This is a fresh compile result, not new physical evidence.

Local-only R0 evidence: `D:/Codex/round2-r0-20261003-a5b3/` contains preflight.json,
python-regression.json, platformio-round2-r0.ini, network-build.log,
network-build-exit.txt, network-build-result.json and network-build/ artifacts.
Exact commands, counts, resource usage and artifact hashes are retained there.
Private inputs and credential-bearing binaries remain local and outside Git.
Historical STEP017F logs, firmware and physical evidence were not overwritten.

## Frozen contract and stop

Contract: [Round 2 Product Plan](docs/ROUND2_PRODUCT_PLAN.md).
Preserve Progress data → existing Python Host renderer → 400×300 monochrome
final frame → existing frame publication → ESP32 HTTP pull → existing length /
format / SHA / ETag validation → GDEY042T81 standard FULL display.
Host preview must use that renderer; last-valid-frame and terminal display
FaultStop semantics remain. Software status is not physical display confirmation.

ROUND2_STATUS = BASELINE_FROZEN
ROUND2_R0 = PASS
BASELINE = FROZEN
NEXT_ALLOWED_STAGE = R1 (Software observability / publication status).
R1 = NOT STARTED; stop after the R0 local checkpoint and await separate authorization.

R0 changes only docs/ROUND2_PRODUCT_PLAN.md and this appended state section.
Runtime product code changes = NONE; firmware behavior/source/config changes = NONE.
Upload, serial access, reset, new LAN runtime and hardware/physical validation = NOT RUN.
No R1/R2/R3 or later-stage implementation, push, tag or remote modification.
Checkpoint message: `docs: freeze eink-panel round 2 baseline`.
Resolve checkpoint SHA from Git; no self-referential hash is embedded here.

---

# 24. Round 2 R1A — Software Observability Contract

Date: 2026-10-03 (Asia/Shanghai).
HEAD_BEFORE = `e200be69d095831725e24fb0a90282cb10468907` (R0 checkpoint).
Initial worktree/index clean; HEAD matched the authorized baseline. No rollback.
Authorized scope: minimal Host/device software status, related tests and documents.
Sections 1-23 and historical STEP016/STEP017 results remain unchanged.

## Inspected facts and frozen software contract

- Existing event ingestion/snapshot has event_id: reuse it as publish_id within
  the single configured Progress source, without a new counter/UUID/database.
- PublishedFrame already has SHA-256 strong ETag: frame_version and device
  accepted_frame_version reuse its 64 lowercase hex digits without HTTP quotes.
- Baseline firmware has no firmware version declaration or stable device identity.
  Add only version `round2-r1a-1`; single-device scope, no pairing/registry.
- Baseline Host has no device status state or endpoint. Add process-local state
  under the existing publisher lock, with no separate publication authority.

Contract: [R1A Software Observability](docs/ROUND2_PRODUCT_PLAN.md#r1a-software-observability-contract).

GET /api/panels/progress/status reads publish_id, frame_version, host_stage and
device {last_seen, firmware_version, accepted_frame_version, refresh_stage}.
HOST_ACCEPTED comes from the current accepted snapshot; FRAME_READY requires the
existing installed publication to match it. Status query never triggers rendering.
Failed new rendering keeps old frame delivery and device observations; it cannot
claim FRAME_READY or device completion for the new publish_id.

POST /api/panels/progress/device-report records Host UTC reception time.
DEVICE_FRAME_ACCEPTED requires the actual currently served frame identity.
DEVICE_REFRESH_FLOW_COMPLETE requires a prior accepted observation of that same
frame; it means software return conditions only, never physical display success.
Stale/unknown frame or completion before acceptance returns 409; invalid schema
returns 422. Duplicate acceptance cannot regress completed flow. Communication
reports use refresh_stage=null; they cannot create acceptance/completion state.
No publication history, persistence, device wall-clock authority or extra revision.

## Firmware integration and preserved kernel

Append one DeviceReport state to the existing Machine (old numeric state values
preserved). Changed validated frame -> one acceptance POST -> original display
function -> one completion POST only on its existing software-success return.
Valid 304/unchanged 200 -> communication-only POST -> original polling wait;
zero new frame-acceptance/completion observations and zero display calls.
Truncation, bad SHA, invalid format/HTTP and other rejection paths still discard
the candidate, retain MCU accepted identity and issue no acceptance/completion report.
Display refusal/unknown still FaultStop; MCU accepted ETag advances at the original
software-acceptance point, separately from Host's validated-frame observation.

Reports reuse the existing exclusive SocketOwner, after closing the frame socket,
with one nonblocking bounded POST per observation and a 3-second total budget.
Ordinary report failure does not prevent an eligible display or manufacture Host
success; no retry/queue/replay. Internal ownership/close failure still FaultStop.
Polling wait begins after the report finishes/fails. Report loss can leave Host
stages incomplete; R1A does not infer missing acceptance from a completion report.

Renderer, EventStateStore, T generation, frame publication current/install logic,
GET frame 200/304 contract, protocol.h validation, transport.h SocketOwner,
H1/driver, display() implementation and platformio.ini remain unchanged.
Only the necessary report integration/status methods are added. No frontend/PWA,
database/event bus, discovery/mDNS, provisioning, pairing, OTA, cloud or R2 work.

## Verification and evidence limits

- NEW_TESTS = 16 Python cases in tests/test_publication_status.py. Targeted run:
  `.venv/Scripts/python.exe -m pytest tests/test_publication_status.py -q` using
  existing `D:/Codex/eink-panel/.venv/Scripts/python.exe`: 16 passed in 2.29s; exit 0.
- FULL_REGRESSION = PASS. Exact command from current worktree:
  `& 'D:\Codex\eink-panel\.venv\Scripts\python.exe' -m pytest`.
  380 collected / 380 passed / 0 failed / 0 errors / 0 skipped; 5.64s; exit 0.
  All 364 historical tests pass. In-process TestClient only, no LAN listener.
- Existing C++ fake-port harness extended with report ordering, 304, candidate
  rejection, display failure, report failure/timeout/cleanup and HTTP request cases.
  Compile-only check with existing Xtensa C++17 compiler and -Wall/-Wextra/-Werror
  passed, exit 0. Native harness execution = NOT RUN: host C++ compiler unavailable.
  No compiler installation or Docker daemon startup. Compile is not test execution.
- NETWORK_BUILD = PASS. Existing environment `esp32-m1-network-progress`, exit 0,
  52.20s; RAM 60576 / 327680 bytes (18.5%); Flash 754661 / 1310720 bytes (57.6%).
  Compared with R0: RAM +616 bytes; Flash +1444 bytes.
  Reused the R0 Python/PlatformIO command, REAL-RUNTIME headers and pinned caches;
  external configuration changes build_dir only. Actual dependency metadata includes
  report.h and both existing runtime-private headers; private hashes unchanged.
- RUNTIME_TEST = NOT RUN (real LAN/device report/display). Host in-process API
  behavior tested above; new firmware has been compiled but not deployed.
- physical display evidence = NOT RUN; R1B = NOT RUN; R2 = NOT STARTED.
  Upload, flash, serial, reset and hardware operations = NOT RUN.

Local-only evidence root: `D:/Codex/round2-r1a-20261003-a5b3/`.
preflight.json, python-regression.json, platformio-round2-r1a.ini,
network-build.log / network-build-exit.txt / network-build-result.json and
network-harness-compile.json / .log record commands, counts, exits, resources and
artifact hashes. Firmware and credential-bearing artifacts stay local, outside Git.
R0/STEP017F evidence is preserved. New firmware runtime/physical PASS is not claimed.

## Result and checkpoint stop

ROUND2_R1A = PASS
SOFTWARE_OBSERVABILITY = IMPLEMENTED
PHYSICAL_VALIDATION = NOT_RUN
NEXT_REQUIRED_STAGE = R1B
ROUND2_STATUS = R1A_SOFTWARE_COMPLETE_AWAITING_R1B

Checkpoint includes only the two Host implementation files, three network firmware
files, two related test files, Round 2 plan and this appended state section.
Message: `feat: add round 2 publication observability`.
Resolve its SHA from Git; no self-referential hash is embedded here.
Stop after the local checkpoint. No push, upload, R1B execution or R2 started.


---

# 25. Round 2 R1B — Real Device Observability Verification

Date: 2026-10-03 (Asia/Shanghai).
HEAD_BEFORE = `7c7de5b4e2f3f625b5722f6b299e56ee108380c7` (R1A checkpoint).
Resumed preflight: exact HEAD, worktree/index clean, WLAN 192.168.100.101/24,
saved REAL-RUNTIME SSID matches current WLAN in memory; private headers unchanged.
Prior LAN blocking audit remains at the external evidence root. No rollback,
credential/network/pin/board/driver change, R0/R1A repetition or product-code edit.
Sections 1-24 remain byte-for-byte unchanged.

## Reused build and regression evidence

Per the continuation instruction, reuse the already completed R1B checks after
verifying current HEAD, clean tracked tree, private hashes and BIN/ELF hashes:

- Python command: `& 'D:\Codex\eink-panel\.venv\Scripts\python.exe' -m pytest`,
  cwd this worktree. 380 collected / 380 passed / 0 failed / 0 errors / 0 skipped;
  exit 0; pytest 6.18s, process elapsed 6.66s. Includes R1A related Python cases.
  REUSED; not rerun during this continuation. No new tests.
- Firmware: `esp32-m1-network-progress`, exit 0, build process elapsed 48.31s;
  RAM 60576 / 327680 bytes (18.5%); Flash 754661 / 1310720 bytes (57.6%).
  REUSED; no rebuild. Exact existing PlatformIO module argv/environment in
  build-result.json; pinned caches/REAL-RUNTIME headers and external build_dir.
- BIN 761232 bytes; SHA-256
  `eb98f24250941e5febfdb099f7de94e4390213b22b0a9bc43299941bb1959c2a`.
  Current artifact equals both the prior R1B build and R1A candidate.
- Native C++ harness execution = NOT RUN; existing compile-only result is not
  promoted to runtime PASS. No toolchain/dependency install or upgrade.

## Actual deployment and initial state

Fresh authorized ROM read_mac: COM11 CH340, ESP32-D0WD revision v1.1,
MAC 1c:c3:ab:1f:5f:d0, exit 0, no stub/no Flash write; original target confirmed.
Application upload: existing esptool 4.9.0 method, COM11, 460800 baud,
default_reset / after no_reset, write_flash keep mode/frequency/size, 0x10000;
exit 0, target MAC matches, Hash of data verified. Only application sectors
0x10000-0xc9fff written; no independent erase or bootloader/partition/OTA/NVS/eFuse
write. Exact command/output and candidate hash in upload-result.json.

Current unchanged server.main:app started on 192.168.100.101:8000, one h11 worker,
EINK_PROGRESS_SOURCE=step017f-lan; passive external ASGI evidence wrapper only.
Before device application start, GET status had all publish/frame/Host/device
fields null; no mock device state. Serial reader opened first at 115200 with
DTR false/no buffer clear; one existing esptool HardReset RTS sequence started
the uploaded application. No further reset/re-upload for B or C.
Actual HTTP client 192.168.100.104 maps through WLAN neighbor evidence to the
same ROM-probed MAC. Firmware report version is round2-r1a-1.

## A / B / C correlation and direct human evidence

Both new publications use formal POST /api/events and existing frame GET;
no direct snapshot/cache write, test shortcut or alternate renderer.

| Scenario | Identity / software evidence | Direct human observation |
| --- | --- | --- |
| A: R1B-A / STATUS A / 71% | publish_id `r1b-a-20261003T073526Z`; Host FRAME_READY; device 200/15000 bytes, ACCEPTED then REFRESH_FLOW_COMPLETE for the same frame | User observed refresh and confirmed all three visible fields correct: PASS |
| B: unchanged | 15:37:30-15:38:40 +08, 70.016s, actual 60s poll configuration; device HTTP 304/empty body then refresh_stage=null report; last_seen changed, all identities unchanged; zero new accepted/completion reports, no new software DisplayUpdate | User confirmed screen held R1B-A / 71% without visible refresh/content change in this defined window: PASS |
| C: R1B-B / STATUS B / 72% | new publish_id `r1b-b-20261003T074358Z` and new frame; Host FRAME_READY; normal polling without reset, ACCEPTED then REFRESH_FLOW_COMPLETE for that same new frame | User directly confirmed final R1B-B / STATUS B / 72%: PASS |

A frame_version = `088647200428d1944e42b4c0e0a14944458631795bd05f931c2cc2e0c2153b0c`.
C frame_version = `22eda266dd0185040954cc4b7e138c04024a8d6b4274844ddea81f885a5fc2ee`.
For each new frame, Host frame_version = device accepted report frame_version =
device completion report frame_version = SHA-256 of the actual 15000-byte T frame.
Status GET observations captured ACCEPTED followed by COMPLETE; HTTP POST bodies
and response 200s provide independent reception evidence, while serial records
show the existing display software path and its return-condition marker.
SOFTWARE_REFRESH_FLOW = COMPLETE and PHYSICAL_SCREEN_OBSERVATION = PASS remain
separate facts; physical PASS comes only from the three recorded human replies.

B last_seen: 2026-10-03T07:37:05.578507+00:00 ->
2026-10-03T07:38:05.674844+00:00. publish_id/frame_version/accepted_frame_version
and completed stage remain A; the 304 POST only records communication.
C's accepted identity advances to the new hash and remains there in captured
status observations and the final live query; old A state does not cover C.
Stale-report rejection source and already-passed R1A Python cases reused;
real delayed-report replay = NOT RUN. No unrelated fault injection.

## Evidence, limitations and checkpoint stop

Independent local root: `D:/Codex/round2-r1b-20261003-a5b3/`.
Current acceptance summary is r1b-resume-summary.json. Earlier r1b-summary.json
and goal-blocked-audit.json remain historical LAN-block records, not overwritten.
resume-preflight.json, target-identity-resume.json, upload-result.json,
host-runtime.json, host-initial-status.json, live-process-device-map.json,
publication-a/c.json, status/HTTP/serial logs, scenario-a.json,
scenario-b-304.json, scenario-c.json and human-observation-*.json preserve the
actual commands, identities, chronology and direct human replies. Private headers
are not copied; credential-bearing binaries/log evidence remain local outside Git.
Host remains running with C; passive serial capture is released at completion
without another reset. No scheduler, automation or R2 implementation.

ROUND2_R1B = PASS
REAL_DEVICE_REPORTING = VERIFIED
REAL_DEVICE_OBSERVABILITY = VERIFIED
SOFTWARE_STATUS_CORRELATION = PASS
PHYSICAL_SCREEN_OBSERVATION = PASS
304_SEMANTICS_REAL_DEVICE = VERIFIED
ROUND2_STATUS = R1B_VERIFIED
Exact physical FULL count = NOT MEASURED.
BUSY fault injection = NOT RUN; LONG_DURATION = NOT RUN.
Partial refresh/power/deep sleep/discovery/provisioning/PWA/OTA/cloud = NOT VERIFIED.
R2 = NOT STARTED.
NEXT_ALLOWED_STAGE = R2; this request stops at R1B, pending separate R2 instruction.

Only PROJECT_STATE.md is appended. Product implementation and firmware behavior
changes = NONE. Local checkpoint message:
`test: verify round 2 observability on device`.
Resolve checkpoint SHA from Git; no self-referential hash embedded here.
No push/tag/remote operation; stop after the local checkpoint.

# 26. Round 2 R2A — Host Discovery Software Contract

Date: 2026-10-03. Scope: software implementation, mocked Python contracts,
full regression, C++ compile check and target firmware build only.
HEAD_BEFORE = `7ca5027f7d719caa4f2ecb4bf83fdeef998ad67b` (R1B checkpoint).
Initial `git status --short` output was empty; worktree and index = CLEAN.
Historical sections 1-25 and R0/R1A/R1B conclusions remain unchanged.

## Actual contract and preserved path

Service type = `_eink-panel._tcp.local.`; instance =
`eink-panel._eink-panel._tcp.local.`; target = `eink-panel.local.`.
Python had no mDNS dependency; requirements.txt now pins zeroconf==0.151.5.
Installed into the existing Python 3.12 environment (direct transitive dependency
ifaddr==0.2.0); installation and naming validation evidence remain external.

LAN entry: `python -m server.main --host <LAN-IPv4> --port 8000`.
The selected bind IPv4 and port are shared by Uvicorn and the FastAPI lifespan
advertisement, including nondefault port. Startup registers one fixed identity
on that interface; shutdown unregisters and closes. Expected interface/name
registration failure releases resources and preserves HTTP availability.
Default loopback 127.0.0.1:8000 and direct ASGI imports do not advertise; direct
uvicorn CLI invocation does not infer bind/port. No rendering at advertisement
startup or status query. Existing HTTP handlers and publication schema unchanged.

Firmware uses bundled Espressif mDNS, no new PlatformIO dependency. One bounded
1000 ms PTR query precedes each normal frame HTTP transaction. A single matching
instance with valid IPv4/port yields DISCOVERED; unavailable/invalid discovery
yields CONFIGURED_FALLBACK from unchanged private macros NETWORK_HOST_IPV4 and
NETWORK_HOST_PORT. Private network/display header hashes match R1B; contents and
credentials are not copied into Git. No Wi-Fi initialization/configuration change.

Selected endpoint remains stable through frame GET and both device reports,
using the same existing SocketOwner and HTTP machine; only socket destination
and Host header use the resolved endpoint. Resolver retains source internally,
adds no publication state and does not validate/render/display frames. Existing
state enum numeric values are retained by appending HostResolve. Discovery is
outside unchanged HTTP/TCP budgets, query resources are freed; no history/cache,
retry framework, scanning or multi-Host arbitration. HTTP failure keeps the
existing wait behavior. Frame length/format/SHA/ETag/200/304/LKG and standard FULL
display implementation, driver and R1A report payload/stages remain unchanged.

## Verification and evidence limits

| Verification | Exact command / result |
| --- | --- |
| New Python contracts | `D:/Codex/eink-panel/.venv/Scripts/python.exe -m pytest tests/test_host_discovery.py -q`; collected 13, passed 13, failed 0, exit 0 |
| Full historical + new Python regression | `D:/Codex/eink-panel/.venv/Scripts/python.exe -m pytest`; collected 393, passed 393, failed 0, exit 0 (380 historical + 13 new) |
| C++ harness compile | `D:/Codex/eink-panel/.venv-hw/pio-core/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe -std=c++17 -Wall -Wextra -Werror -c tests/cpp/test_network_progress.cpp -o D:/Codex/round2-r2a-20261003-a5b3/network-harness.o`; exit 0 |
| Target firmware | `D:/Codex/eink-panel/.venv-hw/Scripts/python.exe -B -m platformio run -d C:/Users/cslki/.codex/worktrees/a5b3/eink-panel/hardware/gdey042t81_esp32 -c D:/Codex/round2-r2a-20261003-a5b3/platformio-round2-r2a.ini -e esp32-m1-network-progress --disable-auto-clean -j 4`; SUCCESS, exit 0 |

Host tests mock every Zeroconf engine and listener, testing stable identity,
actual bind port, startup without render, shutdown release, unavailable service,
loopback and real in-process frame/status/304/report behavior.
The first new test run was 12 passed / 1 failed due to a new assertion expecting
null after an accepted event; the existing correct HOST_ACCEPTED expectation was
restored in the test only. No historical product failure or unrelated fix.

C++ harness adds both endpoint decisions, existing transport reuse, source change
on 304, bad length/SHA/format/extra bytes preserving LKG, report destination/header,
invalid endpoint fallback and resolver without render/display/frame validation.
Native g++/clang++/cl were not found. CXX_COMPILE_CHECK = PASS; CXX_RUNTIME = NOT RUN.
These C++ assertions were compiled, not executed. R2A acceptance uses the explicitly
permitted compile-only harness gate; real service query/IPv4 changes are unverified.

RAM = 62,504 / 327,680 bytes (19.1%); R1B 60,576 -> delta +1,928 bytes.
Flash = 780,129 / 1,310,720 bytes (59.5%); R1B 754,661 -> delta +25,468 bytes.
These are build-reported static resource facts, not runtime heap/latency evidence.
Build uses an external copy of the current PlatformIO config with external build
output, existing core/libdeps and the unchanged REAL-RUNTIME private inputs.
No upload, serial access, reset, real mDNS advertisement/query, LAN change or screen
observation. Existing R1B Host/device processes were not restarted or modified.

Evidence root: `D:/Codex/round2-r2a-20261003-a5b3/`.
preflight.json, dependency-install.log, new-tests.json, python-regression.json/log,
network-harness-compile.json/log and network-build.json/log record commands/results.
Private configuration and credential-bearing firmware binaries remain outside Git.
Final Git review records diff --stat, diff --check and status, checks only R2A
files are staged, frozen kernel portions/private headers are unchanged, and both
state documents retain their prior bytes as an exact prefix.

ROUND2_R2A = PASS
ROUND2_STATUS = R2A_SOFTWARE_VERIFIED
REAL_LAN_DISCOVERY = NOT RUN
PHYSICAL_VALIDATION = NOT RUN
CXX_RUNTIME = NOT RUN
R2B = NOT STARTED
R3 = NOT STARTED
NEXT_REQUIRED_STAGE = R2B (separate authorization required).

Local checkpoint message: `feat: add round 2 host discovery`.
Resolve checkpoint SHA from Git; no self-referential hash embedded here.
No push/tag/release/deploy, no R2B/R3 or later stage work. Stop after R2A checkpoint.
