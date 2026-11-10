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


Read `docs/GOAL.md` first (mainline goal, completed baseline, reopen protocol), then this
file (facts, evidence and the latest stage section). If the two disagree, the latest factual
section here wins; backfill `docs/GOAL.md` afterwards.


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


---

# 27. Round 2 R2B — Real LAN Host Discovery Verification

Date: 2026-10-04 (Asia/Shanghai). Final bounded C/D acceptance only.
HEAD_BEFORE = `029c6e5cabe3a0aebf33c72de7733293b2fe77d4` (R2A checkpoint).
Initial worktree/index = CLEAN. BIN/ELF and REAL-RUNTIME private header hashes
match the previously recorded R2A/R2B artifacts. The original device connection
was restored by the user; passive COM11/115200 capture used DTR/RTS false, no
buffer clear or reset. Target WLAN packets verify ESP32 IP 192.168.100.104 and
MAC 1c:c3:ab:1f:5f:d0. Sections 1-26 retain their exact original bytes.

## Reused evidence and actual environment

- A = PASS / reused, including the original direct screen observation.
- B = PASS / reused. DISCOVERY_CAUSAL_PROOF =
  VERIFIED_BY_NEW_ENDPOINT_OBSERVATION. Old .101 TCP state remains AMBIGUOUS;
  no new probe of the configured fallback was performed.
- R2A regression 393/393 PASS and firmware build PASS are reused after hash and
  clean-baseline checks. No tests, full regression or firmware build rerun.
- Previous NET-DIAG: 2/2 natural polls selected .220, completed TCP and reached
  HTTP. Its fresh Host had no frame and returned 503; this is transport evidence,
  not a previous successful C publication.

Temporarily moved the same WLAN from DHCP .101/24 to static .220/24, preserving
SSID, gateway .1 and original IPv4 DNS .1. .220 bound, .101 absent, gateway
reachable. The formal `python -B -m server.main --host 192.168.100.220 --port 8000`
entry used EINK_PROGRESS_SOURCE=round2-r2b-lan, an actual .220:8000 listener and
the unchanged `_eink-panel._tcp.local.` service identity advertising .220:8000.
Native pktmon WLAN capture started before Host startup and continued through C,
the physical confirmation and D; 11:17:20-11:22:16 +08, 296.128 seconds.
Filters were limited to ESP32 TCP/8000 and WLAN mDNS/5353. Raw evidence stays local.

## Scenario C — new publication and physical confirmation

One new exact payload: R2B-B / DISCOVERED / HOST FOUND / 74%, with newly generated
event_id, occurred_at and updated_at. One offline gate used the existing
EventStateStore and ProgressFramePublisher/Host renderer: FRAME_READY, 15000
bytes, non-null SHA. The same payload was published once through POST /api/events;
no direct snapshot/cache write, alternate server, reset or second publication.

C_EVENT_ID = `r2b-c-observed-20261004T031622637437Z`.
C_FRAME_VERSION =
`d387bdb47f3c069b8635274263c571341548257ef99ec3f63096884c1942c0f4`.

Natural polling observation: 11:17:44-11:19:54 +08, 130.000 seconds.
Actual mDNS query and Host WLAN answer advertising .220 were captured. The
ESP32 SYN/SYN-ACK and GET 200 used .220:8000 (source port 53696). Real POSTs
carried DEVICE_FRAME_ACCEPTED (53697) then DEVICE_REFRESH_FLOW_COMPLETE (53698),
both with the same C frame_version and Host 200/recorded acknowledgments.
Host status observed acceptance at 11:18:13.967 and completion at 11:18:16.396.
SHA-256 of the full formal Host response = C frame_version = captured accepted
report frame_version = captured completion report frame_version.

User explicitly confirmed: "观察到真实刷新，四项内容均正确".
C = PASS; PHYSICAL_SCREEN_OBSERVATION = PASS, from that direct human reply.
Software completion and physical observation remain separate evidence classes.

## Scenario D — unchanged frame at the discovered endpoint

Only after C software and physical PASS, observed 11:20:45-11:21:55 +08,
70.109 seconds, without another event or firmware/Host/frame change.
Real ESP32 GET at .220:8000 (53703) returned HTTP 304, unchanged ETag, zero-byte
response body; If-None-Match equals C frame_version. Subsequent real POST (53704)
carried refresh_stage=null and the unchanged frame_version; Host returned 200.
publish_id, frame_version, accepted_frame_version and completed refresh_stage
remained unchanged while last_seen advanced. Captured report bodies contain no
new accepted/completion stage. Passive serial states 16,4,5,6,8,15,12 show the
communication path, with neither DisplayPending(10) nor DisplayUpdate(11).
D = PASS; D_FAKE_ACCEPTED = NO; D_FAKE_COMPLETE = NO; D_DISPLAY_UPDATE = NO.

D human visible observation: NOT CONFIRMED; no visible-change observation is inferred from software.
PRECISE_PHYSICAL_FULL_COUNT = NOT MEASURED; no claim of zero physical FULL cycles.

## Evidence limits, retained anomaly and restoration

Historical TcpConnectFailure is preserved: OBSERVED_ONCE, ROOT_CAUSE =
NOT DETERMINED, REPRODUCED_IN_NET_DIAG = NO. Subsequent observed polls show
DISCOVERY + TCP + HTTP PASS. No repair or reliability investigation was added;
bounded current C/D acceptance does not establish every future poll's reliability.

The capture proves actual endpoints, HTTP headers and the complete device report
bodies. Some C frame-response TCP segments are absent from the capture; whole
wire-body SHA = NOT MEASURED. Frame SHA correlation uses the saved full 15000-byte
formal Host response and captured device report identities. Host multicast Tx is
observed; direct mDNS receipt inside the device is not separately measured.
Initial external analysis demanded complete wire-body reassembly and marked its
capture gap insufficient; that analysis is preserved and superseded by the final
explicit-contract correlation, without raw capture changes or runtime repetition.
Four frame-GET polls and nine HTTP connections were captured; eight initial TCP
SYN connections were observed. SYN counts include POSTs and are not poll counts.

Host gracefully stopped and lifespan unregistered; capture and passive serial
observer stopped; own filters removed and prior pktmon idle/filter state restored.
WLAN DHCP IPv4 and automatic DNS restored, .220 removed, .101/24 restored,
gateway .1 reachable, DNS .1/DHCP and SSID unchanged: NETWORK_RESTORED = VERIFIED.
No test worker, Host or serial process remains. No firmware/private configuration,
product code, test, renderer, polling, driver or display-behavior changes.

REAL_FALLBACK_RUNTIME = NOT RUN; BUSY_FAULT_INJECTION = NOT RUN;
LONG_DURATION = NOT RUN; PRECISE_PHYSICAL_FULL_COUNT = NOT MEASURED.

External evidence root: `D:/Codex/round2-r2b-final-observed-20261004-a5b3/`.
preflight.json, scenario-c-preflight-render.json, scenario-c-publication.json,
scenario-c-runtime.json, scenario-c-physical-confirmation.json, scenario-d-304.json,
scenario-c/d-packet-evidence-final.json, http-wire-flows-final.json,
analysis-authority.json, acceptance-gate.json, network-restore.json and
cleanup-verification.json record the final evidence. Original capture.etl,
capture.pcapng, capture.txt, raw frame and temporary helpers remain outside Git.

ROUND2_R2B = PASS
REAL_LAN_DISCOVERY = VERIFIED
PHYSICAL_VALIDATION = PASS (C direct observation; A reused)
ROUND2_STATUS = R2B_VERIFIED
R3 = NOT STARTED
NEXT_ALLOWED_STAGE = R3 (separate instruction required; this request stops here)

Only PROJECT_STATE.md is appended. Local checkpoint message:
`test: complete round 2 host discovery verification`.
Resolve its SHA from Git; no self-referential hash embedded here.
No push/tag or next-stage work.


---

# 28. Round 2 R3A — Wi-Fi Provisioning Software Contract

Date: 2026-10-04 (Asia/Shanghai). Software implementation only.
HEAD_BEFORE = `a80be902e7ddddee975f7306af7dba50f6d98ef8` (R2B checkpoint).
Initial worktree/index = CLEAN, captured before any edit. Baseline/private header
hashes checked against current R2B evidence. No history rewritten.

## Implementation and frozen boundaries

- Existing configured SSID/password still come from REAL-RUNTIME private macros
  via config.h. Validated persisted credentials take priority; missing/invalid
  stored data selects the original configured credentials. No credential values
  were printed, copied into tracked files or changed in private input headers.
- wifi_provisioning.h supplies the minimal hardware-independent controller;
  wifi_esp32.h uses existing WiFi/SoftAP, WebServer and Preferences. NVS namespace
  eink-wifi/key validated stores one current SSID/password blob after success.
- Explicit Machine::requestProvisioning() accepts only initialized PollWait or
  FailureWait with the existing HTTP/report socket idle. No verified input button
  exists; no GPIO/serial/boot trigger invented. Normal timeout/failure never opens AP.
- Provisioning session starts open eink-panel-setup AP in AP+STA mode; local form
  GET / and POST /configure bind AP default 192.168.4.1:80. No scan/captive DNS or
  management UI. Candidate attempt is bounded by 15000 ms from submission.
- Old association must end before candidate begin. WL_CONNECTED, nonzero STA IP
  and candidate SSID define success, independently of Host availability. Failure
  keeps previous credentials and AP; save is only attempted after success. New
  instance loads successful persisted credentials. Success stops AP/server then
  returns the same Machine to its original HostResolve state.
- Fixed SDK adaptation: begin() can inherit prior failure status, which is allowed
  to reach the bounded timeout rather than rejecting the new attempt immediately.
  AP removal calls enableAP(false) directly; SDK 2.0.17 softAPdisconnect(true)
  compares the bool result to ESP_OK, inverting it. These are local source-audited
  API adaptations, not real SoftAP evidence.
- Host product logic, renderer, Progress/event/publication/status APIs, R2 resolver,
  SocketOwner/frame/report code, SHA/ETag/200/304/LKG, H1 standard FULL/display,
  pins and tracked platformio.ini are unchanged. No new dependency/framework.

## Executed checks and evidence classes

NEW_TESTS = PASS: 23 C++17 static_assert checks evaluate the production controller
with fake Wi-Fi/storage/AP at compile time. Covers configured/persisted selection,
normal failure with no AP, explicit entry/AP lifecycle, candidate connect-before-
save, old association isolation, success/failure/timeout/old credentials, save
failure and simulated new-instance reload. This is compiler evaluation, not native
C++ runtime or hardware execution.

Focused command (exit 0):
`D:/Codex/eink-panel/.venv-hw/pio-core/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe -std=c++17 -Wall -Wextra -Werror -c tests/cpp/test_wifi_provisioning.cpp -o D:/Codex/round2-r3a-20261004-a5b3/wifi-provisioning-contract.o`

CXX_COMPILE_CHECK = PASS (exit 0): same existing Xtensa compile command for
`tests/cpp/test_network_progress.cpp`, output
`D:/Codex/round2-r3a-20261004-a5b3/network-harness.o`.
The original runtime assert matrix and three new provisioning/R2 integration
cases compile; their runtime assertions were NOT executed. Static review confirms
normal saved connection and provisioning success enter the original HostResolve,
with no duplicate resolver/HTTP/display path.
CXX_RUNTIME = NOT RUN: no native g++/clang++/cl on PATH; no compiler installed.

FULL_REGRESSION = PASS: actual recorded command
`D:/Codex/eink-panel/.venv/Scripts/python.exe -m pytest` from this worktree;
collected 393, passed 393, failed 0, errors 0, exit 0. No Python product/test edits.

NETWORK_BUILD = PASS: final command (exit 0, 48.789 s PlatformIO):
`D:/Codex/eink-panel/.venv-hw/Scripts/python.exe -B -m platformio run -d C:/Users/cslki/.codex/worktrees/a5b3/eink-panel/hardware/gdey042t81_esp32 -c D:/Codex/round2-r3a-20261004-a5b3/platformio-round2-r3a-final.ini -e esp32-m1-network-progress --disable-auto-clean -j 4`

RAM = 64,568 / 327,680 bytes (19.7%); R2A 62,504 -> delta +2,064 bytes.
FLASH = 834,405 / 1,310,720 bytes (63.7%); R2A 780,129 -> delta +54,276 bytes.
Static build resources only, not runtime heap/latency or physical evidence.
Final BIN SHA-256 = f6cf27d602c89155eb02bce43a7e085330f0ccb50a7c4a1d43f660c8c41d437c.
Final ELF SHA-256 = 3104bbbe7f2d35fefca596c3b9c39089da2d4488dc0b887158655e7b147e6549.

Build reused the accepted external PlatformIO config, existing core/libdeps and
unchanged REAL-RUNTIME headers. Initial build and its artifacts are retained;
only the affected ESP adapter required a second build after source audit. Focused
controller, harness and Python checks remain valid because their checked sources
were unchanged after their successful runs. Final build uses network-build-final;
no initial evidence file/artifact overwritten.

Evidence root: `D:/Codex/round2-r3a-20261004-a5b3/`.
preflight.json, focused.json/log, cpp.json/log, python.json/log, build.json/log,
build-final.json/log and final-review.json record exact commands/results/review.
Credential-bearing firmware artifacts and private inputs remain outside Git.
Only six R3A firmware/test files and appended sections of the two state/plan
files are staged; historical sections retain their original content.

ROUND2_R3A = PASS
ROUND2_STATUS = R3A_SOFTWARE_VERIFIED
REAL_SOFTAP = NOT RUN
REAL_WIFI_SWITCH = NOT RUN
REAL_PERSISTENCE_REBOOT = NOT RUN
PHYSICAL_VALIDATION = NOT RUN
FLASH_UPLOAD = NOT RUN
SERIAL_RUNTIME = NOT RUN
R3B = NOT STARTED
R3C = NOT STARTED
NEXT_REQUIRED_STAGE = R3B (separate authorization required).

Local checkpoint message: `feat: add round 2 wifi provisioning`.
Resolve checkpoint SHA from Git; no self-referential commit hash embedded here.
No upload/reset/COM11/mobile provisioning/network changes, push/tag/release,
BLE/PWA/OTA/cloud or R3B/R3C work. Stop after the R3A checkpoint.


---

# 29. Round 2 R3A.1 — Provisioning Trigger Binding

Date: 2026-10-04 (Asia/Shanghai). Tiny software binding only.
HEAD_BEFORE = `0dbbe5d4083896ee55c53278c25386cb6ca3504a` (R3A checkpoint).
Initial worktree/index = CLEAN. No prior section rewritten.
R3B previously stopped before upload at REAL_PROVISIONING_TRIGGER_NOT_BOUND;
its evidence stays at D:/Codex/round2-r3b-20261004-a5b3/, without edits.

## Hardware evidence gate and implemented gesture

BOARD = Good Display ESP32-M1 / ESP32-WROOM-32D; lolin32 is its existing compile mapping.
EXISTING_USER_BUTTON = YES: original E13 photo shows side KEY button; official
ESP32-M1 V1.0.pdf physical page 5 Figure 1 item 7 calls it a custom button.
TRIGGER_TYPE = Existing KEY/S1 only.
TRIGGER_GPIO = 25: sole-page schematic MCU block maps S1 pin2/KEY1 to U5 IO25,
module pin10; button's other contacts are GND. Board BOOT IO0 and RST are separate.

Original evidence hashes rechecked against STEP013_EVIDENCE_MANIFEST:
- ESP32-M1-SCH-20260307.pdf: 06baa8124052e4762e1d2bf6642f4371e2bdc620da246b8f4c704e418fd9f4bf.
- ESP32-M1 V1.0.pdf: 60595f7d9aefdcd5d7257354476d9236eb83f4ff61e9d48e68d898ea0c217b7e.
- A711E9B9395EB78D9951E70E9949AB20.jpg: a1d6baac48488348323a66e30a53f7a669118248bf9489a7381bceea1af5593a.

