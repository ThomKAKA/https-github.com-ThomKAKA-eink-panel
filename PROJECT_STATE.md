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

STEP016D-C EVIDENCE CLOSURE: COMPLETE


Current Objective:

Close STEP016D-C evidence using the user's confirmed physical result:
PASS (limited scope) for the Offline Progress Display. Frozen firmware upload on
COM11 succeeded; the GDEY042T81 Progress page showed the five expected fields,
normal Chinese text and orientation, and a stable final page without obvious
clipping, overlap or black artifacts. This closure only organizes existing
evidence; it does not repeat hardware verification.


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

# End of Current State
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
