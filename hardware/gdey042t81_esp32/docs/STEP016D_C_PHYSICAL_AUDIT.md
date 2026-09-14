# STEP016D-C Physical Business Page Validation Audit

## 1. Stage

Stage:

STEP016D-C PHYSICAL BUSINESS PAGE VALIDATION

Result:

PASS (limited scope)

This stage validates the first real STEP016 Progress business page on the
Good Display ESP32-M1 + GDEY042T81 hardware path.

This result does not extend the previously frozen H0/H1 verification scope
beyond the explicitly recorded observations below.


## 2. Frozen Software Baseline

Pre-physical-validation HEAD:

07ba02734dd7266d4b6acd37fcc032758b683b76

PlatformIO environment:

esp32-m1-progress

Frozen firmware.bin SHA-256:

942F7EAA9A7AD6574EE36A05478D085D52440D0578C82ED0457A7C65AC241523

Frozen firmware.elf SHA-256:

A5C170FE154E8A4DF6B978342D274B48B270CF1DCBFF34F23011B4ECC41302F1

Transport frame SHA-256:

A243C5740472D3F2F3C09CA440446D2E50B5DA0B32BCB00B6DDCA533F6084F8D

Transport frame length:

15000 bytes

Coordinate frame:

T


## 3. Frozen Display Path

The validated software path before physical upload was:

Progress JSON

→ Python Renderer

→ L logical frame

→ L-to-T transport adapter

→ T transport frame

→ embedded 15000-byte C array

→ ESP32-M1 firmware

→ existing H1 display path

→ GDEY042T81


Orientation contract:

L → one PC-side Y mirror → T → fixed H1 Y mirror → physical P = L

No additional rotate / flip / mirror is permitted in the MCU loading path.


## 4. Hardware Identification Before Upload

Windows PnP enumeration:

PASS

Device:

USB-SERIAL CH340 (COM11)

VID:PID:

1A86:7523

PnP status:

OK

PlatformIO device discovery:

PASS

Actual upload port:

COM11


## 5. Firmware Identity Gate

Immediately before upload, firmware.bin SHA-256 was recalculated.

Actual:

942F7EAA9A7AD6574EE36A05478D085D52440D0578C82ED0457A7C65AC241523

Expected:

942F7EAA9A7AD6574EE36A05478D085D52440D0578C82ED0457A7C65AC241523

Result:

PASS

No rebuild was performed between identity verification and the controlled
upload.


## 6. Before-Upload Evidence

Evidence file:

STEP016D-C_before_upload.jpg

SHA-256:

1A71796A04D11A70C80BEAA79145C776EA4430386558E302D0ADD2D381DC76CB

Purpose:

Records the display/hardware state before the controlled STEP016D-C upload.

Raw evidence remains local-only under hardware/evidence/ and is not committed.


## 7. Controlled Upload

Upload environment:

esp32-m1-progress

Upload port:

COM11

Upload method:

PlatformIO nobuild upload

Result:

SUCCESS

Observed tool output included:

- manually specified COM11
- firmware.bin upload
- esptool connection to ESP32
- write reached 100%
- "Hash of data verified."
- hard reset via RTS
- PlatformIO SUCCESS

Reported upload duration:

5.942 seconds

No automatic retry was performed.

No second upload was performed for evidence collection.


## 8. Physical Display Observation

User-observed result:

Business page refresh occurred:

YES

Visible refresh behavior:

Multiple visible refresh / flash phases were observed.

Final page stable after update:

YES

Continuous refresh after stabilization:

NO OBSERVED CONTINUOUS REFRESH


Important evidence boundary:

The multiple visible phases must not be interpreted by themselves as multiple
firmware FULL refresh invocations.

A standard e-paper FULL waveform may contain multiple visible black/white
transition phases.

Therefore:

Exact physical FULL invocation count:

NOT INDEPENDENTLY VERIFIED


## 9. Business Page Content Validation

Expected and physically observed:

Project:

电子纸项目

Result:

PASS


Step:

页面验证

Result:

PASS


Progress:

60%

Result:

PASS


Status:

进行中

Result:

PASS


Snapshot time:

2026-09-13 14:30

Result:

PASS


Chinese rendering:

PASS

Physical reading orientation:

PASS

Final page stability:

PASS

Obvious clipping:

NONE OBSERVED

Obvious overlap:

NONE OBSERVED

Obvious abnormal black blocks/artifacts:

NONE OBSERVED


## 10. After-Display Evidence

Evidence file:

STEP016D-C_after_display.jpg

SHA-256:

8C8856AB363F510350F71CF85333C8AD36FE09D8C905BD43CCDE7EBBF4D39098

Purpose:

Records the final physically displayed STEP016 Progress business page.

Raw evidence remains local-only under hardware/evidence/ and is not committed.


## 11. H1 Safety Boundary

Static verification before physical execution confirmed that the STEP016
Progress firmware preserved the existing H1 display path:

- initial=true
- fast full update disabled
- complete dual-RAM preparation
- standard FULL refresh path
- refresh is the final EPD/display operation
- zero EPD commands after refresh returns
- no Partial Refresh
- no Fast Refresh
- no Deep Sleep
- no runtime Wi-Fi fetch
- no runtime HTTP fetch
- no automatic refresh loop

The physical test did not independently instrument or count low-level display
commands.


## 12. Verification Boundary

The following are verified by STEP016D-C:

- frozen firmware successfully uploaded to the target ESP32-M1
- real Progress business page appeared on GDEY042T81
- expected five business fields were displayed correctly
- Chinese rendering was physically readable
- final physical orientation was correct
- final page became stable
- no obvious clipping, overlap, or abnormal black artifacts were observed


The following remain NOT TESTED or NOT VERIFIED:

BUSY timeout fault injection:

NOT TESTED

Deep Sleep:

NOT TESTED

Partial Refresh:

NOT TESTED

Fast Refresh:

NOT TESTED

Long-duration operation:

NOT TESTED

Exact physical FULL invocation count:

NOT INDEPENDENTLY VERIFIED

Network business-data delivery:

NOT TESTED


## 13. Final Decision

STEP016D-C PHYSICAL BUSINESS PAGE VALIDATION:

PASS (limited scope)

The end-to-end offline Progress display chain is physically validated:

Progress JSON

→ Renderer

→ L frame

→ T frame

→ embedded ESP32 firmware

→ GDEY042T81

→ correctly readable Progress business page

No broader hardware or runtime claims are made beyond this audit boundary.