RUNTIME_READ_SAFE = YES by schematic/module/framework source audit, not measured
GPIO runtime. INPUT_PULLUP makes released HIGH, pressed LOW; Arduino GPIO API
uses gpio_config/gpio_get_level, without ADC/DAC. GPIO25 is not a module strapping
or Flash pin, and no current product code uses it. Module datasheet authority:
https://documentation.espressif.com/esp32-wroom-32d_esp32-wroom-32u_datasheet_en.html,
sections 2, 3 and 4.2.1. No electrical test or new wiring/hardware modification.
PIN_CONFLICT = NO: current private display pins remain 12/13/14/18/23/27;
fixed H1 compile guards already enforce those pins. No board-definition changes.

provisioning_button.h holds only the GPIO constant, fixed timing/latch/pending
logic and original request dispatch. main.cpp configures GPIO25 once after
successful WifiInit reaches WifiConnect, then polls the input from the old loop.
TRIGGER_GESTURE = Released input after initialization, then stable 2000 ms hold;
30 ms debounce for press/release. A held-across-boot button cannot trigger until
released and deliberately held again. Normal no-button boot stays unchanged.
SAFE_STATES = Initialized PollWait / FailureWait; the original Machine guard
remains authoritative. Busy transactions record at most one pending bit and wait
for the next allowed boundary. No queued commands or transaction interruption.
ONE_PRESS_ONE_REQUEST = YES: stable release is required to rearm; a failed request
is not retried from the same hold. FaultStop performs no button read/dispatch.

R3A_CORE_CHANGED = NO. machine.h, wifi_provisioning.h, wifi_esp32.h, config.h,
Preferences schema/namespace/key, SoftAP SSID/mode/routes, candidate success and
15000 ms budget, persist-after-success, old-credential preservation, original
HostResolve/R2 resolver, HTTP/frame/report/display, Host and renderer are unchanged.
No additional trigger path, serial command, debug API, failure trigger or dependency.

## Verification results and limits

NEW_TESTS = PASS: 20 C++17 static_assert cases evaluate the production helper with
fake machine/time/input at compile time; exit 0. They check no press, sub-threshold
hold/bounce, both safe states, one continuous hold, second hold after release,
deferred Wi-Fi/discovery/HTTP/frame/display/report/candidate states, boot/init
failure, held-at-boot, failed request and release bounce. No real GPIO involved.
Command: `D:/Codex/eink-panel/.venv-hw/pio-core/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe -std=c++17 -Wall -Wextra -Werror -c tests/cpp/test_provisioning_button.cpp -o D:/Codex/round2-r3a1-20261004-a5b3/provisioning-button-contract.o`.

CXX_COMPILE_CHECK = PASS: existing network harness with two new actual-Machine
button scenarios compiles, exit 0. Covers deferred Wi-Fi connection through
PollWait/FailureWait into provisioning and then the original HostResolve.
Command: same accepted Xtensa C++17/-Wall/-Wextra/-Werror compile of
`tests/cpp/test_network_progress.cpp`, output
`D:/Codex/round2-r3a1-20261004-a5b3/network-harness.o`.
CXX_RUNTIME = NOT RUN: no native g++/clang++/cl on PATH; integration runtime
assertions were compiled only. No compiler installation or hardware execution.

FULL_REGRESSION = PASS, freshly executed from this worktree:
`D:/Codex/eink-panel/.venv/Scripts/python.exe -m pytest`;
collected 393, passed 393, failed 0, errors 0, exit 0 (6.44 s pytest).
No Python product/test changes.

NETWORK_BUILD = PASS, exit 0 (54.503 s PlatformIO):
`D:/Codex/eink-panel/.venv-hw/Scripts/python.exe -B -m platformio run -d C:/Users/cslki/.codex/worktrees/a5b3/eink-panel/hardware/gdey042t81_esp32 -c D:/Codex/round2-r3a1-20261004-a5b3/platformio-round2-r3a1.ini -e esp32-m1-network-progress --disable-auto-clean -j 4`.
Uses the accepted external copy of current PlatformIO configuration, existing
core/libdeps and unchanged REAL-RUNTIME private inputs. No upload.
RAM = 64,584 / 327,680 bytes (19.7%); R3A 64,568 -> delta +16 bytes.
FLASH = 834,669 / 1,310,720 bytes (63.7%); R3A 834,405 -> delta +264 bytes.
Static resource facts only, not runtime heap/timing evidence.
BIN SHA-256 = a64b569a6bc499518068f9eff3d0cff633c6a897ccb71d0bb2360a143e4c2b2c.
ELF SHA-256 = c3771fac7a7864ebe74cafc659292c923b0b9d870c080e6a9b01dbfae1d44496.
Credential-bearing build artifacts stay outside Git.

External evidence root: `D:/Codex/round2-r3a1-20261004-a5b3/`.
hardware-trigger-audit.json, preflight.json, focused.json/log, cpp.json/log,
python.json/log, build.json/log and final-review.json retain commands, results,
source hashes and hardware gate evidence. Read-only PDF renders stay external.
Poppler reported unavailable Symbol/ArialUnicode display fonts; relevant circuit
and manual figure labels were visually legible and cross-checked with the photo.
No original evidence changed or credentials printed/copied into evidence/Git.

ROUND2_R3A1 = PASS
ROUND2_STATUS = R3A1_TRIGGER_SOFTWARE_VERIFIED
REAL_TRIGGER_VALIDATION = NOT RUN
REAL_SOFTAP = NOT RUN
REAL_WIFI_SWITCH = NOT RUN
FLASH_UPLOAD = NOT RUN
SERIAL_RUNTIME = NOT RUN
REAL_REBOOT_PERSISTENCE = NOT RUN
PHYSICAL_VALIDATION = NOT RUN
R3B = NOT STARTED (no real verification this stage; historical blocked audit retained)
R3C = NOT STARTED
NEXT_REQUIRED_STAGE = R3B (new checkpoint, separate authorization).

Only six directly related files are changed: main.cpp, new button helper, new
button contract tests, existing network harness, and appended plan/state sections.
Local checkpoint message: `feat: bind wifi provisioning trigger`.
Resolve checkpoint SHA from Git; no self-referential hash embedded here.
No push/tag/upload/serial/real button press/SoftAP/Wi-Fi/NVS/display validation.
Stop after the R3A.1 checkpoint; R3B/R3C require a separate instruction.


---

# 30. Round 2 R3B — Real Provisioning Attempt (Blocked by Firmware Crash)

Date: 2026-11-07 (Asia/Shanghai). Real-device attempt only; no product code change.
HEAD_BEFORE = `43bf82c5287800b70ce666d60574622a59196901`.
Initial worktree = untracked `docs/PROJECT_OVERVIEW_2026-11-03.md` only; product sources unchanged.

## Current identity and preconditions

- Device MAC `1C:C3:AB:1F:5F:D0` -> IPv4 `10.111.16.216` on REDIAN 2.4 GHz, channel 6,
  WPA3-H2E, required MFP. PC/Host = `10.111.16.75`.
- mDNS `_eink-panel._tcp.local` discovery and a real device TCP/HTTP request were already
  verified before this attempt.
- Running firmware ELF SHA-256 = `c3771fac7a7864ebe74cafc659292c923b0b9d870c080e6a9b01dbfae1d44496`,
  identical to the R3A.1 build artifact.
- One deterministic Progress test frame was published under
  `EINK_PROGRESS_SOURCE=r3b-real-20261107`: publish_id `r3b-real-20261107-001`, 15000 bytes,
  ETag/SHA-256 `5a3f7585fed26781fa474cc1bbd912e79c7509a1ee7ec2c9267e522a03884a5d`.
- The device fetched it with HTTP 200, reported `DEVICE_REFRESH_FLOW_COMPLETE` (firmware
  identifier `round2-r1a-1`), and the operator confirmed the test content on the panel.

## Provisioning attempt and crash

- 16:47:02: operator pressed and held the existing KEY/S1; serial entered Provisioning (17).
- SoftAP `eink-panel-setup` observed at BSSID `1c:c3:ab:1f:5f:d1`, 2.4 GHz channel 6, open.
- Operator connected a second laptop and submitted the form at about 16:56; the page returned
  the production 202 text ("Connecting. Save follows successful LAN connection...").
  Credentials were typed only by the operator and were not recorded.
- 16:54:55: `WebServer.cpp:638 _handleRequest(): request handler not found` (unknown path).
- 16:56:13: `CORRUPT HEAP: Bad head at 0x3ffd404c`; `assert failed: multi_heap_free
  multi_heap_poisoning.c:259`; reboot with `rst:0xc (SW_CPU_RESET)`.
- Decoded backtrace: `panic_abort -> esp_system_abort -> __assert_func -> multi_heap_free ->
  heap_caps_free -> free -> mem_free -> do_memp_free_pool -> memp_free -> tcp_free ->
  tcp_abandon -> tcp_abort -> tcp_do_abort (api_msg.c:863) -> tcpip_thread_handle_msg`.
- The assert is the detection point in the lwIP TCP PCB free path; the corrupting write is
  earlier and not yet identified. No fix was attempted.

## Post-crash observations

- The device rebooted on its own (operator did not touch hardware), rejoined REDIAN, fetched
  the same frame with HTTP 200 at 16:56:19, and completed another FULL refresh at 16:56:22.
- Subsequent polls are HTTP 304 with normal report/PollWait cycles.
- SoftAP absence is explained by the reboot; it is not evidence of a successful
  `stopSoftAP()` after save.

## Result and limits

- R3B = BLOCKED / PARTIAL. The 202 is operator-confirmed but no HTTP headers were captured.
  No `17->16`, no persist-return and no attributable AP-close evidence.
- The 16:56 crash is a product-defect candidate in the provisioning path; root cause is
  UNKNOWN. R3C remains NOT STARTED; the post-reboot association is not used as persistence
  proof. The original 2026-10-04 POST gap remains UNKNOWN; this is a new run.
- Evidence root: `D:/Codex/round2-r3b-real-20261107/` (serial.log, serial2.log, host.log,
  frame-headers.txt, frame.bin, status-after-frame.json, crash-analysis.json,
  backtrace-decoded.txt).
- No product code change, no NVS erase, no reflash, no new POST, no credential exposure,
  no R3C action. Host and serial helpers stopped.

NEXT_REQUIRED_STAGE = separately authorized root-cause/minimal-fix stage for the provisioning
heap corruption; no automatic retry. Re-run R3B acceptance only after a verified fix.

---

# 31. Round 2 R3B — Provisioning Heap Corruption: Root Cause and Minimal Fix

Date: 2026-11-07 (Asia/Shanghai). Separately authorized root-cause/minimal-fix stage; upload
to COM12 and one controlled retest were authorized afterwards.

## Scope and constraints

- Scope was limited to the provisioning heap corruption observed in §30. R3C, NVS erase,
  credential capture and any second/modified frame stayed out of scope.
- The operator alone entered Wi-Fi credentials on `http://192.168.4.1/`; no credential was
  recorded in logs, evidence or Git.

## Trigger isolation

- The crash was reproduced on the R3A.1 ELF (`c3771fac...e1d44496`). The decoded backtrace
  ended in `tcp_abort -> tcp_abandon -> tcp_free -> multi_heap_free`; that assert is the
  detection point, not the corrupting write.
- Hypothesis 1 (the WebServer closing a second AP-side client) was rejected: GET `/` plus a
  404 request did not crash.
- Hypothesis 2 (synchronous `WiFi.disconnect` alone) was weakened: two POST `/configure`
  submissions with invalid/empty credentials returned 202 and did not crash.
- The evidence converged on disabling the SoftAP while the Arduino WebServer still owned
  AP-side TCP PCB(s). The POST handler returned 202 and the candidate path then stopped the
  AP; lwIP aborted the still-owned PCB and the abort/free path hit corrupted state.
- The corrupting write itself remains unidentified. The fix removes the precondition instead
  of claiming the corruption mechanism is understood.

## Minimal fix

- Only product file changed: `hardware/gdey042t81_esp32/src/network_progress/wifi_esp32.h`
  (16 insertions, 1 deletion).
- After sending 202, the handler calls `server_.stop()` and records `serverStopped_` before
  the 15 s candidate window, so no AP-side TCP PCB is owned when the AP is disabled.
- `pollProvisioning`: a failed candidate that returns to Provisioning reopens the listener so
  the operator can retry; a pending candidate keeps it closed; success keeps it closed.
- No change to the credential flow, NVS semantics, state IDs, button gesture, display path or
  Host protocol.

## Build and tests

- Isolated build config `D:/Codex/round2-r3b-fix-20261107/platformio-round2-r3b-fix.ini`;
  build directory outside the repository.
- Build SUCCESS. RAM 64,584 B (19.7%); Flash 834,749 B (63.7%, +80 B vs R3A.1).
  BIN SHA-256 `834f7215687384d759074a9e618810890cc84e3a6253746da3b75ce0fe746868`
  (841,328 B); ELF SHA-256
  `309b0318f3a49fec82c3fd8b7bfd14910467ec59d212f39b3fa851175c9e270b`.
- Host suite on this tree: 393 passed.
- Upload to COM12 SUCCESS; NVS not erased; no other flash operation.

## Controlled real-device retest

- Provisioning path (the previously crashing case): 17:34:19 serial entered state 17 after
  the operator held KEY/S1; the operator submitted the form from a second laptop; 17:36:16
  serial entered state 16 with FAILURE=0. The candidate succeeded, the AP closed, and there
  was no panic and no reboot.
- A deliberate second press re-entered Provisioning at 17:36:17.835; this is the expected
  one-press-one-request gesture, not a defect. State 13 with FAILURE=6 at 17:36:17.822 was
  the Host returning 503 (no source published at that moment), not a device fault.
- True USB power cycle at 17:44:24. Boot was `1->2->3->16->4->5->6->13` with FAILURE=6 and no
  panic. At 17:45:08 the same deterministic frame was republished
  (`r3b-real-20261107-001`, 15000 bytes, SHA-256
  `5a3f7585fed26781fa474cc1bbd912e79c7509a1ee7ec2c9267e522a03884a5d`).
- 17:45:30 the device fetched it with HTTP 200; serial showed `16->4->5->6->7->8->9->10->15->11`,
  `_Update_Full : 2182000`, and the next poll was HTTP 304. Host status reported
  `DEVICE_REFRESH_FLOW_COMPLETE` (firmware identifier `round2-r1a-1`), and the operator
  confirmed `R3B 72 RUNNING` on the panel.

## Evidence classes and limits

- Software, build, runtime and physical evidence are recorded separately above; none is used
  to substitute for another.
- The 202 response is operator-confirmed but HTTP headers were not captured.
- AP close is inferred from `17->16` and the AP's absence after success; no simultaneous
  Wi-Fi scan captured the transition itself.
- The underlying lwIP heap-corruption mechanism is not fully identified; only the precondition
  (AP disable with owned AP-side PCB) is removed.
- The original 2026-10-04 POST gap remains UNKNOWN and is not reclassified.
- R3C (association persistence across a controlled cycle) remains NOT STARTED. The 17:44
  power cycle restored normal operation and is not used as R3C acceptance evidence.

## Result

- R3B = PASS for its in-scope criteria after the fix: provisioning `17->16` without a crash,
  normal Host handoff, HTTP 200 with 15000 bytes and matching SHA-256, and one physical FULL
  refresh confirmed by the operator.
