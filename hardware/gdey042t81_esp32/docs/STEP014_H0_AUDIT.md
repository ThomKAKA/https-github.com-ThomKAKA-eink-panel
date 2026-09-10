# STEP-014C H0 physical evidence audit

Date: 2026-09-10. Current decision: STEP-014D anchor review establishes Y mirror;
H0=PASS within the defined display-chain and 8-way geometric-orientation scope.
Pixel-level mapping is NOT EXHAUSTIVELY VERIFIED. Earlier STEP-014C PENDING
findings below are retained as history and superseded by the STEP-014D section.
Evidence review only; no upload, monitor, reset, firmware changes
or hardware retest performed. See [evidence manifest](STEP014_EVIDENCE_MANIFEST.md).
Historical STEP-013 and build-only STEP-014B-3A records are not rewritten.

## Upload evidence

Source: successful PowerShell console output copied from the ChatGPT conversation
and preserved into a local evidence file. This is NOT an original PowerShell transcript.
The current 3686-byte file replaces the earlier empty-file observation.

The complete saved text includes manually selected COM11, vendor-h0-safe-lolin32
firmware.bin, Serial port COM11, Connecting, ESP32-D0WD revision v1.1, four write
regions at 0x1000/0x8000/0xe000/0x10000, four Hash of data verified messages,
Leaving, Hard resetting via RTS pin, and SUCCESS Took 173.92 seconds.
The application write is 289824 bytes, consistent with the build record.

UPLOAD=PASS; ESP32 FLASH WRITE=PASS; FLASH HASH VERIFY=PASS; AUTO RESET=PASS,
all based on the preserved console output, not a new hardware observation.
The log does not contain the pre-upload firmware SHA256; pre-upload matching is
user-reported. Flash transfer verification is not an independently recorded
comparison against the STEP-014B-3A SHA256. Device MAC occurs in the original log;
do not reproduce it in tracked documentation or commit the raw log by default.

## Physical image and geometry

The photo shows a physical panel connected by FPC to the ESP32-M1 assembly and
displaying a border, horizontal/vertical lines, central filled rectangle,
upper-right hollow square, and lower-right solid square in photo coordinates.
Identity as GDEY042T81 relies on STEP-013 seller/physical evidence, not solely the
front-face image. PHYSICAL DISPLAY CONTENT=PASS; EXPECTED GEOMETRIC FEATURES=PASS.

The generated bitmap and preview were re-read, not inferred from chat descriptions.
Source coordinates: 400x300; solid square [24,72)x[24,72), hollow square
[328,376)x[24,72), central rectangle [160,240)x[120,180). Border 4 pixels;
cross at x=[198,202), y=[148,152). Packed row-major MSB-first, 0 black/1 white.
The source header decodes identically to test-pattern.png.

The following table maps source to photo-oriented axes (origin upper-left), before
perspective distortion. Rotation is clockwise; X mirror means reverse x, Y means
reverse y. TL/TR/BL/BR denote corners. Photo-observed pair is solid BR, hollow TR.

| Transform | Solid | Hollow | Dimensions | Corner match |
| --- | --- | --- | --- | --- |
| Identity | TL | TR | 400x300 | No |
| 90 rotation | TR | BR | 300x400 | No |
| 180 rotation | BR | BL | 400x300 | No |
| 270 rotation | BL | TL | 300x400 | No |
| X mirror | TR | TL | 400x300 | No |
| Y mirror | BL | BR | 400x300 | No |
| Transpose | TL | BL | 300x400 | No |
| Anti-diagonal reflection | BR | TR | 300x400 | Yes, feature-level |

Anti-diagonal mapping is x'=299-y, y'=399-x. It places the solid square at
[228,276)x[328,376), hollow square at [228,276)x[24,72), and central rectangle at
[120,180)x[160,240), matching the visible portrait arrangement qualitatively.
The border and cross also remain consistent. This is a feature-level correspondence,
not a pixelwise rectified comparison or proof of a unique hardware coordinate origin.

No pure rotation explains both distinguishable corner markers. A reflection is
required in the source-to-photo composition. The available photo does not establish
whether this arises from photo mirroring, panel scan mapping, or their combination.
Normal camera rotation alone is insufficient. The image is not proven defective;
neither exact orientation nor pixel-for-pixel mapping can be marked PASS.

## STEP-014C historical evidence limits and status (before anchor photo)

| Item | Result | Basis / scope |
| --- | --- | --- |
| UPLOAD / FLASH HASH VERIFY | PASS | Preserved copied console output |
| PHYSICAL DISPLAY CONTENT | PASS | Current photo |
| EXPECTED GEOMETRIC FEATURES | PASS | All six feature types present |
| EXACT ORIENTATION / PIXEL MAPPING | PENDING | Reflection ambiguity and no pixelwise proof |
| DISPLAY CHAIN VERIFIED | YES | Upload evidence plus physical displayed content |
| DISPLAY VERIFIED | YES, content-response only | Not exact mapping or all modes |
| HARDWARE VERIFIED | YES, H0 display-chain scope only | Not comprehensive hardware validation |
| H0 FINAL CLOSURE | PENDING | Exact mapping remains unresolved |
| FULL REFRESH COUNT=1 | Static normal-path claim only | One activation per boot in source; not photo evidence |
| DISPLAY STABLE OVER TIME | User-reported | One photo cannot measure duration |
| DEEP SLEEP PHYSICALLY VERIFIED | NO | Source sends command on success; no runtime/power proof |

