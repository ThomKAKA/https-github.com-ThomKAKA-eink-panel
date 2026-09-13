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

STEP016C: COMPLETE


Current Objective:

Strict offline JSON mapping and the existing ProgressPanel now generate a normal-reading
400x300 1-bit PNG. Renderer-only scope; no raw/header or transmission preflip.
Renderer-only review passed and finalization authorized by the user.
Renderer implementation completed; Renderer-only verification completed;
Bitmap generation verified. ESP32 integration NOT RUN; Physical display
verification for STEP016C NOT RUN. Do not enter STEP016D without authorization.


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

NO


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
- Python regression: 203 passed (125 existing + 78 new), 2.06s
- Raw/header export, transmission direction adaptation, firmware integration: NOT RUN
- New hardware validation and compilation: NOT RUN


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


Pre-STEP016C-finalization HEAD (parent baseline):

d9fea1667be33a354e9987a2cc92dbf8379212bb


Commit history:

- STEP015C: 85e2c4bb64561e55d27b42f215e1235b123a6ae8
- STEP016B INTERFACE FREEZE: f8bf7ae8270aa34d58cb3006f6ab44db2792fd5c


Current expected untracked:

hardware/evidence/

STEP016C finalization commit message:
`feat(renderer): implement offline progress page`
The commit containing this state records the seven authorized files. Resolve its
SHA from Git history; no self-referential commit hash is embedded here.
Artifacts stay ignored; hardware/evidence/ stays local-only and untracked.


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
