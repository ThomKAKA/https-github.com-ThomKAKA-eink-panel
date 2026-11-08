# R7 Remote Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the operator open the existing `/manage` page from a phone on cellular through a private Tailscale Serve HTTPS URL, while the LAN IP listener, mDNS advertisement and the e-ink device keep working unchanged.

**Architecture:** Add a `--remote` flag to the Host that binds a second listener on `127.0.0.1` (same port, same app, one uvicorn server) next to the existing LAN IPv4 listener. Tailscale Serve proxies its tailnet HTTPS name to that loopback listener; the device is untouched. Without the flag, startup stays exactly as today.

**Tech Stack:** Python 3, FastAPI/uvicorn 0.35.0, pytest 8.4.1, zeroconf; Tailscale client + Serve (manual deployment).

**Spec:** `docs/superpowers/specs/2026-11-08-r7-remote-access-design.md`

## Global Constraints

- Default startup (`--host` omitted or loopback) must behave exactly as today: one listener, no advertisement, no Tailscale requirement.
- Never bind `0.0.0.0`, multicast or broadcast. Remote mode requires a unicast non-loopback `--host`.
- Without `--remote`, the setup path must remain `uvicorn.run(app, host=str(address), port=options.port, reload=False)`; do not refactor it.
- No new runtime dependency. No endpoint, frame, page document, OTA or firmware change.
- No application login is added; identity is tailnet membership. Keep `config/firmware.json` absent so OTA arm stays 503.
- Nothing secret (Wi-Fi credentials, tokens, tailnet name) may appear in code, logs, docs, commits or evidence. Redact the `*.ts.net` name in evidence.
- No firewall edit, no company-VPN change, no Windows security change. Tailscale installs happen only after explicit operator approval.
- Every manual/physical step that is blocked must be recorded as BLOCKED/NOT RUN; never claim PASS from code existence.
- Test command (Windows, Git Bash):
  `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest <paths> -q`
- Frontend command: `node --test tests/frontend`
- Worktree: `C:/Users/cslki/.codex/worktrees/a5b3/eink-panel` (run every command there).

## File Structure

| File | Responsibility |
| --- | --- |
| `services/remote_listen.py` (new) | Pure listen-address decision and socket binding for one or two listeners. No FastAPI, no uvicorn. |
| `server/main.py` (modify `main()` only) | Parse `--remote`; build the advertisement from the LAN address; either keep the legacy `uvicorn.run` path or bind both sockets and run one `uvicorn.Server`. |
| `tests/test_remote_listen.py` (new) | Address matrix, error messages, socket binding and cleanup. |
| `tests/test_remote_cli.py` (new) | `main()` wiring for default, remote, invalid and bind-failure cases. |
| `docs/R7-REMOTE-ACCESS.md` (new) | Operator runbook: install, HTTPS, serve, phone steps, ACL, failure modes, rollback, evidence checklist. |
| `PROJECT_STATE.md`, `docs/GOALS.md` (modify) | Record R7A software result and acceptance (or BLOCKED). |
| `D:/Codex/round2-r7-20261108/acceptance/` (new, outside repo) | Evidence: netstat, serve status, LAN regression, remote checks, OTA 503. |

---

### Task 1: Listen-address decision

**Files:**
- Create: `services/remote_listen.py`
- Test: `tests/test_remote_listen.py`

**Interfaces:**
- Produces: `listen_addresses(host: str, remote: bool) -> list[str]`
  - `remote=False` → `[<host>]` for any valid IPv4 string.
  - `remote=True` + loopback → `ValueError("--remote requires a non-loopback --host")`.
  - `remote=True` + unspecified/multicast/broadcast → `ValueError("--remote requires a unicast LAN IPv4")`.
  - `remote=True` + unicast LAN IPv4 → `[<host>, "127.0.0.1"]`.

- [ ] **Step 1: Write the failing test**

```python
"""Remote listener address rules; no sockets are opened in this file yet."""

from __future__ import annotations

import pytest

from services.remote_listen import listen_addresses


def test_default_and_lan_startup_keep_one_address():
    assert listen_addresses("127.0.0.1", False) == ["127.0.0.1"]
    assert listen_addresses("10.21.98.75", False) == ["10.21.98.75"]


def test_remote_adds_loopback_after_the_lan_address():
    assert listen_addresses("10.21.98.75", True) == ["10.21.98.75", "127.0.0.1"]


def test_remote_rejects_loopback_host():
    with pytest.raises(ValueError, match="--remote requires a non-loopback --host"):
        listen_addresses("127.0.0.1", True)


@pytest.mark.parametrize("host", ["0.0.0.0", "224.0.0.251", "255.255.255.255"])
def test_remote_rejects_non_unicast_host(host):
    with pytest.raises(ValueError, match="--remote requires a unicast LAN IPv4"):
        listen_addresses(host, True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest tests/test_remote_listen.py -q`