- Evidence root: `D:/Codex/round2-r3b-fix-20261107/` (build.log, upload.log, serial5.log,
  serial6.log, host-fix.log, frame.bin, frame-headers.txt, config).
- Host and serial helpers stopped after the confirmation. No credential exposure, no NVS
  erase, no R3C action.

NEXT_REQUIRED_STAGE = separate authorization for R3C; no automatic start.

---

# 32. Round 2 R3C — Reboot Persistence (Persistence PASS, Host Handoff Blocked)

Date: 2026-11-07 (Asia/Shanghai). Separately authorized R3C stage.

## Scope frozen before the run

- Precondition: the latest saved credential is the one from the §31 fix run
  (17:36:16 `17->16`); the code saves only after a successful candidate and delivers
  HostResolve only after save success.
- One true power-on (USB power removal), no KEY/S1 press, no re-provisioning.
- No new frame published, so the expected Host result is 503 and no physical FULL refresh;
  this avoids an extra refresh for the refresh-count goal.
- Pass criteria: boot `1->2->3->16` without state 17; same device identity; Host reachable;
  SoftAP absent; no NVS erase or reflash.

## Persistence result — PASS

- 17:56:21 USB power removed and 17:56:29 re-powered; the ROM line shows `0x1 (POW...)`
  (POWERON_RESET) and `0x13 (SPI_FAST_FLASH_BOOT)`; no button was pressed.
- Serial: 17:56:30.002 state 1; 17:56:30.005 state 2; 17:56:30.095 state 3;
  17:56:33.072 state 16 with FAILURE=0. No state 17 occurred anywhere in the run.
- ARP: `10.111.16.216 -> 1c-c3-ab-1f-5f-d0` unchanged; PC `10.111.16.75` on REDIAN.
- The device therefore used the persisted credential and re-associated without provisioning.
  This is the R3C persistence result and it is PASS.

## Host handoff — BLOCKED by the mDNS multicast path

- Every 60 s from 17:56:34 to 18:06:11 the device ran `16->4->13` with FAILURE=5
  (TcpConnectFailure). The 3 s connect timeout is consistent with the compile-time fallback
  `192.168.100.101:8000` in the private build header, not with the current Host; the fallback
  is used when discovery yields no address.
- The Host was listening on `10.111.16.75:8000` (curl 200) and advertising
  `eink-panel._eink-panel._tcp.local.` with IPv4 `10.111.16.75` and port 8000.
- Wire observation at 18:02:57: the device sent the mDNS PTR query; the Host answered in
  92 ms with a 135-byte response containing the A record `10.111.16.75` and port 8000. The
  device still fell back and reported FAILURE=5.
- The identical response forwarded unicast to the device at 18:05:06.290 was accepted:
  `16->4->5->6` at 18:05:07.193-222, and the Host logged
  `GET /api/panels/progress/frame` 503 at 18:05:07. The 503 is expected because no frame was
  published. This isolates the normal-path failure to multicast delivery/reception, not to
  persistence or TCP.
- A second unicast forward at 18:06:07.429 did not change the outcome; the forward is not a
  reliable workaround. The failing layer (AP multicast forwarding vs. device mDNS multicast
  receive) is UNKNOWN; no device-side capture was taken.

## Result and limits

- R3C = PARTIAL: persistence PASS; normal post-reboot Host handoff BLOCKED by the multicast
  path. The stale compile-time fallback is a configuration fact, not a persistence failure.
- No product code change, no NVS erase, no reflash, no new frame, no physical FULL refresh,
  no credential exposure. Host and serial capture stopped.
- Evidence: `D:/Codex/round2-r3c-20261107/` (serial.log, host.log, mdns-observation.txt,
  scan.txt, capture.ps1).
- NEXT_REQUIRED_STAGE = separately authorized narrow diagnosis of the mDNS multicast path
  (Host response vs. device receive) before any code change; no automatic retry.

---

# 33. Round 2 — mDNS Multicast Path Narrow Diagnosis

Date: 2026-11-07 (Asia/Shanghai). Separately authorized narrow diagnosis; no product or
Host code change, no NVS erase, no reflash and no new frame.

## Method

- Static inspection of the exact target stack: Arduino-ESP32 2.0.17, ESP-IDF 4.4.7,
  platform espressif32 6.12.0. mDNS and lwIP sources were fetched for v4.4.7.
- Live tests with the existing device, the existing Host and a second Windows laptop on the
  same REDIAN AP.

## Static findings

- `mdns_networking_lwip.c`: the mDNS PCB binds to 5353 and `_udp_pcb_init` calls
  `_udp_join_group`, which calls `igmp_joingroup_netif(netif, 224.0.0.251)` for IPv4 before
  the PCB is created.
- `wlanif.c` sets `NETIF_FLAG_IGMP` but does not assign `netif->igmp_mac_filter`.
- lwIP 2.1.2 `igmp.c` sends the report through `ip4_output_if_opt(..., ROUTER_ALERT, 4)`, so
  the router alert option is present. `lwipopts.h` has `LWIP_IGMP = 1`.
- No missing join call or malformed report was found in the inspected sources.

## Live evidence