Project GxEPD2, network, frame fetching, partial, fast and 4-gray remain NOT
PHYSICALLY VERIFIED. Seven host C++ tests remain BLOCKED / NOT RUN.
STEP-014C evidence analysis is documented, but H0 is not force-closed as PASS.
Next review should establish photo mirroring/camera orientation and a physical
coordinate reference using existing evidence first; no new hardware test is authorized.

## Verification

Python regression: 125 passed in 1.03s. git diff --check passed; new documents
checked separately for trailing whitespace and local Markdown links. Bitmap header
decoded bytes match the PNG preview and recorded raw bitmap hash.
Original evidence and H0 firmware are preserved. No staging, commit, push or tag.

## STEP-014D physical anchor closure

New evidence: STEP014D_orientation_reference.jpg, 956771 bytes, 4096x1864 RGB,
SHA256 50FDA9A99476366114E936D0C69AE5A50E80E98FC555B69CB9A31C1CC4046844.
EXIF Orientation absent; metadata alone proves neither mirroring nor editing history.
The actual image shows the FPC at photo-right, R above the panel, L below it,
and handwritten LEFT -> RIGHT / ABC123 beside the panel. Rotating the viewing
coordinate frame clockwise 90 degrees (without modifying the file) places FPC
down, L left, R right and makes the writing normally readable. PHOTO MIRROR
STATUS=NOT MIRRORED at whole-image visual-anchor level; not a forensic guarantee
against selective editing. USB plug is visibly disconnected; no sleep inference.

Frames, origin at upper-left:
- BITMAP B: x=0..399 rightwards, y=0..299 downwards, solid TL/hollow TR.
- PANEL P: front viewed, long edge horizontal, FPC edge down, L left/R right.
  Observed solid BL/hollow BR; border, cross and central block present.
- PHOTO Q: screen-local portrait axes, u=0..299, v=0..399, not the full JPEG pixels.
  PANEL -> PHOTO is 90 degrees counterclockwise plus photographic perspective:
  u=y_panel, v=399-x_panel. Clockwise rotation is the inverse normalization.

Independent BITMAP -> PANEL candidate check (clockwise rotation convention):

| Candidate | Solid / hollow | Result |
| --- | --- | --- |
| identity | TL / TR | Rejected |
| rotate 90 | TR / BR | Rejected, axes also swapped |
| rotate 180 | BR / BL | Rejected |
| rotate 270 | BL / TL | Rejected, axes also swapped |
| mirror X (reverse x) | TR / TL | Rejected |
| mirror Y (reverse y) | BL / BR | Unique match |
| transpose | TL / BL | Rejected, axes also swapped |
| anti-diagonal reflection | BR / TR | Rejected, axes also swapped |

Thus x_panel=x_bitmap, y_panel=299-y_bitmap. Composing with P -> Q gives
u=299-y_bitmap, v=399-x_bitmap, explaining the earlier BITMAP -> PHOTO
anti-diagonal observation without requiring photo mirroring. These formulas
describe geometric orientation, not a calibrated perspective fit or all-pixel test.

Firmware consistency: H0-safe and original GDEY042T81 FULL sample both use
0x11=0x01 (X increment, Y decrement, X-first), X byte window 0..49,
Y window 299..0, initial counters (0,299), and sequential identical bitmap
writes to 0x24 then 0x26. The 15000-byte MSB-first header still decodes exactly
to the 400x300 preview. This independently supports the observed Y reversal;
no firmware/register correction was made. Register interpretation was checked
against the [SSD1683 datasheet](https://files.seeedstudio.com/wiki/Other_Display/42-epaper/IC%20Driver%20SSD1683%20Datasheet.PDF)
pages 25 and 39-40 in STEP-014D-1.

Current final status:
- PHOTO MIRROR STATUS=NOT MIRRORED (visual anchors).
- PANEL PHYSICAL FRAME=VERIFIED.
- GEOMETRIC ORIENTATION TRANSFORM=Y MIRROR / VERTICAL FLIP.
- GEOMETRIC ORIENTATION VERIFIED=YES, uniquely among eight candidates.
- PIXEL-LEVEL MAPPING=NOT EXHAUSTIVELY VERIFIED.
- UPLOAD=PASS; FLASH HASH VERIFY=PASS (preserved copied console output).
- PHYSICAL DISPLAY CONTENT=PASS; EXPECTED GEOMETRIC FEATURES=PASS.
- DISPLAY VERIFIED=YES; HARDWARE VERIFIED=YES, H0 display-chain scope only.
- H0=PASS; H0 FINAL CLOSURE=COMPLETE under the stated geometric acceptance scope.

No claim of 120000-pixel exhaustive verification, physically verified deep sleep,
fast/partial/4-gray refresh or project GxEPD2 validation. One refresh is a normal
source-path property per boot; stable-over-time remains user observation.
No hardware retest, firmware regeneration, upload, monitor, push or tag occurred.