Expected: FAIL / collection error: `ModuleNotFoundError: No module named 'services.remote_listen'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Loopback listener for Tailscale Serve, next to the existing LAN listener."""

from __future__ import annotations

from ipaddress import IPv4Address

LOOPBACK = "127.0.0.1"
BROADCAST = 0xFFFFFFFF


def listen_addresses(host: str, remote: bool) -> list[str]:
    """Return the addresses uvicorn must bind for this startup."""
    address = IPv4Address(host)
    if not remote:
        return [str(address)]
    if address.is_loopback:
        raise ValueError("--remote requires a non-loopback --host")
    if address.is_unspecified or address.is_multicast or int(address) == BROADCAST:
        raise ValueError("--remote requires a unicast LAN IPv4")
    return [str(address), LOOPBACK]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest tests/test_remote_listen.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add services/remote_listen.py tests/test_remote_listen.py
git commit -m "feat(host): add the remote listen-address rule"
```

---

### Task 2: Socket binder

**Files:**
- Modify: `services/remote_listen.py`
- Test: `tests/test_remote_listen.py`

**Interfaces:**
- Produces: `bind_listeners(addresses: Sequence[str], port: int, *, sock_factory: Callable[..., socket.socket] = socket.socket) -> tuple[list[socket.socket], int]`
  - Binds every address on the same port; with `port=0`, the first bind picks the ephemeral port and the rest reuse it.
  - On any binding exception, closes every socket created so far and re-raises.
  - Rejects an empty address list and a port outside `0..65535`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_remote_listen.py` (extend the existing imports with
`import socket` and `from services.remote_listen import bind_listeners`):

```python
def test_bind_listeners_share_one_ephemeral_port():
    sockets, port = bind_listeners(["127.0.0.1", "127.0.0.2"], 0)
    try:
        assert port > 0
        assert len(sockets) == 2
        assert {sock.getsockname() for sock in sockets} == {
            ("127.0.0.1", port),
            ("127.0.0.2", port),
        }
        for sock in sockets:
            assert sock.fileno() != -1
    finally:
        for sock in sockets:
            sock.close()


def test_bind_listeners_closes_earlier_sockets_when_a_bind_fails():
    created = []

    def factory(family, type_):
        sock = socket.socket(family, type_)
        created.append(sock)
        return sock

    with pytest.raises(OSError):
        bind_listeners(["127.0.0.1", "192.0.2.1"], 0, sock_factory=factory)
    assert len(created) == 2
    assert all(sock.fileno() == -1 for sock in created)


@pytest.mark.parametrize("addresses,port", [([], 8000), (["127.0.0.1"], -1), (["127.0.0.1"], 65536)])
def test_bind_listeners_rejects_invalid_arguments(addresses, port):
    with pytest.raises(ValueError):
        bind_listeners(addresses, port)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest tests/test_remote_listen.py -q`
Expected: FAIL — `ImportError: cannot import name 'bind_listeners'`.

- [ ] **Step 3: Implement the binder**

Extend the import block at the top of `services/remote_listen.py` to:

```python
import socket
from ipaddress import IPv4Address
from typing import Callable, Sequence
```

Then append the binder:

```python
def bind_listeners(
    addresses: Sequence[str],
    port: int,
    *,
    sock_factory: Callable[..., socket.socket] = socket.socket,
) -> tuple[list[socket.socket], int]:
    """Bind every address on one port and return the listening sockets."""
    if not addresses:
        raise ValueError("At least one listen address is required")
    if not 0 <= port <= 65535:
        raise ValueError("HTTP port must be between 0 and 65535")
    created: list[socket.socket] = []
    bound_port = port
    try:
        for address in addresses:
            sock = sock_factory(socket.AF_INET, socket.SOCK_STREAM)
            created.append(sock)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((address, bound_port))
            sock.listen(128)
            if bound_port == 0:
                bound_port = sock.getsockname()[1]
    except BaseException:
        for sock in created:
            sock.close()
        raise
    return created, bound_port
