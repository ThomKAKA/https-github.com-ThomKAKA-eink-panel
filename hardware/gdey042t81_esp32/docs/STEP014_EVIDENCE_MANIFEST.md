# STEP-014 H0 evidence manifest

Read and SHA256 verified on 2026-09-10. Original files are not modified or renamed.
Local base: `D:\Codex\eink-panel\hardware\evidence\STEP014_H0`.

| Filename | Bytes | SHA256 | Source | Observation |
| --- | ---: | --- | --- | --- |
| STEP014B3B_upload_COM11.txt | 3686 | 0EE7CBAD4E5AFC2C3F52103B659222DEF90BEAD3D021D40A00C2C0341011E6A6 | successful PowerShell console output copied from the ChatGPT conversation and preserved into a local evidence file | Correct env/COM11, four writes and hash checks, RTS reset and SUCCESS; not an original PowerShell transcript |
| STEP014B3B_final_display.jpg | 270041 | 7A757B15E3C28351AFB7A1D4F3D239A774A0CE0ADD60C3EDABA9BC53AFF2731B | User-provided physical screen photograph, copied into this directory | Border, cross, central block, hollow and solid corner markers visible; source-to-photo anti-diagonal feature correspondence, exact mapping pending |

Reference: `D:\Codex\eink-panel\artifacts\step014-h0-safe\src\test_bitmap.h`
and `test-pattern.png` in that project. Raw decoded bitmap SHA256:
`6a7a2758f0a7b6526bb9c2f6e2cd0aed4c102852b3be68127910f4c151777581`.
See [audit](STEP014_H0_AUDIT.md) for the eight-transform comparison and evidence limits.

Raw upload text includes a device MAC identifier; raw photo includes background
objects and a second board, which is not the main route. Do not automatically stage
these originals. Current task leaves their existing untracked status unchanged;
no ignore policy or original file content is changed.