1. Second laptop on REDIAN received:
   - `RX 10.111.16.75:5353 135` (Host advertisement response);
   - `RX 10.111.16.216:5353 40` (ESP32 query);
   - `RX 10.111.16.171:5353 40` (the laptop's own query).
   The AP therefore forwards the Host's multicast response to a Windows group member.
2. Continuous unicast ping for 80 s (2365 successes) did not change the single-response
   outcome: the device still ran `16->4->13` with FAILURE=5. Simple radio wake time is not
   sufficient.
3. The PC sent the same 135-byte response from `10.111.16.75:5353` every 200 ms for 80 s
   (399 sends). Serial then showed:
   `18:24:17.372 16`, `18:24:18.491 4`, `18:24:19.205 5`, `18:24:19.208 6`,
   `18:24:19.239 13 FAILURE=6`; the Host logged `GET /api/panels/progress/frame` 503 at
   18:24:19. The 503 is expected because no frame was published.
   This proves the AP forwards the Host's multicast traffic to the ESP32 and the ESP32
   receives and parses it; the one-shot response is unreliable, while repeated responses
   inside the query window are accepted.

## Result and limits

- The blocker is not an AP-wide multicast block, not a response-parser defect and not simple
  power save. The single Host response is lost due to a timing/reliability issue; the exact
  mechanism (IGMP join timing, AP multicast-to-unicast conversion or Wi-Fi DTIM) is UNKNOWN.
- R3C persistence remains PASS. The post-reboot Host handoff failure is now characterized as
  one-shot mDNS response loss, not a persistence or TCP defect.
- Evidence: `D:/Codex/round2-r3c-mdns-20261107/` (serial-ping.log, serial-repeat.log,
  host-ping.log, second-laptop-output.txt, repeat-observation.txt, igmp-static-notes.txt,
  capture scripts). No credential exposure; Host and serial helpers stopped.
- NEXT_REQUIRED_STAGE = separately authorized minimal-fix stage. Candidate directions:
  (a) Host-side repeat/delay of the mDNS response across the device query window; or
  (b) device-side stable mDNS membership / unicast-response request. Choose and freeze one
  under the next authorization; no automatic implementation.

---

# 34. Round 2 — Device-Side mDNS Membership Stability Fix

Date: 2026-11-07 (Asia/Shanghai). The operator selected the device-side direction from §33.

## Change

- One product file changed:
  `hardware/gdey042t81_esp32/src/network_progress/main.cpp` (+10/-2).
- `discoverHost()` now initializes mDNS once through a static `mdnsReady` and no longer calls
  `mdns_free()` after each query. The IGMP membership on 224.0.0.251 therefore stays alive
  across the 60 s polls instead of leaving and rejoining every minute.
- The mDNS component registers netif event handlers and rejoins after a Wi-Fi reconnect.
  Query filtering, Host protocol, state machine, NVS, display and provisioning are unchanged.

## Build and tests

- Isolated config `D:/Codex/round2-r3c-fix-20261107/platformio-round2-r3c-fix.ini`.
- Build SUCCESS. RAM 64,592 B (19.7%, +8 B vs §31); Flash 834,221 B (63.6%, -528 B vs §31).
  BIN SHA-256 `145a8a85b0d1bbfe3cff8497f7922100f5945975b1a94f8c7bbaf14de898a9c3`
  (840,800 B); ELF SHA-256
  `ab08938cbe55bbe473fd1e4ad46dcdba64b2bca9476c66a140014f0729a5bc5f`.
- Host suite: 393 passed.
- Upload to COM12 SUCCESS; NVS not erased; no other flash operation.

## Real-device verification

- Upload reset, first poll: the Host logged a device
  `GET /api/panels/progress/frame` 503 at about 18:30:05 without any repeated-response
  injection. The first query after boot resolved.
- Second poll at 18:31:03: serial `16->4->5->6->13 FAILURE=6`; the Host logged another 503.
  The 503 is expected because no frame was published.
- Controlled true power cycle at 18:32:57-18:33:00 (`0x1 (POW...)` in the ROM line):
  18:33:00.843 state 1, 18:33:00.845 state 2, 18:33:00.939 state 3,
  18:33:03.945 state 16 FAILURE=0, 18:33:05.049 state 4, 18:33:05.092 state 5,
  18:33:05.094 state 6, 18:33:05.112 state 13 FAILURE=6.
  No state 17 and no FAILURE=5; the Host logged the corresponding 503.
- The persisted credential was used; no provisioning and no button press.

## Result and limits

- Device-side fix = PASS for first-query reliability after boot and across polls. The §33
  one-shot mDNS blocker is resolved in this environment.
- The 503 is deliberate (no frame published); the display path was not exercised and no
  physical FULL refresh occurred.
- The Host IPv4-change path was not tested in this stage. The fix keeps the membership, not a
  cached address; the per-poll query remains, but the changed-address case is unverified.
- The mDNS stack now stays allocated. Static RAM is +8 B; dynamic heap/task usage and
  long-run stability were not measured. No crash occurred in the observed window.
- No credential text was added to the logs; no NVS erase, no new frame, no R3C re-run.
  Evidence: `D:/Codex/round2-r3c-fix-20261107/` (build.log, upload-fix2.log, serial-fix.log,
  serial-fixboot.log, host-fix2.log, platformio-round2-r3c-fix.ini).
- NEXT_REQUIRED_STAGE = mainline R4 local management Web, under separate authorization.
  Optional follow-ups if required: Host IPv4-change verification and a longer stability run.


---

# 35. Round 2 R4 — Local Management Web

Date: 2026-11-07 (Asia/Shanghai). Base commit `0288310` (device-side mDNS fix).
Worktree `C:/Users/cslki/.codex/worktrees/a5b3/eink-panel`, detached HEAD; local commit only,
no push/tag.

## Delivered scope

- New lightweight `/manage` page: one identity/connection card (HOST origin, configured
  publish source, frame format, device firmware/last seen), Progress editor, real final-frame
  preview, publish button and same-publication status card. The simulator page links to it.
- Reuses the existing Python ProgressPanel renderer, `PanelUpdateEvent`, `/api/events`,
  frame GET, device-report and status APIs. No new panel, no browser pixel renderer, no PWA,
  no database/event bus, no retry framework.
- `POST /api/panels/progress/preview` accepts the same `PanelUpdateEvent` and returns the PNG
  that produced the frame plus `X-Frame-Version` (SHA-256), `X-Frame-Format` and
  `X-Frame-Bytes`. It is side-effect free: it neither ingests a snapshot nor publishes a frame.
  A regression test asserts the store and publisher stay empty after preview. Preview does not
  require or modify `EINK_PROGRESS_SOURCE`; it is a renderer check, not a publication.
- `services/event_store.py` now exposes `build_snapshot()`. Ingest and preview share one
  normalization path, so preview and publish cannot drift through duplicate validation code.
  `render_transport_assets()` returns the PNG and its transport frame; `render_transport()`
  delegates to it. Preview and publication use the same SHA-256 and 15000-byte T frame.
- Status adds `source` and `frame_format`; existing fields and stage semantics are unchanged.

## Operator truthfulness rules

- SHA comparison is gated on `status.publish_id === draft.event.event_id`. A previous
  publication's frame version cannot produce a false "预览与发布帧不一致".
- A failed status poll renders `状态未知（读取失败；最近成功 …）`, clears the report rows to
  UNKNOWN and disables publishing. It never leaves a stale "刷新流程完成".
- Editing the form while a preview request is in flight discards the stale response via a
  normalized form signature.
- Renderer failures (`Layout:`, contrast, incomplete Progress data) are localized for the
  operator; raw backend detail is not echoed. Input `maxlength` values match measured text
  budgets for the 400×300 layout: title 13, current step 9, status 18, description 17,
  tags 20 (full-width comma accepted), content source 24.
- After a successful publish (or duplicate) the publish button stays disabled for that draft;
  a 409 requires a fresh preview so a new timestamp is generated.

## Tests and review

- Python: 400 passed, including 7 manage API tests (page load, status source/format,
  preview/publish SHA equality, side-effect-free preview, invalid Progress data, malformed
  event, simulator link).
- Node: `node --test tests/frontend/manage_logic.test.mjs` -> 18 passed; `node --check` clean.
- Independent code review found no Critical issues and 6 Important issues (false mismatch,
  stale success after failed poll, edit-during-preview race, duplicated snapshot builder,
  unsafe lengths/unlocalized errors, missing side-effect test). All six were fixed and covered
  by the tests above.

## Browser evidence

- Real browser at `http://127.0.0.1:8000/manage` (separate Host from the device-facing
  `10.111.16.75:8000` process): identity rendered, preview produced a 400×300 PNG with
  frame version `95a99447…`, and the publish button became enabled. No publish was issued
  during this re-check.
- Stopping that Host made the page show `状态未知（读取失败；最近成功 …）`, UNKNOWN in all
  status rows and a disabled publish button.
- Earlier end-to-end run (pre-review-fix, evidence `D:/Codex/round2-r4-web-20261107/`):
  publish `web-mw69zcyq-n2u6vk9a`, frame 15000 bytes, full SHA-256
  `91b0d1fafb0ace6ecd72070ec9872d259e8acec0fa901175bfa7f658a0b40f2f`,
  preview PNG 1686 bytes; device GET 200 -> DEVICE_FRAME_ACCEPTED ->
  DEVICE_REFRESH_FLOW_COMPLETE for the same frame. Preview `X-Frame-Version` equalled the
  published ETag and the device-reported frame version. One existing standard FULL display
  path was exercised; this is software-report evidence, not an independent physical pixel
  re-confirmation in R4.

## Limits

- State remains process-local and in-memory; no publication history or persistence.
- Device fields are device software reports, not physical confirmation.
- Browser polling stays at 2 s after preview/publish and does not stop automatically; there is
  no automatic retry/reset.
- R5 mobile entry/PWA, R6 LAN OTA and R7 remote control = NOT STARTED.
- NEXT_REQUIRED_STAGE = R5 mobile entry/PWA under separate authorization.

---

# 36. Round 2 R5 — Android Mobile Entry / Conditional PWA

Date: 2026-11-07 (Asia/Shanghai). Base commit `291ccab` (R4 local management).
Worktree `C:/Users/cslki/.codex/worktrees/a5b3/eink-panel`, detached HEAD; local commit only,
no push/tag.

## Scope and platform boundary

- Target is Android Chrome only. No iOS install path is implemented or claimed.
- PWA is conditional on a secure context. Over plain LAN HTTP (`http://<lan-ip>:8000`)
  browsers do not enable Service Worker or full installation; the page says so instead of
  faking installability. Full install/offline applies only on localhost or HTTPS.
- R5 adds no HTTPS/certificate handling, no push, no frontend framework, no Python
  dependency, and no API, frame, device, firmware or publication contract change.

## Delivered

- `GET /manifest.webmanifest` (application/manifest+json, no-cache) and `GET /sw.js`
  (root scope, application/javascript, no-cache). `/manage` now sends `Cache-Control:
  no-cache`; existing routes are unchanged.
- `web/manifest.webmanifest`: id/start_url `/manage`, scope `/`, standalone, black/white
  theme, 192 and 512 PNG icons generated for this panel.
- `web/sw.js` (cache `eink-shell-v2`): precaches only `/manage`, `/static/offline.html`,
  the management CSS/JS modules and icons; install uses `cache: "reload"`. Runtime is
  network-first with no-cache revalidation. Only same-origin GETs under `/manage`,
  `/static/offline.html` or `/static/*` are cacheable; `/api/*`, `/sw.js`, the manifest,
  the simulator root and cross-origin requests are never cached. Cache keys are canonical
  URLs (query removed) so navigations cannot accumulate duplicate entries. Cache writes
  are best-effort: quota/denial cannot hide a live response or force a stale one. Offline
  navigation falls back to the cached `/manage`, then `/static/offline.html`; assets fall
  back to their cached copy. Missing cache entries return a network error.
- `web/pwa_logic.mjs`: pure registration/install predicates and honest hint text.
  `web/manage.js` registers `/sw.js` only when `serviceWorker` exists and
  `window.isSecureContext` is true; captures Android `beforeinstallprompt`, offers an
  install button when available, and handles expired prompts. Registration failure is
  shown once and does not block online management. No prompt is shown in standalone mode.
- Mobile layout: single-column management cards at 820 px; 16 px form fields (including
  coarse-pointer landscape phones), 44 px primary controls, sticky actions with separator,
  top/left/right/bottom safe-area insets, no horizontal overflow at 320 px.
- Offline page states that it is only the shell and that no cached device state is shown;
  it still shows UNKNOWN after the status request fails.

## Tests and review

- Python: 408 passed, including manifest metadata, icon dimensions, SW root/MIME/no-cache,
  shell-asset closure (every `SHELL_ASSETS` entry returns 200), `/manage` no-cache,
  PWA metadata markers and offline-page honesty.
- Node: 29 passed. Covers SW registration/install predicates, hint text, cache allowlist,
  canonical cache keys, best-effort cache writes, live response preservation, offline
  navigation fallback and offline asset fallback/error.
- Independent review: no Critical. Five Important issues fixed: cache-write failures no
  longer replace/hide live responses; `/manage` is revalidated and shell fetches bypass
  stale HTTP cache; coarse-pointer landscape no longer zooms; top/left/right safe areas are
  applied; install/offline behavior now has real tests (shell closure, fallback, cache
  failure) instead of source-text markers. Selected minors fixed: offline fallback covers
  navigations to `/`, cache name bumped for keying change, prompt errors handled, listeners
  registered before `beforeinstallprompt` can fire, display-mode changes re-render the card,
  registration failure is sticky, sticky actions have a separator, offline page has theme
  color.

## Browser evidence

- Real Chromium at `http://127.0.0.1:9000/manage` (secure localhost context; separate Host
  from the device-facing process): manifest linked, SW scope `/`, active and controlling.
  Cache `eink-shell-v2` contained exactly the shell entries and one `/manage`, with no
  `/api/` entries; the previous `eink-shell-v1` was removed.
- Mobile iframe checks at 390x844 and 320x700: no horizontal overflow, one-column grid,
  16 px inputs, 44 px buttons, sticky actions.
- Stopping the Host and reloading: cached shell loaded, status became
  `状态未知（读取失败）`, PUBLISH ID / HOST STAGE / SOURCE = UNKNOWN, and the only console
  errors were the expected failed API status requests.
- No frame was published in R5; no device, NVS, display or physical state was touched.

## Limits

- Real Android phone installation and offline launch = NOT RUN. Verification used desktop
  Chromium with mobile viewport and localhost; device-level PWA behavior remains unverified.
- Over LAN HTTP, install/offline remain unavailable by browser policy. This is displayed
  honestly, not worked around.
- A maskable icon variant is not provided; Android home-screen masking may letterbox the
  square icon. Manual cache-version bump is required when shell assets change.
- R6 LAN OTA and R7 remote control = NOT STARTED.
- NEXT_REQUIRED_STAGE = R6 LAN OTA under separate authorization.

---

# 37. Round 2 R6 — LAN OTA

Date: 2026-11-07 (Asia/Shanghai); real-device acceptance 2026-11-08. Spec commit `20c6a26`;
delivered `a451593`..`7c9b342`, merged to `main` via PR #1 (`3355ce9`). The delivery itself
made no upload, reset or NVS change; the Task 10 acceptance below then USB-flashed the
baseline and ran one OTA under separate confirmations.

## Scope and boundary

- LAN-only OTA: one Host-configured image, explicit arm/disarm, one-shot manifest and image
  download, device size/version/SHA-256/image validation, next-slot boot set, reboot, 120 s
  Wi-Fi self-test with bootloader rollback, a credential-free OTA build profile, and one
  firmware card on `/manage`.
- Not implemented: HTTPS/TLS, authentication, pairing, signed images or secure boot, delta or
  compressed OTA, upload from the browser, automatic or scheduled updates, OTA progress on the
  e-ink display, rollback button, multiple devices or cloud. No partition-table change, no
  full-chip or NVS erase, no credential rotation, no display change and no frame-contract change.
- Trusted-LAN model: anyone on the LAN can arm/disarm or fetch the armed image and cause one
  reboot into the operator's configured credential-free image. This is a documented limit, not
  a security claim.

## Partition and NVS facts

- The built table, identical in both OTA envs (`partitions.bin` SHA-256 `148b959c…`), is the
  board's default OTA-capable layout: `nvs 20K @0x9000`, `otadata 8K @0xe000`,
  `app0 ota_0 1280K @0x10000`, `app1 ota_1 1280K @0x150000`, `spiffs 1408K @0x290000`,
  `coredump 64K @0x3f0000`.
- No migration and no partition override: `platformio.ini` is unchanged, the NVS offset stays
  at 0x9000, and R6 neither rewrites nor erases the persisted R3C credentials.

## Host

- Local configuration `config/firmware.json` is gitignored; the committed example documents
  `path` and `version`. The version must match `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`, the file
  must be 1..1,200,000 bytes, and its bytes are read and SHA-256-hashed once at Host start, so
  later on-disk changes cannot race the status, manifest and image responses. A missing or
  invalid config disables OTA without affecting frame, management, PWA or status routes. The
  path never appears in logs, API bodies or HTML.
- Five endpoints, all `Cache-Control: no-store`: `GET /api/device/firmware/status` (200 always;
  configured, armed, version, size, sha256, expires_at, served_at, device_version),
  `GET .../manifest`, `GET .../image`, `POST .../arm` and `POST .../disarm` (arm/disarm return
  the status body; arm is 503 when unconfigured).
- Manifest bodies are exact and key-ordered, with no extra fields and `Connection: close`:
  configured and unarmed/expired `{"armed":false}`; armed
  `{"armed":true,"version":"<version>","size":<decimal>,"sha256":"<64 lowercase hex>"}`;
  unconfigured 503 `{"detail":"Firmware offer unavailable"}`.
- Image: 503 unconfigured, 409 when not armed or the arm has expired, otherwise the exact bytes
  with `application/octet-stream`, `Content-Length`, `X-Firmware-Version`,
  `X-Firmware-SHA256` and `Connection: close`; no ETag, 304, transfer or content encoding.
- Arm is one-shot with a 600 s expiry. `take_image()` disarms at request start, so consumption
  happens even if the client disconnects mid-body; an accepted device report carrying the target
  version auto-disarms. A rejected report never reaches the offer, so a stale frame cannot
  auto-disarm, although `last_seen` is still updated.
- The `/manage` card shows the configured state, target version, size in KiB, SHA-256 prefix,
  device version and arm/expiry/served state; arming requires a native confirm that names the
  target and the reboot. The card never exposes the path and never publishes a frame; a failed
  firmware status poll shows UNKNOWN without blocking frame management.

## Device

- `State::FirmwareCheck = 18` and `State::FirmwareUpdate = 19` are appended, as is
  `Failure::FirmwareUpdateFailure`; values 0..17 are unchanged. The flow becomes
  `HostResolve -> FirmwareCheck -> (HttpConnect | FirmwareUpdate)`.
- The `Port` gains five firmware entry points — `beginFirmwareCheck`, `pollFirmwareCheck`,
  `beginFirmwareUpdate`, `pollFirmwareUpdate`, `rebootForFirmware` — plus a
  `firmwareVersion()` accessor with a non-pure default. `OtaUpdater` is a member of the
  file-scope port global (about 6.5 KB), never a stack local.
- A manifest failure, 503, malformed body or version match silently proceeds to the frame poll
  without changing failure state. The manifest parser is bounded to 512 bytes and accepts only
  the two documented bodies; the image header parser requires status 200, the exact
  `application/octet-stream`, `Content-Length`, matching version/SHA headers, `no-store` and
  `Connection: close`, and rejects transfer/content encoding.
- The body is streamed in chunks of at most 4096 bytes from one static 4 KiB buffer, never the
  15000-byte frame buffer, into the next OTA partition, with incremental mbedTLS SHA-256. On EOF
  it closes the socket, calls `esp_ota_end`, compares the SHA, then sets the boot partition,
  prints `NETWORK_OTA_READY version=<version>` and reboots. Budgets are 3 s connect, 5 s
  headers, 10 s body idle and 120 s total.
- Any failure aborts the OTA handle, closes the socket, keeps the running firmware and enters
  `FailureWait` with `FirmwareUpdateFailure`; it calls no display function. A per-boot
  `firmwareAttempted_` latch (never reset, including across a provisioning restart) allows at
  most one update attempt per boot, so there is no automatic retry; an attempt that fails before
  the image GET leaves the Host arm to expire or to be disarmed by the operator.
- `maintainFirmwareValidity()` runs every loop, acts only while the running slot is
  `ESP_OTA_IMG_PENDING_VERIFY`, accumulates continuous `WL_CONNECTED` time (reset on disconnect)
  and, after 120 s, calls `esp_ota_mark_app_valid_cancel_rollback()` once and logs
  `NETWORK_OTA_VALIDATED`. It never resets or reboots the device.

## Rollback facts

- The compiled sdkconfig sets `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y` and
  `CONFIG_APP_ROLLBACK_ENABLE=y`, and `verifyRollbackLater()` (returning true) links as the
  strong definition, so a freshly booted OTA image stays pending-verify. The 120 s mark-valid
  call is mandatory, not optional: without it the next reset rolls back to the previous valid
  slot.
- The initial USB-flashed baseline is not pending-verify and is not subject to rollback. A
  firmware that boots but misses the Wi-Fi criterion is reverted only by the next manual reset;
  no automatic reset or retry is added.

## Builds

- `esp32-m1-network-progress-ota` extends the network progress env with `-DEINK_OTA_BUILD=1`;
  `esp32-m1-network-progress-ota-r6-2` adds `-DEINK_FIRMWARE_VERSION=\"round2-r6-2\"`. The
  baseline reports `round2-r6-1`; the target image is identical code with only the token changed.
- Under `EINK_OTA_BUILD` the private network header is not included: SSID placeholder
  `eink-ota-placeholder`, empty password, TEST-NET-1 fallback host `192.0.2.1` and port 8000.
  Runtime credentials come from NVS; provisioning stays available when none are persisted. The
  credential-free image therefore has no usable compiled Host: the real one must come from the
  already-recorded per-poll mDNS `_eink-panel._tcp` discovery (§34), and because `validConfig()`
  accepts the placeholder, a discovery failure appears only as repeated TCP-connect failures
  with no further explanation.
- Post-fix build at the final code commit (`7c9b342`): both envs SUCCESS, `firmware.bin`
  876064 B each, Flash 66.3% (869493/1310720), RAM 21.7% (71256/327680). Baseline SHA-256
  `5100ab0613260080cbdcc64102085904090f8097540d818c612e5d6911139f67`, target
  `60cd29502a33e845b179ba69eea2eb9f5d92d011ca922d5415805ce767ef5cab`, measured from the
  post-fix build artifacts (no source or config file is newer than the binaries). The earlier
  verification build at `aa46c0b` produced 876192 B images (`652d9260…` / `3d38f9c9…`); the
  final fix changed the binary, so those hashes describe that build only.
- Credential scan over both envs' `firmware.bin`, `firmware.elf`, `partitions.bin` and
  `bootloader.bin` (UTF-8 and UTF-16-LE) = PASS, 0 hits; only the documented placeholder string
  appears. Partition table unchanged.
- The OTA env still needs the gitignored pin-only `display_config.local.h` to build. It is a
  build prerequisite, never committed; a clean checkout cannot build the OTA image until it is
  provisioned.

## Tests and review

- Python: 427 passed (re-run at HEAD; no test or build log was stored for that re-run). Node:
  36/36 passed. C++: 7/7 harness translation units pass xtensa `-fsyntax-only`, and both OTA
  envs build SUCCESS.
- `CXX_RUNTIME = NOT RUN`: no host C++ compiler exists on this machine and the xtensa toolchain
  cannot execute host binaries. The C++ assertions (state numbers, per-boot latch, sink version,
  120 s validity hold) were never executed; compile checks and build success are not runtime
  evidence.
- Per-task reviews plus one final whole-branch review found no Critical. Important findings
  fixed: a rejected manifest/header line still allowed the parser to complete (poisoning,
  `96e967e`); transfer drive loops capped below a real response (100→1024, `5da8884`); the card
  kept a post-update `served` state instead of `current`, and the service-worker shell omitted
  the new module (closure test, cache v3, `aa46c0b`); then the pre-GET retry hole, the missing
  `NETWORK_OTA_READY` marker, vacuous path-leak assertions and an unasserted image `Connection`
  header (`7c9b342`). The fifth Important finding (no executed C++ runtime) was record-only: it
  is dispositioned as `CXX_RUNTIME = NOT RUN` above, not fixed.
- Deferred minors, briefly: untested disarm/relative-path/expiry edges; status fields when
  unconfigured; parser tolerance for case/unknown headers; no observation of OTA socket sharing;
  Pending halves untested; Windows-only path positive controls; stale `armed`/`armedUntil` UI
  rendering; duplicate startup status GET; orphan `FIN_WAIT_2` sockets; a 33-byte stub image in
  the UI check.

## Rulings

- (a) Design A7 ("R4/R5 behavior unchanged") is narrowed: a communication-only device report
  (`refresh_stage=null`) now also requires the frame the Host actually serves; previously an
  unknown or stale identity was accepted. The isolated, tested change is `4615b09`; R4/R5
  behavior is otherwise unchanged.
- (b) An update failure follows the spec's `FailureWait` with `FirmwareUpdateFailure`; the
  earlier terminal-`FaultStop` fix (`77e6249`) was withdrawn because it would stop frame polling
  after a transient OTA failure. "No automatic retry" is enforced by the per-boot latch
  (`7c9b342`), with the Host's one-shot image GET as the second guard.
- (c) The plan's stale `firmwareUpdates == 2` Task 6 snippet (also `activate()` without a version
  and `OtaSink::reboot()`) was corrected in `7c9b342`; the implementation matches the spec.
- (d) The Host restart before arming lost the process-local frame. The already-recorded R4 event
  was re-ingested to restore the identical frame before arming (same ETag `91b0d1fa…`), and no
  frame was published inside the OTA window; the device answered 304 pre-OTA. This restores the
  pre-OTA baseline rather than introducing a new frame.

## Browser evidence