```

- [ ] **Step 4: Run the tests**

Run: `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest tests/test_remote_listen.py -q`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add services/remote_listen.py tests/test_remote_listen.py
git commit -m "feat(host): bind the LAN and loopback listeners"
```

---

### Task 3: `--remote` CLI wiring

**Files:**
- Modify: `server/main.py` (`main()` around lines 619-646, plus the import block near line 36)
- Test: `tests/test_remote_cli.py`

**Interfaces:**
- Consumes: `listen_addresses(host, remote)` and `bind_listeners(addresses, port)` from Task 1/2.
- Produces: `main(argv=None) -> int` (0 on success, 1 on bind failure); `if __name__ == "__main__": raise SystemExit(main())`.
- Unchanged: advertisement is constructed from the `--host` value, never from the listen list.

- [ ] **Step 1: Write the failing tests**

```python
"""Host CLI wiring for --remote; uvicorn and sockets are mocked."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import uvicorn

import server.main as server


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    monkeypatch.setattr(server.app.state, "host_advertisement", None, raising=False)


def test_default_startup_still_calls_uvicorn_run(monkeypatch):
    listener = Mock()
    monkeypatch.setattr(uvicorn, "run", listener)
    bind = Mock()
    monkeypatch.setattr(server, "bind_listeners", bind)

    assert server.main(["--host", "192.168.1.23", "--port", "8000"]) == 0
    listener.assert_called_once()
    assert listener.call_args.args == (server.app,)
    assert listener.call_args.kwargs == {"host": "192.168.1.23", "port": 8000, "reload": False}
    bind.assert_not_called()


def test_remote_binds_both_addresses_and_runs_one_server(monkeypatch):
    sockets = [Mock(name="lan"), Mock(name="loopback")]
    bind = Mock(return_value=(sockets, 8000))
    monkeypatch.setattr(server, "bind_listeners", bind)
    config = Mock()
    monkeypatch.setattr(uvicorn, "Config", Mock(return_value=config))
    server_type = Mock()
    monkeypatch.setattr(uvicorn, "Server", server_type)
    listener = Mock()
    monkeypatch.setattr(uvicorn, "run", listener)

    assert server.main(["--host", "192.168.1.23", "--remote"]) == 0
    bind.assert_called_once_with(["192.168.1.23", "127.0.0.1"], 8000)
    server_type.assert_called_once_with(config)
    server_type.return_value.run.assert_called_once_with(sockets=sockets)
    listener.assert_not_called()
    assert server.app.state.host_advertisement.address == "192.168.1.23"


def test_remote_with_loopback_host_exits_with_usage_error(monkeypatch, capsys):
    listener = Mock()
    monkeypatch.setattr(uvicorn, "run", listener)
    with pytest.raises(SystemExit) as exit_info:
        server.main(["--host", "127.0.0.1", "--remote"])
    assert exit_info.value.code == 2
    assert "--remote requires a non-loopback --host" in capsys.readouterr().err
    listener.assert_not_called()


def test_bind_failure_returns_nonzero_without_starting(monkeypatch, caplog):
    monkeypatch.setattr(server, "bind_listeners", Mock(side_effect=OSError("in use")))
    server_type = Mock()
    monkeypatch.setattr(uvicorn, "Server", server_type)

    assert server.main(["--host", "192.168.1.23", "--remote"]) == 1
    server_type.assert_not_called()
    assert "in use" in caplog.text
    assert "192.168.1.23" in caplog.text and "8000" in caplog.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest tests/test_remote_cli.py -q`
Expected: FAIL — `--remote` is an unrecognized argument and `bind_listeners` does not exist on `server.main`.

- [ ] **Step 3: Implement the wiring**

Add the import next to the other service imports in `server/main.py`:

```python
from services.remote_listen import bind_listeners, listen_addresses
```

Replace the whole `def main(argv=None):` function with exactly:

