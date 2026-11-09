# R3D multi-network Wi-Fi — operator runbook

Date: 2026-11-09. Spec: `docs/superpowers/specs/2026-11-09-r3d-multi-network-design.md`
(commit `b619271`). Plan: `docs/superpowers/plans/2026-11-09-r3d-multi-network.md`
(commit `df8ffb4`). Implementation: `df8ffb4..95848a2`.

```
SOFTWARE = COMPLETE (builds and host suites PASS)
BUILD IDENTITY = round2-r3d-1 (both envs; EINK_FIRMWARE_VERSION)
DEVICE ACCEPTANCE = NOT RUN (flashing not authorized)
DEPLOYMENT = unchanged (device still runs the last accepted image, round2-r6-3)
```

This is a runbook, not evidence. Nothing below counts as PASS until an operator authorizes
flashing and records the results in the acceptance directory.

## 1. What the feature does

- The device stores up to three Wi-Fi networks (`networks`, 301 B, version 1) in the existing
  `eink-wifi` NVS namespace. Each slot is SSID 32 + NUL and password 64 + NUL, fixed length,
  no dynamic allocation.
- Selection per connect cycle: the last successful slot first, then the remaining used slots in
  storage order, skipping empty or invalid entries. An empty store falls back to the compiled
  credentials as before.
- Each attempt reuses the existing 15 s association budget; at most three attempts, so one cycle
  is ≤45 s. After exhaustion the existing 60 s retry loop starts again from the last successful
  slot, keeping the last good frame (LKG). An idle link drop is noticed at the next poll, so
  recovery after a drop is ≤60 s + 45 s.
- Provisioning success writes the new pair into the store, sets it as the preferred slot and
  dual-writes the same pair to the legacy `validated` key for rollback.
- Migration: an existing `validated` pair becomes slot 0 on first boot of this firmware, with one
  write, and only while the `networks` key is still absent; a failed write is simply retried on
  the next boot (the key is still absent). A present but malformed `networks` blob is not
  migrated and is never overwritten by the load path; the firmware falls back to `validated`,
  then to the compiled pair.

## 2. Add or update a network

1. Hold S1 until the device enters provisioning; it starts the open AP `eink-panel-setup`.
   The station link is left as-is until a candidate is submitted. Same behaviour as before
   this change.
2. Join `eink-panel-setup` from a phone or laptop and open `http://192.168.4.1/`.
3. The page shows result text, the saved networks (index + SSID + one **Forget** button each;
   no password is ever rendered), and the **Add or update** form.
4. Enter SSID and password, press **Connect and save**. The device runs a 15 s candidate.
   Nothing is written before the candidate succeeds.
5. On success the device joins the candidate, saves it (new row, or the existing row's password
   replaced by exact, case-sensitive SSID) and closes the setup AP, so the browser loses the
   page. Seeing the saved list again requires entering provisioning again (S1); the success page
   is not reachable over the closed AP. On failure the setup page becomes reachable again and the
   previous store is unchanged in the common failure paths; a failure after the store write
   (legacy `validated` save, or the SoftAP stop) can leave the new list persisted, and the code's
   restore write of the old blob is best-effort.
6. Record: how many rows the list shows, and that the device kept its current frame —
   provisioning alone does not refresh the display.
7. A `409` (store full) answer is plain text, not the setup page. Open `http://192.168.4.1/`
   again to see the unchanged list, forget a row, then add again.

## 3. Forget a network

1. Enter the setup AP as in section 2.
2. Press **Forget** on the row to remove. The form posts `index=0..2` (no credential in the URL).
3. The device refuses while a connection candidate is pending; it then compacts the remaining
   slots in order and adjusts the preferred slot (removed below it: shift down; removed slot:
   back to 0) and persists. It does not auto-connect. The device stays in `Provisioning` with the
   setup AP still open, and there is no automatic retry, so S1 cannot exit this state. The exits
   are a successful `/configure` (a candidate that joins) or a power-cycle (the next boot selects
   from the new list).
4. `validated` is deliberately untouched, so a rollback image still has one pair to join.

## 4. Full store (409)

