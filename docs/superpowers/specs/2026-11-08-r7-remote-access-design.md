# R7 Remote Access — Design Spec

Date: 2026-11-08 (Asia/Shanghai)
Status: proposed; implementation starts only after this spec is approved and a plan exists.
Supersedes: nothing. R6 LAN OTA and the frame/device contracts are unchanged.

## 1. Goal

Let the operator open the existing `/manage` page from outside the home LAN — phone on
cellular, laptop on another network — to check device/page status, switch pages, edit
Memo/Course/Takeout, interact with the pet, switch weather cities and generate previews.

Constraints:

- The e-ink device stays LAN-first: it keeps using mDNS plus the LAN HTTP endpoint; no
  firmware, frame-format or polling change.
- No public port, no public hostname, no Funnel, no cloud rendering.
- The Host's management surface is not exposed beyond the home LAN and the private
  tailnet.

## 2. Verified facts

- `python -m server.main --host <IPv4> --port <port>` uses one address for both the
  uvicorn bind and the DNS-SD advertisement. `--host 127.0.0.1` (default) disables the
  advertisement; `0.0.0.0` is rejected by `HostAdvertisement`
  (`is_unspecified` → `ValueError`). See `server/main.py:619-642`,
  `services/host_discovery.py:29-32`.
- The device discovers `_eink-panel._tcp` and polls
  `GET /api/panels/progress/frame`; content changes return 200, unchanged polls 304.
  The Host currently runs as `--host 10.21.98.75 --port 8000`.
- `/manage` has no application login; all `/api/...` routes are open on the bind
  interface. OTA arm/disarm is disabled while the gitignored `config/firmware.json`
  does not exist (arm returns 503).