```python
def main(argv=None):
    import uvicorn

    parser = argparse.ArgumentParser(description="E-Ink Host HTTP server")
    parser.add_argument("--host", default="127.0.0.1", help="Explicit bind IPv4; LAN binding advertises discovery")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Also listen on 127.0.0.1 for Tailscale Serve",
    )
    options = parser.parse_args(argv)
    address = IPv4Address(options.host)
    if not 1 <= options.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    try:
        addresses = listen_addresses(str(address), options.remote)
    except ValueError as error:
        parser.error(str(error))
    app.state.host_advertisement = (
        None if address.is_loopback else HostAdvertisement(str(address), options.port)
    )
    weather_config = None if os.environ.get("EINK_WEATHER") == "0" else load_weather_config()
    if weather_config is None:
        app.state.weather_source = None
        app.state.weather_scheduler = None
    else:
        app.state.weather_source = WeatherSource(page_state, weather_config)
        app.state.weather_scheduler = WeatherScheduler(app.state.weather_source)
    app.state.codex_watchdog = (
        None if os.environ.get("EINK_CODEX") == "0" else CodexUsageService(page_state)
    )
    if not options.remote:
        logger.info("Host listening on %s:%s", address, options.port)
        uvicorn.run(app, host=str(address), port=options.port, reload=False)
        return 0
    try:
        sockets, bound_port = bind_listeners(addresses, options.port)
    except OSError as error:
        logger.error(
            "Host bind failed on %s:%s: %s",
            ", ".join(addresses),
            options.port,
            error,
        )
        return 1
    logger.info(
        "Host listening on %s",
        ", ".join(f"{listen}:{bound_port}" for listen in addresses),
    )
    try:
        uvicorn.Server(uvicorn.Config(app, port=bound_port, reload=False)).run(
            sockets=sockets
        )
    finally:
        for sock in sockets:
            sock.close()
    return 0
```

Update the module tail:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

Do not change the existing `--host`/`--port` help text or the advertisement construction address.

- [ ] **Step 4: Run the CLI and discovery tests**

Run: `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest tests/test_remote_cli.py tests/test_host_discovery.py tests/test_remote_listen.py -q`
Expected: PASS, including the four pre-existing `server.main([...])` tests in `test_host_discovery.py`.

- [ ] **Step 5: Commit**

```bash
git add server/main.py tests/test_remote_cli.py
git commit -m "feat(host): add --remote for the Tailscale loopback listener"
```

---

### Task 4: Full software regression

**Files:**
- No code changes.

- [ ] **Step 1: Run the complete Python suite**

Run: `PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest -q`
Expected: `0 failed`; count ≥ 690 (681 before this plan).

- [ ] **Step 2: Run the frontend suite**

Run: `node --test tests/frontend`
Expected: `fail 0` (57 tests).

- [ ] **Step 3: Check the working tree**

Run: `git status --porcelain`
Expected: empty. If not, stop and inspect before proceeding.

---

### Task 5: Operator runbook

**Files:**
- Create: `docs/R7-REMOTE-ACCESS.md`

- [ ] **Step 1: Write the runbook**

The file must contain these sections with these exact commands and rules:

1. **前提与审批** — Windows Host 和手机各装一次 Tailscale，均需操作者单独同意；不改防火墙、不碰公司 VPN；tailnet 名称、账号、URL 不写入仓库或证据。
2. **安装与开启** — 安装 Tailscale 并登录；管理台开启 MagicDNS 与 HTTPS certificates；用 `tailscale status` 查看本机 `<host>.<tailnet>.ts.net`（只记在本地，不提交）。
3. **启动 Host** — 在项目 worktree 运行：
   ```
   PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" \
   "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" \
   -m server.main --host 10.21.98.75 --port 8000 --remote
   ```
   用 `netstat -ano | findstr :8000` 确认 `10.21.98.75:8000` 与 `127.0.0.1:8000` 同时监听；设备仍 200/304。
4. **开启 Serve** — `tailscale serve --bg --https=443 127.0.0.1:8000`，随后 `tailscale serve status` 必须显示 `https://<host>.<tailnet>.ts.net` → `http://127.0.0.1:8000`；若本机 CLI 只接受另一种参数写法，用 `tailscale serve --help` 校正并把实际命令记入本文件与证据；不得改用 Funnel 或第二个 target。
5. **手机访问** — 手机装 Tailscale 并登录同一 tailnet，关闭 Wi-Fi 只用蜂窝网络，打开 `https://<host>.<tailnet>.ts.net/manage`。
6. **安全边界** — 无应用登录，tailnet 成员即可管理；建议在 Access controls 只放行自己的设备访问该主机 443（语法以管理台为准）；`config/firmware.json` 保持不存在，OTA arm 为 503；丢失设备立即从 tailnet 移除。
7. **失败处理** — 逐条覆盖：Tailscale 停止、HTTPS 未开、LAN IP 变化、端口占用、公司 VPN 冲突；每条给出「停手 / 恢复」动作，与规格 §7 一致。
8. **回滚** — 去掉 `--remote` 重启；`tailscale serve --https=443 off`（以 `--help` 确认）；可选卸载 Tailscale，不影响页面数据与设备。
9. **证据清单** — `netstat.txt`、`serve-status.txt`（tailnet 名打码）、`lan-regression.txt`、`remote-switch.txt`、`ota-503.json`、`remote-manage.png`（地址栏打码）。