Adding a fourth network while three are stored returns HTTP 409 with
"Store full; forget one network first."; nothing is written and the list is unchanged. The 409
body is plain text, so reopen `http://192.168.4.1/` to see the list. Forget a
row, then add again. Updating the password of an SSID already in the list is allowed while full.

## 5. Expected failover (to verify after authorization)

Precondition: the Host must stay reachable for the whole test, so put it on a third network, or
on a network that both stored device networks can reach. If the Host sits on the device's active
AP, turning that AP off cuts the Host too and no failover timeline can be observed.

1. With two networks stored, reboot; the device joins the last successful one. Read the request
   status (`200`, then `304`) from the Host access log, and the `15000` byte body plus the `ETag`
   header from `curl -D - -o /dev/null http://<host>:8000/api/panels/progress/frame` (a `-v`
   capture or a reverse-proxy log works the same way); the `ETag` is the SHA-256 of the frame.
   `/api/pages/status` does not show per-request status, body size or `ETag`; use it only for
   `frame_version` (the published frame's SHA-256) and `device.last_seen` /
   `device.refresh_count`.
2. Turn that AP off. The next poll notices the drop and the device advances to the other stored
   network within one poll plus the fallback (≤60 s + 45 s), fetches the current frame
   (200, 15000 B, `ETag` = SHA-256) and the next poll is 304.
3. `refresh_count` increases once on the first accepted frame after every boot — the accepted
   ETag lives in RAM only, so the first 200 always refreshes — and then once per content change.
   304 polls and Wi-Fi associations add nothing.
4. Record, with SSIDs masked as `net-a` / `net-b`: boot preference result, the failover timeline,
   HTTP statuses and byte counts, ETags before and after, `refresh_count` values, and the serial
   boot lines `NETWORK_WIFI_STORE=301 HEAP=<n>` and
   `NETWORK_NVS used=<n> free=<n> total=<n>`.

## 6. Rollback

1. Every successful provisioning writes both `networks` and `validated`, so the previous firmware
   (which reads only `validated`) still joins one network.
2. The last accepted image is `round2-r6-3` (commit `9636407`, tracked env
   `esp32-m1-network-progress-ota-r6-3`). Its artifact is not in this tree: rebuild it from the R6
   stage config with the r6-3 version flag, or use the separately authorized OTA path. The
   `round2-r6-ota-20261107` artifact is not r6-3 — it reports `round2-r6-2` — so do not present
   it as the rollback image.
3. If the new firmware fails acceptance, reflash that image (USB or a separately authorized OTA)
   and record the result. Do not erase NVS and do not change the partition table to "clean up".
4. A forgotten network can reappear on the rollback image, because `validated` is rollback data
   and is not a mirror of the list. That is expected, not a bug.
5. Record: the image identifier reflashed, that the device obtained an IP and polled (200 → 304),
   and the `NETWORK_NVS` line after the rollback.

## 7. Security rules

- Passwords never appear in evidence, screenshots, serial logs, commit messages or the repo.
  The setup page never renders a stored password and never echoes the submitted one.
- SSIDs are masked in committed text (`net-a`, `net-b`, `net-c`); the serial log prints counts
  and sizes, not credentials.
- The build-time network lives in the untracked private header; do not copy it into docs,
  tests or `config/`.
- `validated` is rollback data. Forget does not touch it, and the new firmware stops reading it
  once a valid `networks` store exists.
- No tailnet name, account or Host credential belongs in these documents.

## 8. Limits

- One active link at a time; the other stored networks are idle. No AP+STA concurrency outside
  the provisioning window.
- No NVS erase, no partition change, no store format change in this stage; the store is 301 B
  of the existing `eink-wifi` namespace.
- At most three networks, no priority editing, no scanning UI, no per-network static IP; order is
  storage order with last-success first.
- The setup AP has no password by design; the physical S1 button is the only gate. Do not leave
  provisioning open in an untrusted place.
- Up to 45 s before the first frame poll when every network fails, once per 60 s cycle; ≤105 s
  after an idle drop.
- All device-side items in this runbook are NOT RUN until flashing is authorized; the evidence
  directory `D:/Codex/round2-r3d-20261109/acceptance/` records that state.