- A temporary loopback-only Host with no LAN advertisement served a 33-byte stub as
  `round2-r6-2`; no device-facing Host and no device were contacted. Six checks PASS: card
  values, confirm text and dismiss path, arm (native confirm, 200, no image fetch), disarm,
  preview/publish unaffected with zero publishes, and a failed firmware status request showing
  UNKNOWN without blocking the page.
- The click tool did not deliver pointer events, so button clicks were dispatched as DOM
  `element.click()` calls inside the page while the real native `confirm` dialog was accepted
  through the tool; the confirm text was captured separately. The temporary config was removed
  and the Host stopped.

## Real-device acceptance (2026-11-08)

- Preconditions: the `round2-r6-1` baseline was USB-flashed to app0 only (876064 B, SHA-256
  `5100ab06…`, no NVS/full-chip erase); the Host offered `round2-r6-2` (876064 B, SHA-256
  `60cd2950…`) from the gitignored `config/firmware.json`. Because the project venv interpreter
  is not covered by the Windows inbound allow rule, the Host ran under the allowed runtime
  interpreter with an isolated `--target` dependency directory
  (`D:/Codex/eink-panel/.venv-hw/pyhost-deps`, fastapi/uvicorn/pydantic/httpx/zeroconf); no
  firewall, system or source change.
- Pre-OTA: device `10.111.16.216`, `device_version=round2-r6-1`; frame GET 304 against the
  existing R4 frame (`91b0d1fa…`), so no display call. After the Host restart lost the
  in-memory frame, the same R4 event (`web-mw69zcyq-n2u6vk9a`, source `r4-web-20261107`) was
  re-ingested before arming; the served frame was byte-identical (SHA-256 `91b0d1fa…`) and no
  frame was published during the OTA window.
- Arm from `/manage`: the card showed target `round2-r6-2`, `856 KiB`, SHA-256 `60cd2950…`,
  device `round2-r6-1`, state `可以准备升级`; `POST /api/device/firmware/arm` 200 at
  `16:40:29Z`, expiry `16:50:29Z`.
- Next poll: manifest 200, image 200 at `16:41:11Z` (`served_at`), arm consumed and disarmed.
  Serial: `State 18 -> 19 -> NETWORK_OTA_READY version=round2-r6-2` -> `SW_CPU_RESET` reboot.
- After reboot: `State 18 -> frame GET 200` -> one normal FULL refresh (`2183 ms`) -> about
  120 s of continuous Wi-Fi -> `NETWORK_OTA_VALIDATED`; later polls were 304. The Host
  received the `round2-r6-2` device report; `/api/panels/progress/status` shows
  `DEVICE_REFRESH_FLOW_COMPLETE` with the unchanged frame. `/manage` then showed target and
  device `round2-r6-2`, state `设备已是目标版本`, both buttons disabled.
- Manual power cycle: under separate confirmation the USB/power was removed at `16:48:16Z`
  (COM12 read failed with `PermissionError`, confirming re-enumeration); the device rebooted
  and reported `round2-r6-2` again at `16:49:32Z`. No rollback to `round2-r6-1`.
- Regressions: NVS credentials survived both cold starts with no reprovisioning; the frame path
  is unchanged (200/304 cycles); no `POST /api/events` occurred during the OTA window; states
  18/19 made no display call (the only FULL refresh is the normal post-reboot frame fetch).
  Occasional `FAILURE=5` (`TcpConnectFailure`) cycles were observed and recovered on the next
  poll, identically to the pre-OTA behavior.
- NOT RUN: physical failure injection or rollback (no bad image, no mid-transfer disconnect),
  and the Android-device check. Serial capture evidence: `serial-ota.log`,
  `serial-powercycle.log`, `host.log`, `status-after-ota.json`,
  `status-after-powercycle.json`, `progress-status-after-powercycle.json` under
  `D:/Codex/round2-r6-ota-20261107/acceptance/`; the serial log heads are garbled by CH340
  boot noise but the `NETWORK_STATE`/`NETWORK_OTA` lines are intact.
- Note: opening COM12 pulses EN. One `POWERON_RESET` boot on r6-1 at capture start
  (`16:39:20Z`) and one after validation (`16:47:55Z`) were observed; neither was separately
  authorized, and neither changed the OTA result (the first preceded arming; the second
  preceded the manual power cycle). Future serial captures must account for this.
- Cleanup (2026-11-08): the acceptance Host was stopped (port 8000 closed), the gitignored
  `config/firmware.json` was removed, and the isolated `pyhost-deps` directory under
  `.venv-hw/` was deleted; the evidence directory was kept. The device remains on
  `round2-r6-2`, and with no Host listening later polls cannot connect (expected `FAILURE=5`).
  No tracked file was affected by the cleanup.

## Host multi-page milestone (2026-11-08)

- Scope: the original Host-rendered route gained a page registry and current-page selection
  (`progress`, `memo`, `course`), an atomic file-backed page store under gitignored
  `data/pages/`, a `PageFrameService` facade, Memo and Course panels, additive `/api/pages/*`
  endpoints, `/manage` switching plus Memo/Course editors, and PWA shell `eink-shell-v4`.
- Compatibility: the device still calls the unchanged `GET /api/panels/progress/frame` and
  `POST /api/panels/progress/device-report`; each response remains 15000 bytes with format
  `epd-t-400x300-mono1-msb-v1`. `/api/panels/progress/status` still returns exactly the
  Progress keys; page-aware facts live only on `/api/pages/status`. Progress still delegates
  to `ProgressFramePublisher`; Memo/Course use the same strict render audit, PNG conversion,
  row-reversal transport adapter and device report ledger.
- Determinism: a frame depends on the stored revision, `day_key` and page data. Memo due
  status is day-level (`OVERDUE`/`TODAY`/`LATER`) and prints no clock minute; Course renders
  the selected day's courses, semester week and per-date overrides. Saving a page or crossing
  midnight produces a new frame; repeated reads of the same revision/day return the same
  ETag/bytes.
- API contracts: `GET /api/pages`, `GET /api/pages/status`, `GET/PUT /api/pages/{memo|course}`,
  `POST /api/pages/{page_id}/select`, `POST /api/pages/{page_id}/preview`. Stale revisions
  return 409 with the current document; invalid or unrenderable data returns 422 and writes
  nothing. Preview uses the same render pipeline and reports `X-Frame-Version/-Format/-Bytes`.
- Software verification: full Python suite 509 passed (baseline before this milestone: 427);
  frontend Node suite 47 passed (baseline: 36). Coverage includes atomic writes, revision
  conflicts, corruption fallback, path rejection, deterministic day rendering, page caching,
  legacy status keys, 409/422 behavior, preview/device hash equality and shell precaching.
- Review closure: each (weekday, week) is capped at eight effective courses at write time, so
  alternating-week schedules remain valid while an overflow day cannot be saved; a full
  eight-row day is strict-rendered above the footer. Loaded override course ids are preserved
  instead of being cleared by option rebuild; switching pages clears acceptance/refresh facts
  while keeping contact facts; save reports are recomputed from a refreshed page status and
  never claim acceptance for an unsaved revision; delete-course removes its overrides; an
  in-flight status poll cannot overwrite a newer page selection.
- Browser evidence (loopback Host `127.0.0.1:8010`, no physical device): switched to Memo,
  saved two items, and previewed revision 2; the device endpoint then returned 15000 bytes,
  SHA-256 `7a273c59533cd74bdc691040c7f28e3f016598a03cc32397dd4909b00fd0aedf`, identical to
  the preview version. Switched to Course, saved two courses plus a cancel override, and
  previewed revision 2; the device endpoint returned SHA-256
  `991844568244b90116bf7d25115b7462ac57140d9462660b297f21607c3f1a8a`, also identical.
  `/api/pages/status` advanced to `Host 已提供当前帧`; no browser console errors appeared.
- Commit chain: `78c43fb` page state, `45d12cb` Memo, `34e4416` Course, `dd51117` shared
  render/ledger, `0717d6b` page service, `f428a8d` page APIs, `970f335` web switcher/Memo/PWA
  v4, `d0db5f6` Course editor.
- NOT RUN: multipage acceptance on the physical panel. No firmware, NVS, partition, OTA or
  display call was performed for this milestone; `hardware/` is unchanged. The loopback Host
  was stopped and the generated `data/pages/` test documents were removed.
- Limits: the worst-case switch/save-to-screen delay remains one 60 s poll plus one FULL
  refresh (~2.2 s); the Host must be online; there is no partial refresh, animation, offline
  multi-page cache, native APK or cloud control. Selection survives Host restart, while the
  served-frame cache and device report ledger are process-local.

## Host multi-page physical acceptance (2026-11-08)

- Result: PASS for the recorded single-device scope (CODEX-ONLY evidence). The real ESP32
  (`10.21.98.216`, MAC `1C-C3-AB-1F-5F-D0`, firmware `round2-r6-2`) displayed Progress, Memo
  and Course through the unchanged `GET /api/panels/progress/frame` and reported through the
  unchanged `POST /api/panels/progress/device-report`. This supersedes the earlier "NOT RUN:
  multipage acceptance on the physical panel" entry for the scope below only.
- Frames: Progress `5f8b1f6e…`, Memo `7d86748d…` (revision 2), Course `ef4f312c…` (revision 2),
  each 15000 bytes with format `epd-t-400x300-mono1-msb-v1`. Memo and Course preview hashes
  were identical to the served device frames. Every page switch produced exactly one device
  `200`; all later polls returned `304` (device `200` = 4, `304` = 13 for the run).
- Latency: select-to-first-GET was 21.7 s for Memo, 28.1 s for Course and 30.1 s for the
  restore to Progress. These are single observations, not a guaranteed bound; the design limit
  remains one 60 s poll plus one FULL refresh (~2.2 s).
- Device reports matched the served ETag and reached `DEVICE_REFRESH_FLOW_COMPLETE`; an
  all-zero ETag report returned `409` without changing the accepted identity. The legacy
  `/api/panels/progress/status` keys were preserved; page-aware facts stayed on
  `/api/pages/status`. `GET /api/device/firmware/manifest` returned 503 (no image configured);
  no OTA was attempted.
- Discovery caveat: the product Host announces `_eink-panel._tcp` once at startup; on this AP
  the device's first mDNS query was not observed for about eight poll cycles even though the
  same-PC browse resolved the advertisement and the device answered ICMP. An acceptance-only
  launcher that repeated the same announcement every 5 s restored discovery within 66 s.
  Product code was not changed in that run; the Host now repeats the announcement itself (see
  the discovery reliability fix below).
- Safety: no serial open, reset, power cycle, firmware build/upload/OTA, NVS or partition
  operation; `hardware/` stayed clean; no credentials were logged. Evidence root:
  `D:/Codex/round2-multipage-20261108/acceptance/` (Host log, frames, preview PNGs, status
  snapshots, `ACCEPTANCE-2026-11-08.md`).
- Operator confirmation: Progress, Memo and Course were each confirmed visually with a single
  full refresh. NOT RUN: instrumented physical refresh counting, serial refresh timing, fault
  injection, a second device or another AP.
- Run notes: the Host ran from this `main` worktree at `48f8056`; dependencies were copied
  offline from the project `.venv` because PyPI was unreachable; the Progress event was
  re-posted after a Host restart because the event store is process-local.

## Host discovery reliability fix (2026-11-08)

- Problem: the acceptance run showed that a startup-only DNS-SD announcement leaves the device
  blind on this AP when its mDNS query is dropped; the device made no request for about eight
  poll cycles until an acceptance-only launcher repeated the announcement.
- Fix (`f11705c`): `HostAdvertisement` starts a daemon thread (`eink-mdns-announce`) that
  repeats `update_service(info)` every `ANNOUNCE_INTERVAL_SECONDS = 1.0` s. The device listens
  about one second per poll, so a longer interval can miss the whole window. A failed
  announcement logs one warning and the loop continues; `close()` sets the stop event, joins
  the thread (`max(2 s, 2 × interval)`) and then unregisters and closes the engine in the
  existing order. `announce_interval` must be a positive finite number.
- Verification: discovery suite 20 passed (4 new tests: repetition, failure tolerance, close
  ordering, interval validation); full Python suite 516 passed; frontend 47 passed.
- Physical re-verification without the launcher: Host started normally on `10.21.98.75:8000`,
  Memo selected at `04:04:21Z`, first device GET at `04:05:06Z` (45.5 s), `200` with 15000
  bytes and ETag `7d86748d…` (identical to the accepted acceptance frame), device reached
  `DEVICE_REFRESH_FLOW_COMPLETE`, and the next poll returned `304`. Selection was restored to
  `progress` and the Host stopped.
- Endpoint change: restarted on `10.21.98.75:8001`; the browse record carried port 8001 and the
  device re-resolved and polled within 27.0 s (`304`, no refresh, report 200). The device does
  not pin the previous endpoint. A literal IPv4 change (secondary alias or DHCP change) was not
  exercised; the address travels in the same record that was verified.
- Safety: no firmware, OTA, serial, reset or partition operation; `hardware/` clean; local
  commit only, nothing pushed. Rollback is `git revert f11705c`.
- Limits: the reason the AP drops the device's query remains unknown (capture not authorized);
  a second device or another AP was not tested. Interval tuning below the 1 s guarantee
  requires re-verification.

## Physical refresh counting and hotspot provisioning (2026-11-08)

- Firmware `round2-r6-3` (commit `9636407`) increments a device-side counter only after an
  accepted frame completes one FULL refresh. The value is stored in NVS (`eink-stats` /
  `full_refresh`), printed as `NETWORK_FULL_REFRESH_TOTAL`, and reported as `refresh_count`.
  The Host records it in `/api/pages/status` (`device.refresh_count`) and `/manage`
  (`PHYSICAL REFRESH`); 304s, failed refreshes and rejected frames do not increment it.
- Software: Python 518 passed, frontend 47 passed, including new coverage for report
  validation, ledger recording (communication reports included), null defaults in both status
  shapes and the management field.
- Physical (hotspot `EINK-TEST`, device `10.21.98.216`): boot printed the persisted total 4
  after the reset; the first course fetch moved it to 5; memo selected at `13:54:43 +08` was
  fetched at `13:55:34` (52 s, 200, 15000 B, ETag `7d86748d…`) and completed at 6; restoring
  progress fetched a new frame and completed at 7. Every following poll was `304` and the
  counter stayed unchanged. This is the first instrumented physical refresh count; the
  earlier multipage acceptance recorded only one refresh per switch by observation.
- Provisioning: renaming the hotspot invalidated the stored SSID; serial showed a repeated
  `FAILURE=3` (`WifiAssociationFailure`) every 60 s and only `EINK-TEST` was on air. Holding
  S1/KEY1 about 2 s opened `eink-panel-setup`, `POST /configure` returned `202 Accepted`, the
  device joined `EINK-TEST` with DHCP `10.21.98.216`, and the Host saw it within one poll
  (37–52 s select-to-fetch). The portal saves credentials only after a successful candidate
  connection, so an SSID rename always requires re-provisioning. The hotspot key was read from
  the operator's saved Windows profile and used in memory only; it was never printed, written
  to disk, logged or committed.
- Safety: no OTA, NVS erase or partition change; serial opened only for the approved counting
  capture; `hardware/` clean. Evidence root: `D:/Codex/round2-multipage-20261108/acceptance/`
  (`REFRESH-COUNT-2026-11-08.md`, `serial-hotspot.log`, `host-hotspot.log`,
  `memo-switch-hotspot.txt`, `progress-restore-hotspot.txt`, `reprovision.ps1`).
- Limits: the counter is a device fact with no Host-side history; BUSY injection B1–B11 still
  blocked; one device and one AP; page content was not re-confirmed visually on this run.

## Weather page (2026-11-08)

> Superseded by “Weather page four-city upgrade (P8, 2026-11-08)” below; the rest of this
> section records the original single-city delivery.

