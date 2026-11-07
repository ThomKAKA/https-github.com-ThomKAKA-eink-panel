# STEP017C — Repeated Standard FULL Display Lifecycle

Status: DESIGN FROZEN; repeated sessions NOT IMPLEMENTED / NOT TESTED.
Historical references: [H1 closure](STEP015C_H1_PHYSICAL_AUDIT.md),
[STEP016 flow](STEP016D_DISPLAY_FLOW.md), [embedded report](STEP016D_B2B_EMBEDDED_FRAME_REPORT.md),
[physical audit](STEP016D_C_PHYSICAL_AUDIT.md).

## 1. Exact local audit and limitation

[H1SafeGDEY042T81](../src/h1/atomic_display.h) privately inherits the pinned panel
class and exposes coldInit, prepareColdStartFullFrame and refreshOnce only.
[Contract](../src/h1/contract.h) state is New -> Initialized -> Preparing -> Prepared
-> Finished. refreshOnce consumes Finished before calling upstream refresh(false).
The same object cannot prepare/refresh again. true reports invocation, not success.
[Progress entry](../src/progress/main.cpp) copies a 15000-byte embedded T array to
static RAM and then uses this path once. Its loop only delays.

Pinned GxEPD2 1.6.9 / de82887e77a78528ea386e68bba2cb0291d2c319 was read from
`.pio/libdeps/esp32-m1-progress/GxEPD2/src/` under the hardware project:

| Source / function | Relevant fact |
| --- | --- |
| GxEPD2_EPD.cpp constructor/init | Constructor sets initial flags; init(initial=true) reestablishes initial-write/refresh, clears init/power/partial/hibernate bookkeeping and pulses reset |
| H1 coldInit | Requires New and 10000000 us busy timeout; selects SPI 4 MHz/MSB/SPI_MODE0, init(115200,true,10,false), selectFastFullUpdate(false) |
| H1 prepare | Requires nonnull 15000-byte full geometry and initial flags; clears only initial-write, immediately calls upstream full-frame write |
| gdey/GxEPD2_420_GDEY042T81.cpp _writeImage | Full geometry avoids clipping return; _InitDisplay performs SWRESET/configuration; suppressed initial-write avoids implicit clearScreen/refresh |
| writeImageForFullRefresh | Complete previous 0x26 write, then complete current 0x24 write |
| _Update_Full | Standard selection writes 0x22=0xF7 then 0x20; after BUSY wait only sets _power_is_on=false |
| refresh(false) | After _Update_Full only clears initial-refresh; no additional EPD command |
| _waitWhileBusy | Finite 10000000 us threshold, prints and breaks on timeout; void, no reliable error propagation |
| H1/base class destruction | No user-defined cleanup destructor issuing EPD commands; no owned SPI shutdown; D/E must preserve and verify this |

H1 historically means zero further EPD commands for the rest of that one-shot
boot. C does not rewrite that boundary or claim the new repeated policy was already
physically validated. Bookkeeping power=false is not a power measurement.

## 2. Strategy decision

| Strategy | Compatibility / tradeoff | Decision |
| --- | --- | --- |
| Initialize once and repeatedly prepare the same object | H1 rejects Finished; would need a new mutable lifecycle/driver exposure | Not selected |
| New bounded object/session for each accepted changed frame | Reuses exact H1 API/state transitions, restores initial=true and complete dual RAM; repeats controller reset/init and requires new validation | Selected |
| MCU reboot or Deep Sleep per frame | Disrupts identities/network, adds recovery/power behavior outside MVP | Rejected |

Create a small automatic H1 object inside the dedicated session function. The
15000-byte array remains static, not a member copied onto the stack. No heap object
churn, placement-new trick, state reset, copied controller sequence or library patch.
The global SPI object remains alive; destruction must not call end/powerOff/hibernate.

## 3. Selected session and acceptance

Preconditions: complete validated changed T, HTTP socket already closed, previous
session accepted or this is the first, application owns the immutable RAM contents.
Before EPD initialization configure only the guarded BUSY input and read it: HIGH
means FAULT_STOP, not a wait/retry. No SPI/reset/display initialization merely to
show a boot/network status; GPIO protection remains mandatory.

```text
validated T in static RAM, socket closed, BUSY idle
-> create fresh H1 object
-> SPI.begin with verified pins
-> coldInit(initial=true; fast-full disabled)
-> prepareColdStartFullFrame(15000, 0,0,400,300)
-> read BUSY; HIGH rejects before refresh
-> time refreshOnce()
-> read elapsed and BUSY
-> software accept OR FAULT_STOP
-> destroy object without EPD/SPI cleanup commands
```

Check coldInit/prepare return values, short-circuit on refusal. After preparation,
BUSY HIGH stops before refresh. If refresh is not invoked, BUSY is HIGH afterward,
or unsigned micros elapsed is >=10000000, classify TIMEOUT_OR_UNKNOWN and park.
Otherwise report SOFTWARE_RETURN_CONDITIONS_MET_NOT_PHYSICAL_PASS and advance
accepted identity. Never report runtime PHYSICAL_DISPLAY_VERIFIED.

Within a session: initialization and preparation request zero physical refreshes;
normal accepted path requests one standard FULL. These are static command-path
claims, not instrumented counts. Finite loops/geometry and upstream delays define
the preparation path; no arbitrary external cancellation or new watchdog reset
is added. The 10-second test measures refresh, not a hard preemptive deadline for
all SPI/MCU failures. A driver stall cannot be repaired safely by this design.

## 4. Session boundary versus failure boundary

After refresh, this session sends zero EPD commands on every result. No RAM rewrite,
clearScreen, writeImageAgain, powerOff, hibernate, partial, fast or retry.
After software acceptance only, release buffer and wait the full polling interval;
a later changed validated frame can create another session with new initialization.
Thus the new success-path boundary is per-session, not zero commands forever.

On display refusal/unknown, FAULT_STOP applies to the remainder of this boot:
no next session, request, reconnect, automatic reboot or identity promotion. The
socket is already closed before display; only application delays remain. Framework
Wi-Fi tasks/radio are not thereby proven off. Logs are diagnostic, not required
for correctness. No network success can clear the fault.

Rebuilding a software object is not hardware power cycling. Repeated reset/full
initialization, retained physical image, controller power behavior and endurance
are new E/F evidence requirements. If D/E reveals an unsafe constructor/destructor
side effect or unavailable API, stop and revisit C; do not patch H1 or dependencies.

## 5. Direction and observability

Keep invert=false, mirror_y=true, pgm=false. MCU neither reverses rows nor decodes
business data: Host L -> one PC reversal -> T -> fixed H1 -> P=L, as in
[orientation rule](STEP016D_ORIENTATION_RULE.md) and
[transport rule](STEP016D_B2A_TRANSPORT_FRAME_RULE.md).

Elapsed/BUSY acceptance cannot prove controller acknowledgement, correct physical
image, BUSY wiring correctness or absence of every fault. A BUSY stuck low can
produce false acceptance. There is no independent success feedback or rollback.
The selected conservative semantics are recorded in [LKG](STEP017C_FRAME_ACCEPTANCE_AND_LKG.md).
H0/H1 and offline PASS remain limited-scope historical evidence, not repeated-LAN PASS.
