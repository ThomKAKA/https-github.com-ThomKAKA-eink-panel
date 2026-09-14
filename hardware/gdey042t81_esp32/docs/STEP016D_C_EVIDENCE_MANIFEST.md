# STEP016D-C Evidence Manifest

## 1. Scope

Stage:

STEP016D-C PHYSICAL BUSINESS PAGE VALIDATION

Final result:

PASS (limited scope)

Pre-validation HEAD:

07ba02734dd7266d4b6acd37fcc032758b683b76

Raw evidence directory:

hardware/evidence/STEP016D_C/

Raw evidence policy:

LOCAL ONLY / UNTRACKED

Raw evidence must not be added to Git.


## 2. Frozen Firmware

File:

hardware/gdey042t81_esp32/.pio/build/esp32-m1-progress/firmware.bin

SHA-256:

942F7EAA9A7AD6574EE36A05478D085D52440D0578C82ED0457A7C65AC241523

PlatformIO environment:

esp32-m1-progress

Role:

Exact frozen binary used for the controlled STEP016D-C upload.


## 3. Frozen ELF

File:

hardware/gdey042t81_esp32/.pio/build/esp32-m1-progress/firmware.elf

SHA-256:

A5C170FE154E8A4DF6B978342D274B48B270CF1DCBFF34F23011B4ECC41302F1

Role:

Build artifact previously used to verify the embedded 15000-byte transport
array identity.


## 4. Transport Frame

Coordinate frame:

T

Length:

15000 bytes

SHA-256:

A243C5740472D3F2F3C09CA440446D2E50B5DA0B32BCB00B6DDCA533F6084F8D

Previously verified relationship:

T raw bytes
=
generated embedded C array bytes
=
15000-byte array extracted from firmware ELF

This is software identity evidence.

It is not physical pixel-mapping evidence by itself.


## 5. Before-Upload Photo

File:

hardware/evidence/STEP016D_C/STEP016D-C_before_upload.jpg

SHA-256:

1A71796A04D11A70C80BEAA79145C776EA4430386558E302D0ADD2D381DC76CB

Evidence type:

RAW LOCAL PHOTO

Role:

Records physical display/hardware state immediately before the controlled
STEP016D-C upload.

Limit:

Does not prove firmware execution or later refresh behavior.


## 6. Upload Evidence

Target:

Good Display ESP32-M1

USB bridge:

CH340

VID:PID:

1A86:7523

Actual port:

COM11

Environment:

esp32-m1-progress

Upload result:

SUCCESS

Relevant terminal observations:

- Using manually specified COM11
- Uploading firmware.bin
- ESP32 detected
- Writing reached 100%
- Hash of data verified
- Hard resetting via RTS pin
- PlatformIO SUCCESS

Duration:

5.942 seconds


### Upload log file

If a preserved local copy of the terminal output is created, record:

File:

hardware/evidence/STEP016D_C/STEP016D-C_upload_log.txt

SHA-256:

<RECORD AFTER FILE EXISTS>

Evidence classification:

PRESERVED / COPIED TERMINAL OUTPUT

Do not describe a manually copied log as an original automatic transcript.


If no local upload log file has yet been created:

Upload log file SHA-256:

NOT YET RECORDED

The audit must not invent a hash.


## 7. After-Display Photo

File:

hardware/evidence/STEP016D_C/STEP016D-C_after_display.jpg

SHA-256:

8C8856AB363F510350F71CF85333C8AD36FE09D8C905BD43CCDE7EBBF4D39098

Evidence type:

RAW LOCAL PHOTO

Role:

Records final physical Progress business page.

Supports:

- page physically appeared
- final orientation
- visible content
- visible layout
- final stable image appearance

Does not independently prove:

- exact FULL refresh invocation count
- BUSY timeout behavior
- Deep Sleep behavior


## 8. Human Observation Record

Observer reported:

Business page refresh occurred:

YES

Visible refresh behavior:

MULTIPLE VISIBLE REFRESH / FLASH PHASES

Final page stable:

YES

Orientation:

NORMAL READING DIRECTION

Expected content:

电子纸项目 — PASS

页面验证 — PASS

60% — PASS

进行中 — PASS

2026-09-13 14:30 — PASS

Chinese rendering:

PASS

Obvious clipping:

NONE OBSERVED

Obvious overlap:

NONE OBSERVED

Obvious abnormal black artifacts:

NONE OBSERVED


Interpretation boundary:

Multiple visible waveform phases do not establish multiple firmware FULL
refresh invocations.

Exact physical FULL invocation count remains:

NOT INDEPENDENTLY VERIFIED


## 9. Evidence Boundary

Supported:

- exact frozen firmware identity
- successful ESP32 upload
- successful esptool data verification
- physical appearance of business page
- content correctness
- Chinese readability
- physical orientation
- final stable state


Not supported:

- BUSY timeout fault handling
- Deep Sleep
- Partial Refresh
- Fast Refresh
- long-duration reliability
- exact physical FULL command count
- network runtime behavior


## 10. Git Policy

Tracked:

hardware/gdey042t81_esp32/docs/STEP016D_C_PHYSICAL_AUDIT.md

hardware/gdey042t81_esp32/docs/STEP016D_C_EVIDENCE_MANIFEST.md

PROJECT_STATE.md


Local-only / untracked:

hardware/evidence/


Expected final Git status after closure commit:

?? hardware/evidence/