- [ ] **Step 2: Check for secrets and placeholders**

Run: `grep -n -i "password\|token\|ts\.net\|TBD\|TODO" docs/R7-REMOTE-ACCESS.md`
Expected: only the documented placeholder `<host>.<tailnet>.ts.net` and the guidance text; no real tailnet name, IP of a public service, password or token.

- [ ] **Step 3: Commit**

```bash
git add docs/R7-REMOTE-ACCESS.md
git commit -m "docs(r7): add the remote access runbook"
```

---

### Task 6: Install and tailnet setup (approval gate)

**Files:** none in the repo.

- [ ] **Step 1: Ask for explicit approval**

Ask the operator, in one message, to approve: (a) installing Tailscale on the Windows Host, (b) installing Tailscale on the phone, (c) enabling MagicDNS and HTTPS certificates in the tailnet.

- [ ] **Step 2: Stop on refusal or policy block**

If any part is refused, blocked by company policy, or the company VPN conflicts: record `R7A SOFTWARE = PASS; DEPLOYMENT = BLOCKED` in `PROJECT_STATE.md` later in Task 8, keep the code and runbook commits, and skip Task 7. Do not edit the VPN, firewall or security software.

- [ ] **Step 3: Install and verify the clients**

Run: `tailscale status`
Expected: logged in, this machine online, one tailnet; note the machine's `*.ts.net` name locally only.

Run: `tailscale ip -4`
Expected: one `100.x.y.z` tailnet address.

- [ ] **Step 4: Enable HTTPS and confirm**

In the admin console enable MagicDNS and HTTPS certificates. Then on the Host:

Run: `tailscale status`
Expected: this machine appears with its `*.ts.net` DNS name (note it locally only; do not commit it). Serve is verified in Task 7 Step 4; no certificate file is requested into the repo.

---

### Task 7: Dual-listen and remote acceptance

**Files:** none in the repo; evidence under `D:/Codex/round2-r7-20261108/acceptance/`.

- [ ] **Step 1: Preflight**

Run: `curl -s http://10.21.98.75:8000/api/pages/status` and `ping -n 2 10.21.98.216`.
Expected: 200 from the Host and the device replies. Record the current `page`, `revision`, `frame_version`, and `device.refresh_count` in `lan-regression.txt`.

- [ ] **Step 2: Restart with `--remote`**

Find and stop the running Host, then start it with the Task 5 command (`--remote`). Confirm the selected page is a file page (weather) so the restart does not lose an in-memory Progress frame.

```bash
netstat -ano | findstr :8000
taskkill //PID <pid-from-the-line> //F
```

Run: `netstat -ano | findstr :8000`
Expected: two listeners on the same port, one `10.21.98.75`, one `127.0.0.1`; save to `netstat.txt`.

- [ ] **Step 3: LAN regression**

Run: `curl -s -D - -o /dev/null http://10.21.98.75:8000/api/panels/progress/frame`
Expected: 200, 15000 bytes, ETag = SHA-256; the next device poll (allow 1–2 minutes for the known AP pause) is 304 and `refresh_count` does not increase. Also confirm `GET /api/pages/status` shows `device.last_seen` advancing after the restart and `frame_version` equal to the served ETag (the device still finds and reaches the LAN endpoint after the dual-listen change). Save headers and status to `lan-regression.txt`.

- [ ] **Step 4: Start Serve**

Run: `tailscale serve --bg --https=443 127.0.0.1:8000`
Run: `tailscale serve status`
Expected: `https://<host>.<tailnet>.ts.net` → `http://127.0.0.1:8000`; save a redacted copy to `serve-status.txt`.

- [ ] **Step 5: Remote page load**

On the phone with Wi-Fi off, open the HTTPS URL. Take a screenshot, redact the address bar and any tailnet name, save as `remote-manage.png`.
Expected: the same `/manage` page with page switcher, weather card and preview controls.