- New page `weather` (file, read-only) rendered by `panels/weather.py`: current temperature
  and WMO label, 8 hourly columns, 3 daily rows, source/updated footer with a STALE marker.
  Deterministic; an empty document renders “等待天气数据”.
- `services/weather_source.py` fetches Open-Meteo over HTTPS (Changsha, 28.2282/112.9388,
  system CA, hourly 8 from the current hour, daily 3) and writes the cached page document.
  Failures keep the last good document; after 90 minutes it is marked stale once
  (revision +1), and recovery clears it. The real HTTP client uses `trust_env=False` because
  the operator machine has a malformed `NO_PROXY` that breaks httpx environment parsing;
  the first failed attempt is kept in `weather-proxy-error.log`.
- `services/weather_scheduler.py` refreshes at startup and at the top of each hour
  (+5 s, minimum 60 s) on a daemon thread; a failure logs a warning and keeps the thread
  alive. Tests set `EINK_WEATHER=0` and never fetch.
- API: read-only weather document (`PUT` returns 400 `Page is read-only`), preview from the
  cached document, and `POST /api/pages/weather/refresh`. `/manage` gained a weather card
  (status, 立即刷新, 生成预览) with frontend tests for `weatherSummary`.
- Tests: Python 552 passed, frontend 48 passed (34 new Python tests).
- Physical (EINK-TEST, device `10.21.98.216`): real data at 14:33 (15°C 毛毛雨; days
  14~16 / 8~14 / 6~14). Selection at 14:33:58 was fetched at 14:34:58 (60 s) with frame
  `96723128…` and 15000 B; the next poll returned 304 and `refresh_count` moved 7 → 8 exactly
  once. Manual refresh produced `bbfdfff7…` and `refresh_count: 9`; the following poll was
  304. The preview SHA matched the device accepted frame.
- Limits: the physical stale state was not staged (software-only LKG test); the top-of-hour
  refresh was not observed live; the page is Changsha-only and read-only. The operator
  confirmed the physical weather screen (“确认屏幕显示正常”) on 2026-11-08.

## Calendar page (2026-11-08)

- New read-only page `calendar` rendered by `panels/calendar.py` for the month that contains
  the device day key: weekday header, finite month grid, day numbers with a small label,
  today filled black with a large white number, and a `今日 {date} 周X 农历…` line with a
  festival or solar-term suffix. The page stores no data; a fresh Host serves it immediately.
  The two footer lines are 10 px bold black (`来源 / 日历 r1`, `更新 / 按当天日期渲染`)
  because the shared 8 px gray footer was not clear on the physical panel.
- `panels/almanac.py` computes lunar dates, leap months, the 24 solar terms and festival
  labels from a dependency-free truncated Meeus series (new moons, solar longitude, ΔT 69 s,
  UTC+8). Leap months are numbered by the first month without a major solar term; the month
  that spans the December solstice now keeps its full length so December dates resolve.
- `/manage` gained a calendar card (生成预览) and preview panel; the preview reports whether
  its frame version equals the served frame (`calendarPreviewMatch`).
- Tests: Python 575 passed, frontend 49 passed (23 new Python tests: almanac fixtures for
  CNY 2024–2028, leap 2/2023, leap 6/2025, 中秋/除夕/端午, 2026 solar terms, panel geometry
  and determinism, API read-only/preview/frame, plus page-list updates).
- Physical (EINK-TEST, device `10.21.98.216`): selected at 14:50:47; the device fetched the
  frame at 35.1 s (`200`, 15000 B, frame `d466d24e…`), accepted it, `refresh_count` moved
  9 → 10 exactly once, and the next poll returned `304`. After the footer refinement the
  restarted Host served frame `6be515ec…` at 25 s, the counter moved 10 → 11 once, and the
  next poll was 304 again. The preview SHA matched the device accepted frame in both runs.
  The operator confirmed the screen (“确认日历显示正常”) on 2026-11-08.
  Final selection is `calendar`: `progress` needs `EINK_PROGRESS_SOURCE`, which this Host run
  did not have (503), while the calendar always renders. The device answers 304 for the
  unchanged calendar frame. Evidence: `CALENDAR-2026-11-08.md`.
- Limits: no 调休 data; month rollover was not observed live; one device and one AP.

## Codex usage page (2026-11-08)

- New read-only page `codex` rendered by `panels/codex_usage.py`: today/week/all-time tokens,
  quota plan/percent/window/reset/snapshot, a seven-day bar chart with Y-axis ticks
  (peak / half / 0) and grid lines, last activity, and a filled STALE tag.
- `scripts/sync_codex_usage.py` aggregates `token_usage_record.usage.total_tokens` from
  `~/.codex/sessions/**/*.jsonl` by CST day, takes the latest `rate_limits` snapshot, and
  POSTs the result to `/api/pages/codex/usage`. Only aggregate numbers and timestamps are
  read; prompts, responses and paths never enter the payload or the log.
- `services/codex_usage.py` validates the payload, saves revision+1 with `stale=false`, and a
  Host watchdog (every 60 s) marks the document stale once after 15 minutes without a sync;
  the next ingest clears it. `EINK_CODEX=0` disables the watchdog for tests.
- Tests: Python 605 passed, frontend 52 passed (30 new Python tests plus frontend logic).
- Real data: today 0 (Codex unused on 11-08), 7 days 22,646,123, all time 132,173,864 over
  878 responses and 6 sessions; quota `free`, 0%, 30-day window, reset 12-07, snapshot
  11-07 15:10.
- Physical (EINK-TEST, device `10.21.98.216`): sync `r2` at 15:11, device fetched frame
  `77100110…` at 20.0 s (200, 15000 B), `refresh_count` 11 → 12 once, next poll 304. After
  the operator asked for a readable Y axis, frame `b02b70ab…` (`r3`) replaced it (counter
  12 → 14 because the restart frame and the sync frame both changed in the test sequence);
  the following poll was 304. Preview SHA matched the served frame in both runs. Operator
  confirmed the screen (“确认用量页面显示正常”) on 2026-11-08. Evidence: `CODEX-2026-11-08.md`.
- Limits: the sync is manual (no scheduled task); today is zero because Codex was not used;
  the quota snapshot is from the last Codex run, not a live call; one device and one AP.

## Memo / Course page enhancement (2026-11-08)

- Course switched to the fixed five-period model: 1 08:00–09:40, 2 10:00–11:40,
  3 14:00–15:40, 4 16:00–17:40, 5 19:00–20:40. Each course stores weekday, week,
  period and room; duplicate `(weekday, week, period)` slots are rejected at write
  time (422). Overrides are `cancel`, `move_room`, `move_period` and `add`; an added
  class needs name/period/room, is limited to one per date and may not reuse a course
  id. Legacy `start`/`end` documents are rejected, so the stored document was
  rewritten once via `PUT /api/pages/course` (revision 2 → 3: 09:00 → period 1,
  14:00 → period 3) before physical acceptance.
- Memo semantics frozen: `due` is stored to the minute for ordering but the panel
  shows only the day-level `OVERDUE` / `TODAY` / `LATER` status plus `MM-DD`; there
  is no minute countdown, and emoji is unsupported (the missing-glyph audit rejects
  it). `docs/MEMO-COURSE.md` records both pages.
- Rendering: after the first device review the week/count header, date, period times
  and rooms were raised from 10 px to 13 px bold; course names stay 13 px regular and
  the footer 10 px bold. A render-audit test pins those sizes, and six effective rows
  still fit above the footer.
- Tests: Python 607 passed, frontend 52 passed.
- Physical (EINK-TEST, device `10.21.98.216`): course r3 frame `40433e5d…`
  (200 / 15000 B / `epd-t-400x300-mono1-msb-v1`) was accepted and refreshed the panel,
  `refresh_count` 14 → 15, next poll 304; memo re-served `7d86748d…` and refreshed
  15 → 16 without regression; reselecting course refreshed 16 → 17; the header/room
  size fix produced `3700a1ff…` (17 → 18); the date/time size fix produced
  `ce7e2473…` (18 → 19); every later poll was 304. The 15000-byte body always
  hashed to the served ETag and previews used the same renderer.
- Operator review: the first confirmation reported the week/count and room labels as
  unclear, then asked for clearer time labels; after both fixes the reply was
  “现在清楚了”. Evidence: `MEMO-COURSE-2026-11-08.md`.
- Limits: one device and one AP; no live cross-midnight switch (unit-tested only); no
  fault injection; legacy course documents in other environments need one re-save.

## Takeout page (2026-11-08)

- New page `takeout` (file, editable, time-sensitive) rendered by `panels/takeout.py`:
  up to six orders with name, stored status (`waiting` / `delivering` / `arrived`),
  optional expected minute and an 8-character note. The screen shows the four states
  待取 / 配送中 / 已到 / 超时 and sorts late → delivering → waiting → arrived.
- “超时” is derived, not stored: an order that is not arrived and whose `expected_at`
  is earlier than the Host minute renders as late; the exact expected minute is not
  late, an order without an expected time never is. `PageFrameService` injects the
  minute as `now` for time-sensitive pages and includes it in the render key, while
  status readiness ignores it; the ETag still changes only when the bytes change.
- `POST /api/takeout/orders` upserts one order by id. Status can only move forward
  (`waiting → delivering → arrived`; same status allowed), a seventh order or an
  invalid status returns 422, and a concurrent write conflict returns 409. Every
  successful receive increments the revision. `/manage` gained an editor with
  save/preview and a forward-only status select; `docs/TAKEOUT.md` records the rules.
- Tests: Python 645 passed, frontend 55 passed.
- Physical (EINK-TEST, device `10.21.98.216`): the empty state frame `250a886e…`
  (200 / 15000 B) refreshed the panel, `refresh_count` 19 → 20, next poll 304. Three
  orders (r8) produced `1751eee0…`, 20 → 21. With no write at all, crossing the 16:06
  expected minute changed the frame to `672c9595…`, 21 → 22, and the next poll was
  304; the preview returned the same frame version. The operator confirmed the
  three-order screen (“显示正常”). Evidence: `TAKEOUT-2026-11-08.md`.
- Run note: the first order POST used an interactive Python script whose stdin was
  decoded with the local GBK code page, so Chinese names were stored mangled. The
  orders were re-sent from UTF-8 JSON files and httpx (final revision 8) and verified
  character by character; the device only fetched the corrected revision. This was
  an acceptance-script encoding issue, not a page or API defect.
- Limits: one device and one AP; no fault injection, platform integration, push
  notification or cancelled state; the 16-chapter cap is page-driven; midnight
  rollover is unit-tested only.

## Android WebView shell (P6, 2026-11-08)

- New `android-shell/` (manifest, `MainActivity.java`, Gradle-free `build.sh`) builds a minimal
  WebView shell `com.eink.shell` (minSdk 24 / targetSdk 34, `INTERNET`, cleartext LAN allowed).
  One top bar shows the saved Host address with 地址 and 重载 buttons; the address is kept in
  `SharedPreferences` and can be provisioned with
  `am start ... -e url http://host:8000/manage`. JavaScript and DOM Storage are on; file and
  content access are off; no credentials are stored.
- Toolchain lives outside the repository at `D:/Codex/android-toolchain` (JDK 17.0.21+9,
  cmdline-tools 11076708, build-tools 34.0.0, platforms/android-34, platform-tools 37.0.1).
  The APK is 12695 bytes, SHA-256 `822277b7…`, v2/v3 signature verified; it is not committed
  (only source and build script are). Build and install steps: `docs/P6-WEBVIEW-SHELL.md`.
- Phone (OPPO PGEM10, Android 16, serial `645d7e89`): `adb install` failed with ColorOS
  `Failure [-99]`, and `pm install` could not read `/sdcard`. Installed via
  `adb push //data/local/tmp` + `pm install -r`, which opened OPPO's install guide; tapping
  继续安装 installed versionCode 1 at 20:16. This is a vendor USB-install restriction, not an
  APK defect.
- Acceptance: the Host was restarted on `10.21.98.75:8000` after the PC moved back to that
  address (the earlier bind on `10.1.80.106` had become invalid). The phone
  (`10.21.98.170`) loaded `/manage`; `/static/*` and status requests returned 200. Page
  selection from the phone: `POST /api/pages/memo/select` 200, later
  `POST /api/pages/takeout/select` 200. Editing from the phone: added an item, typed
  `P6-phone`, tapped 保存到 Host → `PUT /api/pages/memo` 200 (revision 3) plus an automatic
  preview 200, with the report 「已保存，等待设备下一次轮询（≤60 s）」. The memo content was
  then restored to its previous three items (revision 4) and takeout re-selected
  (`takeout-r8`).
- Tests: Python 645 passed, frontend 55 passed (no Python/frontend code change; the shell is a
  separate artifact).
- NOT RUN: PWA installation on the phone (the HTTP origin reports 「不支持安装」), an e-ink
  fetch during this increment (device `10.21.98.216` was unreachable after the PC network
  change; R7 correction — the same device reappeared at `10.127.70.216` by DHCP on 2026-11-09 and
  polled normally, so this sentence describes only the P6 run), landscape/dark-mode/IME checks
  and a non-ColorOS install.
- Limits: the shell is online-only with no push, offline cache or mDNS discovery; the address
  is plain HTTP on the trusted LAN; the APK lives outside the repository.

## Pet page (P7, 2026-11-08)

- New page `pet` (file, read-only) rendered by `panels/pet.py`: the character is the supplied
  line-art template prepared once into a 174x186 1-bit bitmap (`assets/pet/source.webp` →
  `scripts/prepare_pet_art.py` → `assets/pet/chibi.png`), pasted unchanged at (16, 56). The
  watermark sits outside the crop window. State is shown only by the right column: name,
  `Lv.N`, 饱食/心情/亲密 bars, word pair, today-fed line and last interaction; the footer is
  10 px bold black.
- Document fields: `name` (1-8 chars, default 大肥鱼), `satiety`/`mood` 0-100, `affinity` 0-999,
  `last_fed`, `last_interaction`. Level = `min(99, 1 + affinity // 25)`.
- Daily decay is derived, not scheduled: with `updated_at` as the base day, `decay = 0` on the
  same day else `25 + 15 × (days − 1)`; satiety floors at 0 and mood drops 10 more below 30
  satiety. The frame render key already includes `day_key`, so midnight alone produces a new
  frame.
- `POST /api/pet/interact` (`feed` +30 satiety/+2 affinity and marks today, `pet` +12 mood/+1
  affinity, `play` +20 mood/−10 satiety/+3 affinity; clamps 100/999/0). Each action rebases the
  decay by writing today's effective values, increments the revision, and retries one conflict;
  unknown actions return 422 and a surviving conflict 409. `GET /api/pet/state` exposes the
  effective view; `PUT /api/pages/pet` is 400 `Page is read-only`; preview uses the stored
  document.
- `/manage` gained a pet card (state, 喂食 / 摸摸 / 玩耍, preview) and the pure function
  `petSummary`; the page switcher is registry-driven. `docs/PET.md` records the rules.
- Tests: Python 671 passed, frontend 56 passed.
- Physical (round2-r6-3, `10.21.98.216`): baseline `refresh_count` 26. Selecting the first pet
  prototype (r1) returned 200 / 15000 B / ETag `50e6d34a…`, count 27, next poll 304. Feeding
  from `/manage` produced r2 `931362c7…`, count 28, next poll 304. A line-art redraw produced
  `a613ca49…` (count 30). The final template bitmap produced `1d2e727e…`; the device accepted it,
  count 31, and the next poll was 304. The preview `X-Frame-Version` equalled the served ETag in
  every check and `X-Frame-Bytes` was 15000.
