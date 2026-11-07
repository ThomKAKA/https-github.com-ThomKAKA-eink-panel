# STEP017 State Reconciliation

Status: state reconciliation COMPLETE; STEP017D closure remains NO-GO.
This is a document-only reconciliation, not C-R1, D-R1 or E execution.

## 1. Why reconciliation was required

The prior expected baseline was `5371460e01b38b9ec4f54438b74cf23d7691dc04`
(STEP017C design freeze). A subsequent audit found the D implementation already
committed, while PROJECT_STATE still called it NOT RUN and uncommitted.
The closure's three blockers remain present. A commit is a saved implementation,
not approval, completion, build verification or authorization to enter E.

Initial actual HEAD: `239411582893d05b70fbb5f0d571c078201f5216`.
Parent: `5371460e01b38b9ec4f54438b74cf23d7691dc04`.
Message: `feat(network): freeze STEP017D ESP32 fetcher implementation`.
There is one commit between the prior baseline and this initial HEAD.
Initial index empty; tracked worktree clean; only `?? hardware/evidence/`.
The reconciliation commit will be a successor, not the implementation commit.

## 2. Implementation commit scope

Eight files, 688 inserted lines:

- Modified `PROJECT_STATE.md`.
- Added `hardware/gdey042t81_esp32/docs/STEP017D_NETWORK_FETCHER_IMPLEMENTATION_REPORT.md`.
- Modified `hardware/gdey042t81_esp32/platformio.ini` (dedicated network environment).
- Added `hardware/gdey042t81_esp32/src/network_progress/config.h`.
- Added `hardware/gdey042t81_esp32/src/network_progress/machine.h`.
- Added `hardware/gdey042t81_esp32/src/network_progress/main.cpp`.
- Added `hardware/gdey042t81_esp32/src/network_progress/protocol.h`.
- Added `tests/cpp/test_network_progress.cpp`.

These files are tracked. The [implementation report](STEP017D_NETWORK_FETCHER_IMPLEMENTATION_REPORT.md)
is preserved verbatim: "No commit" and "no commit created" refer to its generation
time, not the subsequent Git history. No approval is inferred from the commit message.

## 3. Closure blockers

All three are PRESENT in the committed implementation and local fixed framework.
The framework paths below are local dependency-cache evidence, not submitted files.

| Blocker | Source evidence | Effect |
|---|---|---|
| Wi-Fi reconnect ownership assumption mismatch | `src/network_progress/main.cpp:20-24` calls setAutoReconnect(false); `.venv-hw/pio-core/packages/framework-arduinoespressif32/libraries/WiFi/src/WiFiGeneric.cpp:1079-1093` has a first_connect retry independent of getAutoReconnect() | Application ownership of every Wi-Fi attempt is not established; C-R1 contract amendment required |
| CONFIG_INVALID / WIFI_INIT_FAILURE conflation | `src/network_progress/main.cpp:20-24` returns false for both configuration and WiFi.mode failure; `src/network_progress/machine.h:46-48` sends both to FAULT_STOP | Failure classification and later D remediation required |
| Socket cleanup guarantee gap | `.venv-hw/pio-core/packages/framework-arduinoespressif32/libraries/WiFi/src/WiFiClient.cpp:281-290` returns from failed setsockopt before handle ownership; stop at lines 209-214 only releases existing handles; `src/network_progress/main.cpp:29-38` uses connect/stop | Cannot claim all failure paths are application-cleaned; C-R1 transport ownership amendment required |

Project `src/` paths above are relative to `hardware/gdey042t81_esp32/`;
`.venv-hw/` paths are relative to the repository root. Findings are source-level,
not measured runtime failure frequency or fault-injection results.
No reconnect, transport or failure-classification replacement is selected here.

## 4. State conflicts corrected

In [PROJECT_STATE](../../../PROJECT_STATE.md), current sections 2, 7 and 11
previously described D implementation as NOT RUN, while section 18 said IMPLEMENTED.
Section 18 also said uncommitted after Git had recorded the implementation.
The current product summary, next stage and missing closure blockers needed alignment.

Current summaries and section 18 now distinguish implementation presence from
approval and verification. Section 13 records C/D commits. Section 17 is explicitly
the preserved C-freeze historical record; its then-current NOT RUN/next-stage
statements are not current instructions. A/B and STEP016 historical results remain
historical; NOT RUN text is not mechanically replaced. The D report is not rewritten.

## 5. Reconciled stage status

| Item | Current status |
|---|---|
| STEP016D-C physical business page | PASS (limited scope) |
| STEP016D-C evidence closure | COMPLETE |
| STEP017A architecture / STEP017B Host / STEP017C original design freeze | COMPLETE |
| Host endpoint | IMPLEMENTED AND SOFTWARE TESTED; historical B results, not rerun |
| STEP017D implementation | PRESENT; committed at `239411582893d05b70fbb5f0d571c078201f5216` |
| STEP017D closure / approved | NO-GO / NO |
| STEP017D compile / runtime / physical verified | NO / NOT RUN for each |
| STEP017C-R1 transport assumption amendment | NOT RUN; next actionable stage |
| STEP017D-R1 remediation | NOT READY; requires C-R1 freeze first |
| STEP017E software/compile verification | NOT READY; blockers unresolved |
| Physical LAN update | NOT RUN |
| NETWORK PRODUCT FUNCTION VERIFIED | NO |

Current factual stage: STEP017D IMPLEMENTATION PRESENT, CLOSURE NO-GO.
Unique next actionable stage: STEP017C-R1 NETWORK TRANSPORT ASSUMPTION AMENDMENT.
This reconciliation does not start or authorize that next stage.

## 6. Protected history and execution limits

H0 PASS, H1 PASS (limited scope), and STEP016 offline product PASS (limited scope)
are preserved. BUSY timeout fault injection, Deep Sleep, Partial Refresh,
Fast Refresh and long-duration operation remain NOT TESTED. Exact physical FULL
invocation count remains NOT independently verified. No new network product PASS.

Only PROJECT_STATE and this reconciliation document may change. Source, tests,
PlatformIO, A/B/C/STEP016 documents, the D report, GxEPD2, framework files and raw
evidence remain untouched. Evidence stays local-only and untracked.

Tests: NOT RUN. Compile/link: NOT RUN. Runtime network: NOT RUN. Hardware: NOT RUN.
Only document consistency, local links, sensitive-content and Git diff/scope checks.
No pytest, C++ tests, builds, Wi-Fi/HTTP execution, upload or serial/COM access.

Local commit message: `docs(project): reconcile STEP017D closure state`.
Resolve its actual SHA from Git history; no self-referential hash is embedded here.
No push/tag. Stop after state reconciliation, before C-R1, D-R1 or E.