- [ ] **Step 6: Remote page switch and memo save**

Switch to Memo (or another page), then back to Weather. Record the device `refresh_count` before and after; each content change must produce one 200 and the next poll 304.
Save `/api/pages/memo` before/after and the device status to `remote-switch.txt`; restore the memo content afterwards so the device page is unchanged.

- [ ] **Step 7: Remote preview equality**

Generate a weather preview from the remote page. Compare `X-Frame-Version` with the served frame ETag at `http://10.21.98.75:8000/api/panels/progress/frame`.
Expected: identical; append to `remote-switch.txt`.

- [ ] **Step 8: OTA stays closed**

Run: `curl -s http://10.21.98.75:8000/api/device/firmware/status`
Expected: `configured: false`; `POST .../arm` returns 503. Save both to `ota-503.json`. Confirm `config/firmware.json` does not exist (`ls config/firmware.json` fails).

- [ ] **Step 9: Write the evidence summary**

Create `D:/Codex/round2-r7-20261108/acceptance/README.md` with: date, device firmware, Host listen addresses, the redacted serve status, A1–A6 results, and explicit NOT RUN items. No tailnet name, no tokens.

---

### Task 8: Project state, goals and commit

**Files:**
- Modify: `PROJECT_STATE.md` (append an R7A section before “Limits and next stage”, update `NEXT_REQUIRED_STAGE`)
- Modify: `docs/GOALS.md` (§4 row 11 or a new R7 note, and §11 “下一个动作” — keep the wording factual)

- [ ] **Step 1: Record the software result**

Append a section `## Remote access (R7A, 2026-11-08)` stating: `--remote` adds a loopback listener; default startup unchanged; advertisement still the LAN IPv4; tests added; Python/Node counts; commits.

- [ ] **Step 2: Record the deployment result**

- If Task 7 completed: list A1–A6 with evidence file names, the redacted serve status, remote page switch counts, preview equality, OTA 503, and the explicit “no firewall/VPN change” statement.
- If blocked: write `DEPLOYMENT = BLOCKED` with the exact blocker (install refused / policy / VPN conflict) and `REMOTE ACCEPTANCE = NOT RUN`. Never write PASS without the Task 7 evidence.

Update `NEXT_REQUIRED_STAGE` accordingly: on success, “R7A remote access PASS; R8 not authorized”; on block, “R7A software PASS; deployment BLOCKED — needs operator approval for Tailscale”.

- [ ] **Step 3: Update GOALS**

In `docs/GOALS.md`, mark the phone/remote entry with the factual result (remote management over Tailscale; device unchanged) or the BLOCKED state. Do not claim PWA installation unless it was actually installed and verified.

- [ ] **Step 4: Run the full regression one last time**

Run the Task 4 commands; expected `0 failed` and `fail 0`.

- [ ] **Step 5: Commit**

```bash
git add PROJECT_STATE.md docs/GOALS.md
git commit -m "docs(r7): record the remote access result"
git status --porcelain
```

Expected: clean tree. Do not push, tag or open a PR.

---

## Verification Summary

| Claim | Command / evidence |
| --- | --- |
| Address rule is correct | `pytest tests/test_remote_listen.py` |
| Two sockets share one port | `test_bind_listeners_share_one_ephemeral_port` |
| Default startup unchanged | `test_default_startup_still_calls_uvicorn_run` + `tests/test_host_discovery.py` |
| Remote startup runs one server on two sockets | `test_remote_binds_both_addresses_and_runs_one_server` |
| No regression | full pytest + `node --test tests/frontend` |
| Device unaffected | Task 7 Step 3 (200→304, count unchanged) |
| Remote `/manage` works | Task 7 Steps 5–7 (phone cellular, switch, preview) |
| OTA stays closed | Task 7 Step 8 (503, no firmware config) |

## Stop Rules

- Stop before installing Tailscale without explicit approval.
- Stop if Windows asks for a firewall decision; ask the operator instead of allowing silently.
- Stop if the company VPN or endpoint policy blocks Tailscale; do not modify them.
- Stop after software commits if deployment is blocked; record BLOCKED, do not simulate remote access.
- Never write the tailnet name, account, tokens, Wi-Fi credentials or firmware paths into the repo, logs or evidence.
- No push, tag, PR, OTA or firmware change in this plan.