- Live phone UI: with the WebView shell the operator switched Course/Memo/Progress/Weather and
  then the pet page, and triggered three interactions at 20:56 (revision 10, satiety 100,
  mood 100, affinity 16). The device accepted that r10 frame (`576f9039…`) and the count reached
  32. This is live UI evidence, not a scripted API-only check.
- Operator visual confirmation: on 2026-11-08 the operator reported that the final pet bitmap
  is clear on the physical panel (“宠物页位图在真机上清楚”). The frame identity, SHA and count
  evidence above predates that statement and is unchanged.
- NOT RUN: cross-day decay on the physical device (software-only test); no firmware, OTA,
  serial, NVS or partition change was performed.
- Limits: one fixed bitmap and no rename/change UI; no animation or device-side state; the Host
  must be online for a new frame; a bitmap at this size loses fine lines compared with the
  template.

## Weather page four-city upgrade (P8, 2026-11-08)

- `config/weather.json` now holds `cities` (tianjin/guilin/changsha/nanjing with coordinates)
  and `default_city=changsha`; the old single-city keys are gone. `WeatherSource` sends one
  Open-Meteo batch request with comma-joined latitude/longitude, rejects any response whose
  count differs from the configured list, and stores `{current_city, cities{id:{name,
  current_temp, current_label, hourly, daily}}, stale, source}`. The live document is ~2.5 KB.
- `panels/weather.py` validates each city (`hourly` ≤8, `daily` ≤3, temperature −50..60) and
  renders only `current_city`; a document whose `current_city` is missing (but `cities` is not
  empty) is rejected, and an empty `cities` renders 等待天气数据. The page header shows the city
  name and `day_key` at 10 px bold. The render key already includes `day_key`.
- New HTTP surface: `GET /api/pages/weather/cities` (config order + current city) and
  `POST /api/pages/weather/select-city {"city": id}` (unknown 422, conflict 409, selecting the
  current city returns the same revision). Switching only rewrites `current_city` and bumps the
  revision, so the device takes one new frame and then 304. `refresh()` keeps a still-valid
  selection across fetches; `PUT /api/pages/weather` stays 400 read-only.
- `/manage` weather card gained four city buttons (generated from the cities endpoint), summary
  `城市 temp° label · 更新 time`, and wires `weatherCityOptions` (pure function) into the
  existing refresh/preview flow. `web/sw.js` cache bumped to `eink-shell-v5`.
- City list is the extension point: adding a city is a `config/weather.json` edit plus a Host
  restart. Guards: `test_a_fifth_city_needs_config_only` (batch fetch + store),
  `test_a_fifth_city_renders_without_a_panel_change` (renderer) and
  `test_a_fifth_city_only_needs_a_config_edit` (cities endpoint + switch). A document past the
  16 KiB budget now returns `ok: false` / `weather document exceeds the 16 KiB budget` instead
  of raising, leaving the previous document and frame intact (`test_a_city_list_past_the_
  document_budget_is_reported`). Live probe on 2026-11-08: adding 上海 as a fifth city needed
  no code, wrote a 3,080 B five-city document (revisions 32/33) and was then reverted to four
  cities (revision 34); counts and ETags behaved normally.
- Tests: Python 681 passed; frontend 57 passed. `tests/fixtures/open_meteo_four_cities.json` is
  a real batch response (4 entries) and `tests/fixtures/open_meteo_changsha.json` was removed.
- Physical (round2-r6-3, `10.21.98.216`): baseline count 32. Weather r25 (长沙) 200/15000 B,
  ETag `29dfea0e…`, count 33, next 304. guilin r26 `0ba1a911…` → 34, 304; tianjin r27
  `73ba20df…` → 35; nanjing r28 `fdcb8ff5…` → 36; changsha r29 `3cbe8e3a…` → 37, 304 at
  13:19:00Z. The same switch done through the `/manage` buttons (桂林 then 长沙, r31) produced
  `34a14b68…`, count 38, then 304 at 13:22:13Z. Preview `X-Frame-Version` equalled the served
  ETag each time; served bodies were 15,000 bytes in `epd-t-400x300-mono1-msb-v1`.
- Operator completion: on 2026-11-08, after the switching, extension and budget work, the
  operator declared the weather page complete (“天气页完成”). This closes the visual/acceptance
  gate that was previously pending; the frame, SHA and count evidence above is unchanged.
- NOT RUN: physical stale path (upstream failure); no firmware, OTA, serial, NVS or partition
  change.

## Remote access (R7A, 2026-11-09)

- `--remote` adds one `127.0.0.1` listener next to the LAN listener on the same port
  (`services/remote_listen.py`); the default path is unchanged — without the flag the Host
  still binds only `--host` through the plain uvicorn path. Frame contract, 200/304, 60 s
  polling and mDNS are untouched.
- Advertisement still comes from `--host`: `app.state.host_advertisement` is built from the LAN
  address only, and `--remote` refuses a loopback, unspecified, multicast or broadcast host
  (`--remote requires a non-loopback --host` / `--remote requires a unicast LAN IPv4`).
- Windows bind rule: `SO_REUSEADDR` is set only on POSIX (`sys.platform != "win32"`), because on
  Windows it lets a second process claim the same endpoint; the default exclusive bind is kept
  so a taken port fails loudly instead of leaving one listener half-open.
- Tests: Python 697 passed, frontend 57 passed. The final whole-branch review found 0 Critical;
  its single Important item was this recording task.
- Commits: `c4e97d9` spec, `8d9e4cb` plan, `57502bb` plan tweak, `d3074e1` gitignore,
  `5e06a93` listen rule, `962acbc` binder, `e4c973e` Windows bind amendment, `2883dd8`
  Windows bind fix, `96310cf` CLI, `7fda49e` runbook, `a378faa` runbook gaps.

Deployment, 2026-11-09: Tailscale 1.104.5 was installed via winget with explicit operator
approval and logged in as a single host client; MagicDNS and HTTPS certificates were enabled in
the admin console; Serve was configured with
`tailscale serve --bg --https=443 127.0.0.1:8000`. Redacted `tailscale serve status`:

```
https://<host>.<tailnet>.ts.net (tailnet only)
|-- / proxy http://127.0.0.1:8000
```

From the Host, `https://<host>.<tailnet>.ts.net/manage` returned 200 and curl verified the
certificate (`ssl_verify_result 0`); `/api/pages` also returned 200 and loopback `/manage` still
returned 200 (`https-check.txt`, a re-typed summary; those requests were not re-run for that
file). The device reached the same backend over the LAN in A1/A2; the
A3 Serve checks were first issued from the Host over HTTPS. A phone joined the tailnet on
2026-11-09 and completed the phone half of A3; see the R7B section below.

| Item | Result |
| --- | --- |
| A1 — default unchanged | PASS (host + device): the no-flag startup (PID 19540) binds only `10.127.70.75:8000` and loopback is refused; LAN `/manage` 200. The device (`10.127.70.216`, round2-r6-3) fetched weather r41 (ETag `e1d23906850cb7f8b419b01b9868c0bd38fcadcfee08ded18a85e16a436d95d3`, 200) and reported `DEVICE_REFRESH_FLOW_COMPLETE`, refresh count 45 → 46; the next poll was 304 with the count unchanged. OTA manifest 503. The no-flag default path is also covered by `tests/test_remote_cli.py` / `tests/test_host_discovery.py` |
| A2 — dual listen | PASS (host + device): `--remote` (PID 27876) has `10.127.70.75:8000` and `127.0.0.1:8000` both `LISTENING` under the same PID (`netstat.txt`); HTTPS `/manage` and `/api/pages/status` returned 200 through Serve. The device fetched weather r42 (ETag `207e8068282d33ad872f6aee23bdcdac42a1fcedb26747c576f7bb15ca25360f`, 200), count 46 → 47, next poll 304. The r42 revision is a weather content refresh, not caused by `--remote` |
| A3 — remote management (phone, Wi-Fi off) | PASS (phone, with a path caveat): the phone (Wi-Fi off, cellular, Tailscale online) loaded the HTTPS `/manage` through Serve, switched weather → memo → weather, saved a memo edit and generated a draft preview; the device took the frames (count 51 → 53 → 56, weather-r53 ETag `ab42d7ab…`, accepted equal, `DEVICE_REFRESH_FLOW_COMPLETE`). The memo was restored. Details and the earlier Host-initiated Serve run are in the R7B section below. Caveat: the Host and the device were clients of the phone's hotspot, so the tailnet path was direct/local — this proves a second device over Serve/HTTPS, not an external-network traversal |
| A4 — OTA remains closed | PASS: `GET /api/device/firmware/status` → `configured: false`; `POST /api/device/firmware/arm` → 503; the device request for the manifest → 503 |
| A5 — no unapproved system change | PASS: only the approved Host Tailscale install (no phone install was performed) plus the tailnet HTTPS toggle; no firewall edit, no company-VPN change, no other Host service or registry change |
| A6 — recorded | this section, the R7B section, `docs/GOAL.md` and `docs/R7-REMOTE-ACCESS.md`; phone screenshots are now present in the evidence directory |

- Device address: this run the Host listened on `10.127.70.75:8000` and `127.0.0.1:8000`
  (PID 19540 without the flag, PID 27876 with it). The device moved with DHCP from
  `10.21.98.216` to `10.127.70.216`; it polls the Host continuously on firmware `round2-r6-3`
  (a ping result was not archived; the polling log is the evidence), so the A1/A2 device half
  and the A3 Serve backend were executed for real. The old `10.21.98.216` no longer responds,
  and the old Host LAN address `10.21.98.75` is gone. The evidence covers this run, this machine
  and this network only.
- Evidence (`D:/Codex/round2-r7-20261108/acceptance/`, outside the repo): `netstat.txt`
  (PID 27876), `serve-status.txt`, `https-check.txt`, `lan-regression.txt` (A1/A2 with the real
  device), `remote-switch.txt` (Serve backend), `ota-503.json`, `remote-phone.txt` and
  `remote-manage.png` / `remote-memo-save.png` / `remote-memo-preview.png` (redacted phone
  screenshots).
- No firewall, company-VPN or Host service was changed; `config/firmware.json` remains absent
  and remote OTA was not attempted (A4).
- NOT RUN: external-network traversal (the Host and the device were clients of the phone's
  hotspot, so the tailnet path was direct/local); mDNS client discovery (the device reached the
  Host through its configured LAN endpoint and the Host-side advertisement started without
  error); PWA installation on the HTTPS source. DEPLOYMENT = PARTIAL; REMOTE ACCEPTANCE = PASS
  (A3 phone half, hotspot-local path).

## Phone remote acceptance (R7B, 2026-11-09)

- Phone conditions: Wi-Fi off, cellular (5G), Tailscale connected; the Host saw the phone as an
  online peer with a direct path. The device (`10.127.70.216`, round2-r6-3) was polling the Host
  (`10.127.70.75:8000` + `127.0.0.1:8000`, PID 27876).
- Phone run (21:02–21:06 +08): `/manage` loaded over HTTPS through Serve. Baseline weather-r52,
  frame `a7fbcac6…`, count 51. Memo selected (memo-r6, count 53); one item was added and two
  states changed, then saved ("已保存，等待设备下一次轮询（≤60 s）"); the draft preview reported
  frame version `98d9f85c…` with footer `memo r7`. Back on weather: weather-r53, ETag
  `ab42d7ab9739b54a05b9d03341de46567806b30b5cd3a26976fdf9304250af40`, accepted equal,
  `DEVICE_REFRESH_FLOW_COMPLETE`, count 56, last_seen 13:06:31Z; a later sample at 13:07:33Z
  kept count 56. The per-action split of 51 → 53 → 56 was not instrumented.
- Restore: memo revision 7 → 8 with the revision-6 content (3 items, original states); no test
  data remains. Final page weather-r53 at count 56.
- Earlier Host-initiated Serve run (kept for the backend half): pet `2f6ea60d…` count 47 → 48;
  preview 15000 B with `X-Frame-Version` equal to the served ETag; memo PUT r4 → 5 → 6
  restored; weather restore count 49.
- Evidence (`D:/Codex/round2-r7-20261108/acceptance/`): `remote-manage.png`,
  `remote-memo-save.png`, `remote-memo-preview.png` (address bar and HOST value redacted),
  `remote-phone.txt`, and the updated `README.md`.
- Caveat: the Host and the device were clients of the phone's hotspot, so the tailnet path was
  direct/local. This proves a second device managing the Host through Serve/HTTPS, not
  traversal from an external network. The external-network case stays NOT RUN until the Host
  can leave the hotspot (M2 / R3D).
- NOT RUN: PWA installation on the HTTPS origin; physical inspection of the memo frame (the
  device moved on to weather-r53).
- UI note: the identity card reads the Progress panel status, so with a non-Progress page
  selected it shows `未配置 / 未通信` while the page card shows the real device report. Cosmetic;
  logged for M6, not fixed in this increment.

## R3D multi-network (2026-11-09)

- Landed (commits `df8ffb4..95848a2`, 10 commits, 6 files, +665/-31; spec `b619271`, plan
  `df8ffb4`): a fixed 301 B three-slot store (`networks`, version 1) in the existing
  `eink-wifi` NVS namespace with `static_assert` on the layout; selection by last-success slot
  then storage order with empty/invalid slots skipped; one-time migration of the legacy
  `validated` pair into slot 0 (a present but malformed blob is never overwritten by the load
  path, though an explicit add/forget can replace it, and a failed `hasStore()` read-only open is
  treated as absent); add/update by exact SSID and forget by index with compaction and `lastOk`
  adjustment, both on the setup page
  (`/configure`, `/forget`); the store-full rejection as 409; and the Machine's fallback — one
  `nextWifi()` port hook, three 15 s attempts (≤45 s) inside `WifiConnect` before the existing
  `FailureWait`. `validated` is still dual-written so the previous image keeps one working pair.
- Build identity `round2-r3d-1` (the stage ini now passes `EINK_FIRMWARE_VERSION=\"round2-r3d-1\"`
  to `esp32-m1-network-progress`; the image no longer reports the stale default `round2-r6-1`).
  Software gates PASS, re-run on this HEAD with the version TU forced to recompile: both envs
  build exit 0 — RAM 71,576 B / 327,680 B, flash 875,357 B (non-OTA) and 875,193 B (OTA), all
  unchanged by the token; both ELFs contain `round2-r3d-1` and no `round2-r6-1`. The pre-R3D
  control ELF for the same env measures `.dram0.data + .bss = 71,256` B, so R3D costs ~320 B of
  static RAM (the 301-byte store plus alignment). Four `tests/cpp` harnesses `-fsyntax-only`
  exit 0 (the Machine harness is compile-only, it was not run), Python 697 passed, frontend
  57 pass / 0 fail. Scope and credential scan: 6 changed files, no real credential literals.
- **No flash, upload, NVS erase, reset or power-cycle was performed.** DEVICE ACCEPTANCE =
  NOT RUN: two-network provisioning, boot preference, failover after the AP is turned off, 409
  on the device, forget plus rollback reflash, `NETWORK_NVS` stats, serial excerpts and the
  physical frame/count checks all still need separate flashing authorization. Records and
  commands: `D:/Codex/round2-r3d-20261109/acceptance/` (outside the repo).