- Tailscale Serve proxies **only to `http://127.0.0.1`**
  ([CLI reference](https://tailscale.com/docs/reference/tailscale-cli/serve)).
- Serve over HTTPS requires HTTPS certificates to be enabled for the tailnet
  ([Serve docs](https://tailscale.com/docs/features/tailscale-serve),
  [HTTPS docs](https://tailscale.com/docs/how-to/set-up-https-certificates)).
- `--bg` makes a serve configuration persistent
  ([CLI reference](https://tailscale.com/docs/reference/tailscale-cli/serve)).
- Tailscale is not installed on the Host machine.

## 3. Scope

**In scope**

- A `--remote` Host flag that adds a second listener on `127.0.0.1` while the primary
  listener stays on the explicit LAN IPv4. Without the flag, startup is byte-for-byte
  the current behavior.
- Unit tests for the listen-address rule and the CLI error cases; full regression.
- A Tailscale Serve deployment: install the client on the Host and the phone, enable
  MagicDNS and HTTPS in the tailnet, serve the loopback listener, verify from cellular.
- A runbook `docs/R7-REMOTE-ACCESS.md`: install, enable HTTPS, start command, serve
  command, phone steps, ACL guidance, failure modes, rollback.
- Evidence, `PROJECT_STATE.md` section, `docs/GOALS.md` update, local commit.

**Out of scope**

- Device internet access, remote frame fetching, remote OTA, cloud rendering.
- Application login, sessions, multi-user accounts, per-route authorization.
- Public exposure (Funnel, port forwarding, public DNS), TLS termination in our code.
- Multi-device or multi-Host support; BLE/native app; R8.
- Any change to the frame contract, panels, page documents, OTA offer or firmware.

## 4. Host change: dual listen

### 4.1 CLI

```
python -m server.main --host 10.21.98.75 --port 8000 --remote
```

- `--remote` is a boolean flag, default off.
- Listen addresses are computed by one pure helper, `listen_addresses(host, remote)`:

| `--host` | `--remote` | Listener addresses | Advertisement |
| --- | --- | --- | --- |
| `127.0.0.1` (default) | off | `127.0.0.1` | none (unchanged) |
| unicast LAN IPv4 | off | that address | that address (unchanged) |
| unicast LAN IPv4 | on | that address **and** `127.0.0.1` | that address (unchanged) |
| `127.0.0.1` | on | error: `--remote requires a non-loopback --host` | — |
| `0.0.0.0` / multicast / broadcast | on | error before binding: `--remote requires a unicast LAN IPv4` | — |
| `0.0.0.0` / multicast / broadcast | off | existing startup error from `HostAdvertisement` (unchanged) | — |

- `--port` applies to both listeners; the port range check is unchanged.
- Advertisement code is untouched: it still receives the LAN IPv4 and announces every
  1 s.

### 4.2 Startup

- Create one `AF_INET`/`SOCK_STREAM` socket per listen address with `SO_REUSEADDR`,
  `bind((address, port))` and `listen(...)`, then hand both sockets to one
  `uvicorn.Server(...).run(sockets=[...])` so a single process, lifespan and app state
  serve both interfaces. Two small functions carry this: `listen_addresses(host, remote)`
  (pure decision) and `bind_listeners(addresses, port)` (socket creation; closes what it
  created if a later bind fails).
- If any bind fails, close the sockets already created and exit non-zero with one
  `logger.error` line naming the address and port; no partial server.
- No new endpoint, no change to `/api/pages/*`, `/api/panels/*`, static files, page
  state, mDNS payload or logs other than the startup line below.
- One INFO line at startup: `Host listening on <addr:port>[, <addr:port>]` (no
  credentials, no tailnet name).

### 4.3 What stays exactly as today

- `/manage`, page APIs, frame GET, device report, preview, weather/pet/calendar/codex
  behaviour, `data/pages/` documents, selection file, OTA endpoints and all status
  bodies.
- Default startup (`--host` omitted or loopback) publishes no advertisement and binds
  only loopback.

## 5. Remote access deployment (Tailscale)

All steps below are operator actions performed with explicit approval; the repo only
documents them.

1. Install Tailscale on the Windows Host and sign in to the operator's tailnet (needs
   admin approval). Install the Tailscale app on the phone and sign in to the same
   tailnet.
2. In the tailnet admin console, enable MagicDNS and HTTPS certificates.
3. Start the Host with `--host <LAN IPv4> --port 8000 --remote`. Confirm the device
   still polls 200/304 and mDNS still advertises the LAN IPv4.
4. Expose only the loopback listener:

   ```
   tailscale serve --bg --https=443 127.0.0.1:8000
   tailscale serve status
   ```

   The status output must show `https://<host>.<tailnet>.ts.net` proxying to
   `http://127.0.0.1:8000`. If the installed CLI rejects this spelling, adjust only the
   argument form after checking `tailscale serve --help` and record the exact command
   in the runbook and evidence. Do not use Funnel and do not add a second target.
5. On the phone, turn Wi-Fi off (cellular only), open
   `https://<host>.<tailnet>.ts.net/manage`, and run the acceptance checks in §9.
6. Optional: install the PWA from the HTTPS origin. The LAN HTTP origin and the
   `ts.net` HTTPS origin keep separate service-worker caches; this is expected.

No firewall rule is added by this spec. Tailscale creates its own adapter/rules at
install time; the LAN listener already works today. If Windows prompts for a firewall
decision, stop and ask before allowing.

## 6. Security model

- **Identity is tailnet membership.** Anyone who can join the tailnet and is allowed by
  its ACL can reach `/manage`; there is no application login. The recommended ACL is
  "only the operator's devices may reach TCP 443 of this Host"; document it, do not
  automate it.
- The Host never binds `0.0.0.0` and never binds the Tailscale IP. Remote traffic can
  only arrive through `tailscale serve` → `127.0.0.1`. Direct `http://100.x:8000` is
  not reachable.
- Funnel is not used, so the `ts.net` name is not reachable from the public internet.
- OTA stays disabled: keep `config/firmware.json` absent during R7 acceptance so
  `/api/device/firmware/*` returns 503. If firmware offering is configured later, a
  tailnet device can arm an update; that is equivalent to LAN membership and must be
  covered by the ACL. R7 does not add remote OTA.
- No credentials, tailnet names or tokens are written to the repo, logs or evidence.
  The Host logs only the listen addresses.
- The e-ink device does not join the tailnet and keeps no new secrets.

## 7. Failure handling

| Situation | Behaviour | Operator step |
| --- | --- | --- |
| Tailscale stopped / logged out | Remote URL fails; LAN `/manage` and device polling unaffected | Restart Tailscale; no Host restart needed |
| HTTPS certs not enabled | `tailscale serve --https` fails; no TLS name | Enable HTTPS in admin console, or fall back to tailnet HTTP (no PWA install) and record it |
| LAN IPv4 changes | mDNS and direct LAN access break as today; serve still points at loopback but the Host is bound to the old IP | Restart Host with the new `--host`; keep `--remote` |
| `--remote` bind fails (port in use) | Process exits non-zero after closing sockets | Free the port or change `--port`; do not silently drop a listener |
| Company VPN / policy conflict | Remote access may not establish; do not disable or reconfigure the VPN | Stop R7 verification and report |
| Tailnet device lost/compromised | Full management access | Remove the device from the tailnet; no Host change |

## 8. Tests

Host-side automated tests (pytest, no network):

1. `listen_addresses("127.0.0.1", False) == ["127.0.0.1"]`.
2. `listen_addresses("10.21.98.75", False) == ["10.21.98.75"]` (backward compatible).
3. `listen_addresses("10.21.98.75", True) == ["10.21.98.75", "127.0.0.1"]`.
4. `listen_addresses("127.0.0.1", True)` raises `ValueError("--remote requires a
   non-loopback --host")`.
5. `listen_addresses("0.0.0.0", True)` raises
   `ValueError("--remote requires a unicast LAN IPv4")`; the existing `--port` range
   check still runs before any socket is created.
6. `bind_listeners(["127.0.0.1", "127.0.0.1"], 0)` creates two listening sockets on
   the same ephemeral port, reports the bound port, and closes both in the test
   (no uvicorn process is started).
7. Existing CLI tests for `--host`/`--port` keep passing; no existing test changes its
   expectation.

Full regression: Python suite and frontend Node suite green; no new production
dependency.

## 9. Acceptance criteria

- **A1 — Default unchanged.** Start without `--remote`: only the LAN listener exists,
  mDNS advertises the LAN IPv4, the device polls 200/304, and `/manage` over LAN works
  as before.
- **A2 — Dual listen.** Start with `--remote`: two listening sockets on the same port
  (LAN IPv4 and `127.0.0.1`), advertisement still the LAN IPv4, device still 200/304
  with no extra refresh.
- **A3 — Remote management.** With phone Wi-Fi off, `https://<host>.<tailnet>.ts.net/manage`
  loads; switching a page produces one device 200 (refresh count +1) and the next poll
  304; a memo save and a frame preview succeed; the preview version equals the served
  ETag.
- **A4 — OTA remains closed.** `GET /api/device/firmware/status` reports
  `configured: false`; `POST /api/device/firmware/arm` returns 503; no firmware config
  is added.
- **A5 — No unapproved system change.** Only the two approved Tailscale installs and
  the tailnet HTTPS toggle; no firewall edit, no company-VPN change, no Host
  service/registry change beyond Tailscale's own installer.
- **A6 — Recorded.** `docs/R7-REMOTE-ACCESS.md`, a `PROJECT_STATE.md` section, a
  `docs/GOALS.md` update, and evidence under
  `D:/Codex/round2-r7-20261108/acceptance/` (remote page, page switch, serve status,
  LAN regression, OTA 503). No credentials in any file.

## 10. Limits

- Trust is still LAN + tailnet, not internet-wide; no application authentication.
- Tailscale is a third-party dependency with its own account, client and updates;
  phone battery and always-on VPN behaviour are outside this project.
- HTTPS availability depends on the tailnet's MagicDNS/certificate settings.
- One Host, one tailnet, one operator; no multi-user, no audit log of remote actions.
- Remote access adds no reliability guarantee: if the Host or the phone's Tailscale
  is down, the remote page is unavailable while the device keeps its last frame.

## 11. Rollback

- Stop the Host and restart without `--remote`; LAN behavior is identical to today.
- `tailscale serve --https=443 off` (verify the exact disable form with `--help`); the
  tailnet name stops responding, LAN and device polling are unaffected.
- Uninstalling Tailscale is optional and does not touch page data, firmware or the
  device.

## 12. Decision log

- 2026-11-08: R7 target is remote management of the Host, not device remote fetch,
  cloud rendering or remote OTA (operator decision).
- 2026-11-08: Access is a private Tailscale overlay, not Cloudflare Tunnel, a
  self-hosted WireGuard VPS or public exposure (operator decision).
- 2026-11-08: Dual listen (`--remote` adds loopback) rather than binding `0.0.0.0`,
  because Serve proxies to loopback only and `0.0.0.0` would expose the management
  page on every network the machine joins (operator decision).