- Runbook: `docs/R3D-MULTI-NETWORK.md`. Known limits: one active link; no AP+STA outside
  provisioning; no NVS erase or partition change; store fixed at 301 B / three networks; the
  setup AP stays open and S1-gated; worst case ≤45 s per cycle and ≤105 s after an idle drop.
  The spec's failover line expects `200 → 304`, but the code keeps the accepted ETag across a
  network switch, so the first post-failover poll is normally 304 unless content changed or the
  device rebooted; device acceptance records the actual sequence.
  Deferred minors (29 ledgered, all non-blocking — see
  `.superpowers/sdd/2026-11-09-r3d-multi-network/progress.md`) include a foreign-blob replacement
  by an explicit add/forget, the failed read-only open treated as "absent" in `hasStore()`,
  `resultText()` without a `default:` plus `-Werror=switch`, `/forget` index bounds written as
  `'0'..'2'` instead of `kMaxWifiNetworks`, and the page's ~45 String concatenations without
  `reserve`. M2 is closed as PARTIAL by the physical acceptance section below; DEPLOYMENT stays
  PARTIAL.
  No credential, SSID or account is recorded here.

## R3D multi-network — physical acceptance (2026-11-10)

- Flashed `round2-r3d-1` (881,936 B, COM12) under explicit authorization. No NVS erase, no
  partition change, no push or tag. Boot: `NETWORK_WIFI_STORE=301`, free heap 280,892 B, NVS
  `used=92 free=538 total=630` (`93/537/630` after the first added network). The first cycle
  failed with `FAILURE=5` because the Host process was still bound to a stale address; the next
  cycle returned 200 and refreshed.
- PASS: the legacy `validated` pair was migrated into slot 0 (no re-provisioning needed and the
  setup page listed it as a stored row); a second network was added (list showed 2 rows);
  re-submitting an existing SSID updated in place (the list stayed at one row for it); boot
  preference (five reboots rejoined a stored network); `200 → 304` with counts 57 → 59 on
  content changes, 59–62 held through 304s, and exactly +1 per post-boot first frame
  (59 → 60, 60 → 61, 62 → 63); forgetting the second network (list 2 → 1) followed by a reset
  that joined the remaining network and resumed 304 plus reports at 18:06 (`refresh_count` 63).
  No credential appears in the serial or Host logs.
- BLOCKED: failover with the active AP switched off — there was no controllable second AP. The
  second network was a mobile Wi-Fi whose clients the Host could not reach, and the first
  network is the Host's own uplink. The operator decision on 2026-11-10 is to record the item
  BLOCKED and close M2 as PARTIAL.
- NOT RUN: `409` on a full three-network store (only two networks existed); rollback reflash of
  `round2-r6-3` (separate authorization; the image was not built in this tree).
- Finding (design-consistent): with the device associated to a network the Host had left, it
  stayed on that slot — association succeeded, mDNS found nothing, the configured fallback is
  the TEST-NET address `192.0.2.1:8080` — and repeated `FAILURE=5`; it did not try the other
  stored slot because fallback runs only on association failure. Moving the Host back restored
  polling within one poll. Finding (operator caveat): a `stopSoftAP()` failure after a
  successful save left the device in Provisioning with the pair already saved; a manual reset
  was required (observed twice).
- Evidence: `D:/Codex/round2-r3d-20261109/acceptance/` (`README.md`, `upload.txt`,
  `serial-*.txt`, `status-*.json`, `host-*.log`). SSIDs are masked there and here. Current
  device: `10.49.252.216`, page takeout, `refresh_count` 63, firmware `round2-r3d-1`; Host
  `10.49.252.75:8000` plus loopback.
- M2 closed as **PARTIAL** on 2026-11-10: the store, selection, migration, add, update, forget
  and polling semantics are physically verified; failover, 409 and rollback stay open.

## M3 R6 residuals (2026-11-10)

- Single full-refresh timing (PASS): two Host page switches each produced one 200 on the next
  60 s poll; the device printed `_Update_Full : 2184000` both times (2,184,000 µs = **2.184 s**
  per full refresh, integer-identical). HTTP connect → flow-complete report was **3 s**; the
  switch was served **50 s** and **8 s** after the request, i.e. always the next poll. The
  following 304 performed no display call and left the count at 65. Serial:
  `D:/Codex/round2-m3-20261110/timing-serial.txt`.
- CXX_RUNTIME rubric (recorded): no host C++ compiler exists (`where g++ clang++ cl` finds
  nothing; no MSYS/MinGW/LLVM/Visual Studio; PlatformIO and `.venv-hw` hold only the xtensa
  cross toolchain, which cannot execute on Windows). The four harnesses recompiled with
  `-fsyntax-only` exit 0 today, so compile-time `static_assert`s are evidence, but the runtime
  `assert()`s in `test_network_progress.cpp` (parser, state machine, report ordering) were never
  executed. CXX_COMPILE_CHECK = PASS; **CXX_RUNTIME = NOT RUN**, and that boundary is now
  explicit rather than implied. No host toolchain was installed; that would be a separate
  system change.
- OTA end-to-end (PASS): built the OTA env at HEAD with `EINK_FIRMWARE_VERSION=round2-r3d-ota1`
  (flash 875,193 B, `firmware.bin` 881,776 B), configured the gitignored Host offer, armed it and
  completed the update in about 10 s; the device rebooted into it with NVS intact (count 65),
  joined Wi-Fi in 5 s from the stored credentials, emitted `NETWORK_OTA_VALIDATED` 120 s later
  and kept polling 304. The Host auto-disarmed on the accepted report.
- Corrupted image (PASS): 16 bytes flipped in a copy (offered as `round2-r3d-bad1`); the device
  downloaded it, failed `esp_ota_end` and entered `FailureWait` with `FAILURE=10`
  (FirmwareUpdateFailure) — no reboot, no display call, running image and frame kept.
- Mid-transfer disconnect (PASS): killing the Host 0.5 s after `STATE=19` aborted the body;
  the device reported `FAILURE=10` four seconds later with no `NETWORK_OTA_READY` and no reboot,
  then resumed 304 polling once the Host was back. The first two attempts were discarded (one
  kill landed after the ~2 s transfer completed, one matched a stale serial marker); only the
  third is counted.
- Post-OTA Android shell (PASS): the P6 shell on the phone loaded `/manage` and every static
  asset from the updated Host (200), switched to memo and back to takeout through the shell,
  pulled both previews, and the device fetched the two changed frames (count 68 → 70, page back
  on takeout). This closes the last non-flashing M3 item.
- Rollback reflash of `round2-r6-3` (PASS): built at `9636407` (`esp32-m1-network-progress-ota-r6-3`,
  flash 870,245 B, image 876,816 B), USB-flashed on COM12, booted with the NVS counter intact
  (70) and — after re-provisioning net-a — served 200 → 304 (count 71). The device was then
  restored to `round2-r3d-ota1` by OTA (`NETWORK_OTA_READY`, post-boot count 72, VALIDATED
  120 s later) without a second USB flash. Finding: the legacy `validated` pair is the last
  *provisioned* network, not the last successful one; because R3D had last provisioned and then
  forgotten net-b, the old image booted onto net-b, which the Host cannot join, and had to be
  re-provisioned before the frame path could be verified.
- Evidence: `D:/Codex/round2-m3-20261110/` (`README.md`, `timing-serial.txt`, `cxx-probe.txt`,
  `build-ota.txt`, `ota-serial.txt`, `reset-before-fault.txt`, `fault-serial2.txt`,
  `host*.log`, `rollback-*.txt`, `build-r6-3.txt`, `upload-r6-3.txt`). Current device:
  `10.49.252.216`, page takeout, `refresh_count` 72, firmware `round2-r3d-ota1` (OTA image;
  credentials from NVS).

## M6 management identity card (2026-11-10)

- Bug: the `/manage` identity card (`身份 / 连接`) read the Progress-only
  `/api/panels/progress/status`, so with memo, course or takeout selected it still showed the
  Progress source and rendered `--` / `未通信` for the device fields even though the device was
  polling.
- Fix: `identityFields()` in `web/manage_logic.mjs` now takes the selected page's
  `/api/pages/status` payload; `web/manage.js` polls that endpoint with the 10 s status cycle and
  renders `source`, `frame_format`, `device.firmware_version` and `device.last_seen`. A failed
  pages-status read shows `UNKNOWN` in all four fields, matching the existing failure wording.
- Tests: three `identityFields` cases (selected page, idle wording, failed poll) written before
  the implementation; `node --test tests/frontend` → **60 pass / 0 fail** (was 57).
- Verification: `node --check web/manage.js` exit 0; the running Host (PID 24776, this worktree)
  serves the edited `manage.js`/`manage_logic.mjs`; evaluating `identityFields` against the live
  `/api/pages/status` while page `takeout` was selected produced
  `{"source":"takeout","frameFormat":"epd-t-400x300-mono1-msb-v1","firmware":"round2-r3d-ota1",`
  `"lastSeen":"2026-11-10T12:34:13.708825+00:00"}`. Browser visual re-check **NOT RUN**: the
  browser connector was not connected in this session, and the Edge instance launched for it
  could not be driven (input rejected as covered); it was closed afterwards. Device unchanged:
  `10.49.252.216`, page takeout, `refresh_count` 72, firmware `round2-r3d-ota1`.

## M6 HTTPS-origin PWA install (2026-11-10)

- Origin: Tailscale Serve (`443 → http://127.0.0.1:8000`, tailnet only); the tailnet host name is
  deliberately not recorded. The Host keeps its LAN + loopback dual listen.
- Served over HTTPS: `/manage` 200 `text/html`, `/manifest.webmanifest` 200
  `application/manifest+json`, `/sw.js` 200 `application/javascript`, both icons 200 `image/png`,
  `/api/pages/status` 200 JSON. Manifest fields: `id`/`start_url` `/manage`, scope `/`,
  `display: standalone`, icons 192×192 and 512×512.
- Installability (headless Chrome, local debug port, HTTPS origin): `window.isSecureContext`
  true; manifest linked with no parse errors; Service Worker scope `/`, state `activated`,
  `navigator.serviceWorker.controller` true; `Page.getInstallabilityErrors` returned **[]** (no
  blocking condition).
- Phone install (operator-confirmed): over the HTTPS origin, the in-page `安装到主屏` button
  appeared automatically (`beforeinstallprompt`), and the operator completed the installation.
  This closes the R5/R7B "phone PWA install NOT RUN" item. The Host access log around the install
  shows `/manage`, `/manifest.webmanifest`, `/static/icons/icon-192.png` and `/sw.js`
  (`D:/Codex/round2-m3-20261110/host-rollback.log`).
- Limits: standalone/offline launch after install was **not separately observed**; the
  non-tailnet external path remains NOT RUN; only Chrome on Android is covered (no iOS claim).

## M6 page boundary states (2026-11-10)

- Scope (operator-selected): the "当前页面" card's wording when the selected page has no frame or
  no source. No device switch, no firmware change.
- Problem: `pageSwitchState` only returned `active` / `pending` / `expired`, and the `expired`
  label was always "等待设备取帧". With Progress selected and no configured source (the live Host
  state) the card therefore implied a frame was on its way, although the device would keep
  receiving 503 until an event was published. The state name was also misleading.
- Change: states are now `active` / `pending` / `no-frame` / `unknown`; labels are
  "Host 已提供当前帧" / "等待切换" / "该页暂无帧". Progress distinguishes
  "未配置发布源，暂无帧" (tone `error`) from "等待发布事件" (source present), and a file page
  before its first render says "该页暂无帧" (tone `warn`). Tone selection moved into
  `pageSwitchTone`; the switcher's dashed border follows `data-state="no-frame"`.
- Tests: three frontend cases cover the state, label and tone matrices; `node --test tests/frontend`
  → **62 pass / 0 fail**. The page API test now pins the Progress-without-event status
  (`publish_id` and `frame_version` null, `frame_format` still present); Python **697 passed**.
- Live check (payload-only, device untouched): current takeout → `active` /
  "Host 已提供当前帧"; the live Progress status (source null, no frame) → `no-frame` /
  "未配置发布源，暂无帧" / `error`; a synthetic file page before its first render → `no-frame` /
  "该页暂无帧" / `warn`. Browser screenshot **NOT RUN** (no browser connector in this session).

## M5 release alignment (2026-11-10)

- Authorization: the operator's explicit request to process M5's authorization and tag. Tag name
  `v0.5.0-round2-stable` chosen from the presented options.
- Pre-flight: `origin/main` was `4e0e55e` and local `main` was 70 commits ahead; `git ls-remote`
  returned the same remote head. The release diff contains no `config/firmware.json`, firmware
  image, key or credential file (the two tracked Wi-Fi headers hold code plus the public setup
  SSID only). Fresh gates: Python **697 passed**, frontend **60 pass / 0 fail**.
- Result: the release commit fast-forwards `origin/main` from `4e0e55e` to
  `v0.5.0-round2-stable`; the annotated tag describes the round-2 content and its open items.
  Open items remain M2 failover (BLOCKED), device 409 (NOT RUN), M4 BUSY B1–B11 (blocked on
  procurement) and the HTTPS-origin PWA install (NOT RUN at release time; closed later on
  2026-11-10 — see "M6 HTTPS-origin PWA install").

## Limits and next stage

- State is in memory per Host process and cleared on restart; one image and one device; OTA can
  delay a frame poll by up to 120 s and causes one reboot on success; trust is LAN-only.
- The readiness marker may be truncated because there is no `Serial.flush()` before restart;
  this run captured it intact.
- NEXT_REQUIRED_STAGE = M2 (R3D) closed as **PARTIAL** on 2026-11-10. Physical acceptance
  covered the migrated store, two-network add/update, boot preference, `200 → 304`, count
  semantics and forget-then-rejoin; the item list and evidence are in the
  "R3D multi-network — physical acceptance" section and
  `D:/Codex/round2-r3d-20261109/acceptance/`. Still open: live failover with the active AP
  switched off (BLOCKED — no controllable second AP; the second network's clients were not
  reachable from the Host, and the first network is the Host's uplink), `409` on a full store
  (NOT RUN — only two networks existed), and the `round2-r6-3` rollback reflash (NOT RUN —
  separate flashing authorization; build at commit `9636407`). The next mainline increment is
  M3 (R6 residual), which also carries the rollback reflash. M3 started on 2026-11-10: the
  refresh timing is measured (2.184 s), the CXX_RUNTIME rubric is recorded (NOT RUN, no host
  compiler), and the authorized OTA path is verified (end-to-end OTA, corrupted image rejected,
  mid-transfer disconnect aborted safely; the device now runs `round2-r3d-ota1` from NVS
  credentials). M3 is complete: the last item, the `round2-r6-3` rollback reflash, passed on
  2026-11-10 (old image 200 → 304, restored to `round2-r3d-ota1` by OTA). M5 is complete: the
  authorized push aligned `origin/main` with local `main` and tagged the release
  `v0.5.0-round2-stable` (see "M5 release alignment"). The remaining mainline increment is
  M4 (BUSY B1–B11, blocked on procurement). M6's logged identity-card item was fixed on
  2026-11-10 (see "M6 management identity card") and the HTTPS-origin PWA install then passed on
  the phone (see "M6 HTTPS-origin PWA install"); the remaining M6 items are optional and
  unselected.
  M1 closed on 2026-11-09: the hotspot was restored, the device polls again (`10.127.70.216`,
  count 51 → 56), and the phone completed the A3 phone half over Serve/HTTPS (see the R7B
  section). The earlier "读取中" state was not reproduced in this run and no page fix was made.
  DEPLOYMENT = PARTIAL because the non-tailnet external-network case remains NOT RUN; the
  HTTPS-origin PWA install is now PASS.
  P8 four-city weather
  remains the last completed page increment, physically verified and declared complete by the
  operator on 2026-11-08 (device accepted all four cities plus a `/manage` switch). All optional
  page increments are implemented.
  R6 physical failure-injection/rollback remains NOT RUN; multipage physical acceptance PASSED for
  a single device and AP; refresh counting and hotspot re-provisioning PASSED (instrumented
  per-refresh timing remains NOT RUN); R7A software PASS; A1/A2 and the A3 phone run PASS with
  the hotspot-path caveat; R8 not authorized.
